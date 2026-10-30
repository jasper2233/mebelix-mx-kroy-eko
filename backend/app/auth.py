"""Autentifikatsiya — MES SSO (JWT) uchun tayyor joy.

Sozlash (muhit o'zgaruvchilari):
  MEBELIX_AUTH_REQUIRED=1          — token majburiy (aks holda tokensiz so'rov «local» foydalanuvchi)
  MEBELIX_JWT_SECRET=...           — HS256 kaliti  (yoki)
  MEBELIX_JWT_PUBLIC_KEY=...       — RS256 ochiq kaliti (PEM)
  MEBELIX_JWT_AUDIENCE=...         — ixtiyoriy «aud» tekshiruvi
  MEBELIX_DEFAULT_USER=admin       — tokensiz rejimdagi foydalanuvchi nomi
  MEBELIX_USERS=login:parol[:rol1|rol2],...  — kirish oynasi (`POST /api/auth/login`) foydalanuvchilari; token
                                     MEBELIX_JWT_SECRET bilan imzolanadi (rol berilmasa — admin)
  MEBELIX_JWT_TTL_HOURS=168        — kirish oynasi bergan token muddati (soat)
  MEBELIX_AUTH_LOCAL=1             — shu kompyuterdan (127.0.0.1, proksi/tunnel sarlavhalarisiz) tokensiz kirish
                                     (MCP, mahalliy brauzer); tunnel orqali kelgan so'rov baribir token talab qiladi
Token: `Authorization: Bearer <jwt>`; foydalanuvchi nomi — `name` / `preferred_username` / `sub`.
Token muddati (`exp`) majburiy — muddatsiz token rad etiladi (401).

Rollar (I_MES_INTEGRATION.md, I4): kroychi (tahrir), texnolog (sozlamalar, postprotsessor), ko'ruvchi (faqat o'qish).
Token da `roles` (ro'yxat yoki matn; Keycloak: `realm_access.roles`) bo'lishi mumkin. `MEBELIX_AUTH_REQUIRED=1` da
faqat «ko'ruvchi» rollari bor (tahrirlovchi roli yo'q) foydalanuvchi o'qiy oladi (GET/HEAD/OPTIONS), yozish
(POST/PUT/PATCH/DELETE) — 403. Rollari yo'q (yoki tanilmagan) token — avvalgidek to'liq huquq.
"""
from __future__ import annotations

import os
import re
from typing import Optional

from fastapi import Header, HTTPException, Request

from .i18n import _

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

# rol nomlari (hujjatdagi: kroychi / texnolog / ko'ruvchi) → ichki nom
_ROLE_ALIASES = {
    "admin": "admin", "administrator": "admin",
    "kroychi": "cutter", "cutter": "cutter", "operator": "cutter", "editor": "cutter", "kroy": "cutter",
    "texnolog": "technologist", "technologist": "technologist", "tech": "technologist",
    "ko'ruvchi": "viewer", "koruvchi": "viewer", "viewer": "viewer", "readonly": "viewer",
    "read-only": "viewer", "reader": "viewer", "view": "viewer",
    "кройщик": "cutter", "технолог": "technologist", "наблюдатель": "viewer", "просмотр": "viewer",
}
_WRITE_ROLES = {"admin", "cutter", "technologist"}

# POST bo'lsa ham hech narsa saqlamaydigan so'rovlar (oldindan ko'rish, qoralama hisoblash) — «ko'ruvchi» ham chaqira oladi
_READONLY_POST = re.compile(
    r"^/api/(projects/[^/]+/(report|labels)"
    r"|projects/[^/]+/operations/[^/]+/(variants|edit)"
    r"|postprocessors/preview|import/preview)/?$")


def _cfg():
    return dict(required=os.getenv("MEBELIX_AUTH_REQUIRED", "0") in ("1", "true", "yes"),
                secret=os.getenv("MEBELIX_JWT_SECRET"), public=os.getenv("MEBELIX_JWT_PUBLIC_KEY"),
                audience=os.getenv("MEBELIX_JWT_AUDIENCE"), default=os.getenv("MEBELIX_DEFAULT_USER", "admin"))


def decode_token(token: str) -> dict:
    import jwt
    c = _cfg()
    key, algs = (c["public"], ["RS256", "ES256"]) if c["public"] else (c["secret"], ["HS256"])
    if not key:
        raise HTTPException(401, _("jwt_no_key"))
    try:
        opts = {"verify_aud": bool(c["audience"]), "require": ["exp"]}
        return jwt.decode(token, key, algorithms=algs, audience=c["audience"] or None, options=opts)
    except jwt.MissingRequiredClaimError as e:
        raise HTTPException(401, _("jwt_no_exp") if e.claim == "exp" else _("jwt_bad", e=e)) from e
    except jwt.PyJWTError as e:
        raise HTTPException(401, _("jwt_bad", e=e)) from e


def claim_roles(claims: dict) -> list[str]:
    """Token dagi rollar ro'yxati (xom nomlar): `roles` / `role` / Keycha `realm_access.roles`."""
    raw: list = []
    for v in (claims.get("roles"), claims.get("role"), (claims.get("realm_access") or {}).get("roles")
              if isinstance(claims.get("realm_access"), dict) else None):
        if isinstance(v, str):
            raw += [x for x in re.split(r"[,\s;]+", v) if x]
        elif isinstance(v, (list, tuple)):
            raw += [str(x) for x in v]
    seen: list[str] = []
    for r in raw:
        if r not in seen:
            seen.append(r)
    return seen


def canonical_roles(roles: list[str]) -> set[str]:
    """Xom rol nomlari → ichki nomlar to'plami (admin / cutter / technologist / viewer); tanilmagan nomlar tushib qoladi."""
    canon = {_ROLE_ALIASES.get(re.sub("[‘’ʻʼ`]", "'", r.strip().lower())) for r in roles}
    canon.discard(None)
    return canon


def is_read_only(roles: list[str]) -> bool:
    """Faqat «ko'ruvchi» rollari bor (tahrirlovchi roli yo'q) bo'lsa — True."""
    canon = canonical_roles(roles)
    return bool(canon) and not (canon & _WRITE_ROLES)


_PROXY_HEADERS = ("cf-connecting-ip", "x-forwarded-for", "x-real-ip", "forwarded")


def _local_ok(request: Request) -> bool:
    """MEBELIX_AUTH_LOCAL=1: shu kompyuterdan to'g'ridan-to'g'ri so'rov (proksi/tunnel sarlavhasi yo'q) — tokensiz."""
    if os.getenv("MEBELIX_AUTH_LOCAL", "0") not in ("1", "true", "yes"):
        return False
    host = request.client.host if request.client else ""
    return host in ("127.0.0.1", "::1", "localhost") and not any(h in request.headers for h in _PROXY_HEADERS)


_PBKDF2_ITER = 260_000


def hash_password(password: str) -> str:
    """PBKDF2-SHA256 (tuzli) — `pbkdf2_sha256$<iter>$<tuz hex>$<xesh hex>`; ochiq parol bazada saqlanmaydi."""
    import hashlib
    import secrets
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _PBKDF2_ITER)
    return f"pbkdf2_sha256${_PBKDF2_ITER}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    import hashlib
    import hmac
    try:
        algo, it, salt, want = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(it))
        return hmac.compare_digest(dk.hex(), want)
    except (ValueError, TypeError):
        return False


def db_user(login: str):
    """Bazadagi foydalanuvchi (login katta-kichik harfga sezgirsiz) yoki None. `users` jadvali RLS siz — faqat kirish uchun."""
    try:
        from .db import SessionLocal, UserRow
        with SessionLocal() as s:
            return s.query(UserRow).filter(UserRow.login == (login or "").strip().lower()).first()
    except Exception:  # noqa: BLE001 — baza tayyor bo'lmasa (eski sxema) muhit foydalanuvchilari ishlayveradi
        return None


def _company_active(cid: int) -> bool:
    try:
        from .db import CompanyRow, SessionLocal
        with SessionLocal() as s:
            c = s.get(CompanyRow, cid)
            return c is None or bool(c.active)
    except Exception:  # noqa: BLE001
        return True


def request_company(request: Request) -> Optional[int]:
    """So'rov qaysi korxonaniki (middleware uchun, xato bermaydi): tokendagi `cid`; token yo'q / yaroqsiz — None
    (u holda standart korxona — tokensiz mahalliy rejim; token majburiy bo'lsa `current_user` 401 qaytaradi)."""
    auth = request.headers.get("authorization") or ""
    if not auth.lower().startswith("bearer "):
        return None
    try:
        claims = decode_token(auth.split(" ", 1)[1].strip())
    except HTTPException:
        return None
    try:
        return int(claims.get("cid") or 0) or None
    except (TypeError, ValueError):
        return None


def request_login(request: Request) -> Optional[str]:
    """So'rov egasining logini (tokendagi `sub`); token yo'q / yaroqsiz — None (xato bermaydi)."""
    auth = request.headers.get("authorization") or ""
    if not auth.lower().startswith("bearer "):
        return None
    try:
        claims = decode_token(auth.split(" ", 1)[1].strip())
    except HTTPException:
        return None
    v = claims.get("sub") or claims.get("name")
    return str(v) if v else None


def password_required() -> bool:
    """Login / parol tizimi yoqilganmi (tokensiz mahalliy rejimda parol so'ralmaydi)."""
    return bool(_cfg()["secret"])


def confirm_password(user: dict, password: Optional[str]) -> None:
    """Muhim sozlamani o'zgartirishdan oldin: shu loginning paroli (stanok standarti va h.k.). Rol — yozuv huquqi."""
    import hmac
    if user.get("read_only") or not (set(canonical_roles(user.get("roles") or [])) & _WRITE_ROLES):
        raise HTTPException(403, _("forbidden_readonly"))
    if not password_required():
        return
    login = str(user.get("sub") or "")
    du = db_user(login)
    if du is not None:
        if du.active and verify_password(password or "", du.password_hash):
            return
    else:
        u = login_users().get(login)
        if u is not None and hmac.compare_digest(u[0].encode(), (password or "").encode()):
            return
    raise HTTPException(403, _("password_wrong"))


def login_users() -> dict[str, tuple[str, list[str]]]:
    """MEBELIX_USERS → {login: (parol, rollar)}."""
    out: dict[str, tuple[str, list[str]]] = {}
    for item in os.getenv("MEBELIX_USERS", "").split(","):
        bits = item.strip().split(":")
        if len(bits) >= 2 and bits[0]:
            roles = [r for r in (bits[2] if len(bits) > 2 else "admin").split("|") if r]
            out[bits[0]] = (bits[1], roles or ["admin"])
    return out


def _db_has_users() -> bool:
    try:
        from .db import SessionLocal, UserRow
        with SessionLocal() as s:
            return s.query(UserRow.id).first() is not None
    except Exception:  # noqa: BLE001
        return False


def login_enabled() -> bool:
    return bool(_cfg()["secret"] and (login_users() or _db_has_users()))


def issue_token(username: str, password: str) -> Optional[dict]:
    """Login/parol to'g'ri bo'lsa — HS256 token (MEBELIX_JWT_SECRET), aks holda None. Avval bazadagi foydalanuvchilar (ko'p
    abonentli rejim: token ichida korxona `cid`), so'ng `MEBELIX_USERS` (standart korxona — bizning ishxona)."""
    import hmac
    import time
    import jwt
    from . import tenant
    c = _cfg()
    if not c["secret"]:
        return None
    du = db_user(username)
    if du is not None:
        if not du.active or not verify_password(password, du.password_hash) or not _company_active(du.company_id):
            return None
        username, roles, cid = du.login, list(du.roles or []) or ["admin"], int(du.company_id)
        _touch_login(du.id)
    else:
        u = login_users().get(username)
        if u is None or not hmac.compare_digest(u[0].encode(), password.encode()):
            return None
        roles, cid = u[1], tenant.DEFAULT_CID
    exp = int(time.time() + float(os.getenv("MEBELIX_JWT_TTL_HOURS", "168")) * 3600)
    claims: dict = {"sub": username, "name": username, "roles": roles, "exp": exp, "cid": cid}
    if c["audience"]:
        claims["aud"] = c["audience"]
    return {"token": jwt.encode(claims, c["secret"], algorithm="HS256"), "exp": exp, "name": username, "roles": roles,
            "cid": cid}


def _touch_login(user_id: int) -> None:
    try:
        from datetime import datetime
        from .db import SessionLocal, UserRow
        with SessionLocal() as s:
            u = s.get(UserRow, user_id)
            if u is not None:
                u.last_login = datetime.utcnow()
                s.commit()
    except Exception:  # noqa: BLE001 — oxirgi kirish vaqti yozilmasa ham kirish ishlayveradi
        pass


def current_user(request: Request, authorization: Optional[str] = Header(None)) -> dict:
    from . import tenant
    c = _cfg()
    if authorization and authorization.lower().startswith("bearer ") and (c["secret"] or c["public"]):
        claims = decode_token(authorization.split(" ", 1)[1].strip())
        name = claims.get("name") or claims.get("preferred_username") or claims.get("sub") or "user"
        roles = claim_roles(claims)
        ro = is_read_only(roles)
        if c["required"] and ro and request.method.upper() not in SAFE_METHODS \
                and not _READONLY_POST.match(request.url.path):
            raise HTTPException(403, _("forbidden_readonly"))
        try:
            cid = int(claims.get("cid") or tenant.DEFAULT_CID)
        except (TypeError, ValueError):
            cid = tenant.DEFAULT_CID
        return {"sub": str(claims.get("sub", name)), "name": str(name), "roles": roles, "read_only": ro,
                "claims": claims, "cid": cid}
    if c["required"] and not _local_ok(request):
        raise HTTPException(401, _("auth_required"))
    return {"sub": "local", "name": c["default"], "roles": ["admin"], "read_only": False, "claims": {}, "cid": tenant.DEFAULT_CID}
