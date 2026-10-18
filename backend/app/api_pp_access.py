"""Postprotsessorlarga kirish huquqi API si (model — `services/pp_access.py` izohida).

  GET /api/postprocessors/access   — hamma o'qiydi: {explicit, open, machines: [{key, name, group, label, open, native}],
                                     can_edit (joriy foydalanuvchi admin), updated_by, updated_at}
  PUT /api/postprocessors/access   — faqat administrator: {open: [stanok kaliti] | null}; null — standartga qaytarish
                                     (bugun ishlayotgan hamma stanoklar ochiq). Noma'lum kalit — 400, admin emas — 403.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from .auth import current_user
from .services import pp_access

router = APIRouter(prefix="/postprocessors/access", tags=["postprotsessor"])


def _can_edit(user: dict) -> bool:
    try:
        pp_access.require_admin(user)
        return True
    except HTTPException:
        return False


@router.get("")
def access_get(user: dict = Depends(current_user)):
    return dict(pp_access.state(), can_edit=_can_edit(user))


class AccessIn(BaseModel):
    open: Optional[list[str]] = Field(None, max_length=500)


@router.put("")
def access_put(inp: AccessIn, user: dict = Depends(current_user)):
    pp_access.require_admin(user)
    return dict(pp_access.set_open(inp.open, user.get("name", "")), can_edit=True)
