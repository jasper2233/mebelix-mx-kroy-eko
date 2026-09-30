"""Autentifikatsiya — MES SSO (JWT) uchun tayyor joy (hozircha stub).

Sozlash (muhit o'zgaruvchilari):
  MEBELIX_AUTH_REQUIRED=1          — token majburiy (aks holda tokensiz so'rov «local» foydalanuvchi)
  MEBELIX_JWT_SECRET=...           — HS256 kaliti  (yoki)
  MEBELIX_JWT_PUBLIC_KEY=...       — RS256 ochiq kaliti (PEM)
  MEBELIX_JWT_AUDIENCE=...         — ixtiyoriy «aud» tekshiruvi
  MEBELIX_DEFAULT_USER=admin       — tokensiz rejimdagi foydalanuvchi nomi
Token: `Authorization: Bearer <jwt>`; foydalanuvchi nomi — `name` / `preferred_username` / `sub`.
"""
from __future__ import annotations

import os
from typing import Optional

from fastapi import Header, HTTPException

from .i18n import _


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
        opts = {"verify_aud": bool(c["audience"])}
        return jwt.decode(token, key, algorithms=algs, audience=c["audience"] or None, options=opts)
    except jwt.PyJWTError as e:
        raise HTTPException(401, _("jwt_bad", e=e)) from e


def current_user(authorization: Optional[str] = Header(None)) -> dict:
    c = _cfg()
    if authorization and authorization.lower().startswith("bearer ") and (c["secret"] or c["public"]):
        claims = decode_token(authorization.split(" ", 1)[1].strip())
        name = claims.get("name") or claims.get("preferred_username") or claims.get("sub") or "user"
        return {"sub": str(claims.get("sub", name)), "name": str(name), "roles": claims.get("roles", []),
                "claims": claims}
    if c["required"]:
        raise HTTPException(401, _("auth_required"))
    return {"sub": "local", "name": c["default"], "roles": ["admin"], "claims": {}}
