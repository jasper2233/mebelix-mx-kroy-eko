"""Autentifikatsiya — MES SSO (JWT) uchun tayyor joy.

Sozlash (muhit o'zgaruvchilari):
  MEBELIX_AUTH_REQUIRED=1          — token majburiy (aks holda tokensiz so'rov «local» foydalanuvchi)
  MEBELIX_JWT_SECRET=...           — HS256 kaliti  (yoki)
  MEBELIX_JWT_PUBLIC_KEY=...       — RS256 ochiq kaliti (PEM)
  MEBELIX_JWT_AUDIENCE=...         — ixtiyoriy «aud» tekshiruvi
  MEBELIX_DEFAULT_USER=admin       — tokensiz rejimdagi foydalanuvchi nomi
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


def current_user(request: Request, authorization: Optional[str] = Header(None)) -> dict:
    c = _cfg()
    if authorization and authorization.lower().startswith("bearer ") and (c["secret"] or c["public"]):
        claims = decode_token(authorization.split(" ", 1)[1].strip())
        name = claims.get("name") or claims.get("preferred_username") or claims.get("sub") or "user"
        roles = claim_roles(claims)
        ro = is_read_only(roles)
        if c["required"] and ro and request.method.upper() not in SAFE_METHODS \
                and not _READONLY_POST.match(request.url.path):
            raise HTTPException(403, _("forbidden_readonly"))
        return {"sub": str(claims.get("sub", name)), "name": str(name), "roles": roles, "read_only": ro,
                "claims": claims}
    if c["required"]:
        raise HTTPException(401, _("auth_required"))
    return {"sub": "local", "name": c["default"], "roles": ["admin"], "read_only": False, "claims": {}}
