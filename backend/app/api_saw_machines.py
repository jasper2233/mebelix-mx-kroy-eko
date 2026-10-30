"""«Раскроечные станки» API (model va qoidalar — `services/saw_machines.py`).

  GET  /api/saw-machines                 — {machines, default_id, my_machine_id, login, password_required, fields}
  PUT  /api/saw-machines/me              — {machine_id}: joriy login o'z stanogini tanlaydi (yangi loyihalar shu stanokdan;
                                           null — korxonaning asosiy stanogi)
  POST /api/saw-machines/save            — standartni o'zgartirish (login paroli bilan): {password, machine: {id?, name, cut},
                                           make_default?}; id yo'q — yangi stanok
  POST /api/saw-machines/{id}/delete     — {password}
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from .auth import confirm_password, current_user, password_required
from .i18n import _
from .services import saw_machines as SM

router = APIRouter(prefix="/saw-machines", tags=["sozlamalar"])


def _out(sm: SM.SawMachines, user: dict) -> dict:
    login = SM.norm_login(user.get("sub"))
    return dict(machines=[m.model_dump() for m in sm.machines], default_id=sm.default_id,
                my_machine_id=SM.machine_for(login, sm).id, my_choice=sm.user_machine.get(login),
                login=login, password_required=password_required(), fields=list(SM.MACHINE_FIELDS))


@router.get("")
def list_machines(user: dict = Depends(current_user)):
    return _out(SM.load(), user)


class MeIn(BaseModel):
    machine_id: Optional[str] = None


@router.put("/me")
def choose_machine(inp: MeIn, user: dict = Depends(current_user)):
    sm = SM.load()
    login = SM.norm_login(user.get("sub"))
    if inp.machine_id and inp.machine_id not in {m.id for m in sm.machines}:
        raise HTTPException(404, _("saw_machine_not_found"))
    if inp.machine_id:
        sm.user_machine[login] = inp.machine_id
    else:
        sm.user_machine.pop(login, None)
    return _out(SM.save(sm), user)


class MachineIn(BaseModel):
    id: Optional[str] = None
    name: str = Field("", max_length=100)
    cut: dict = Field(default_factory=dict)


class SaveIn(BaseModel):
    password: Optional[str] = None
    machine: MachineIn
    make_default: bool = False


@router.post("/save")
def save_machine(inp: SaveIn, user: dict = Depends(current_user)):
    confirm_password(user, inp.password)
    sm = SM.load()
    login = SM.norm_login(user.get("sub"))
    try:
        cut = SM.clean_cut(inp.machine.cut)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    by = {m.id: m for m in sm.machines}
    if inp.machine.id:
        m = by.get(inp.machine.id)
        if m is None:
            raise HTTPException(404, _("saw_machine_not_found"))
        m.name = inp.machine.name.strip() or m.name
        m.cut = {**m.cut, **cut}
    else:
        if not inp.machine.name.strip():
            raise HTTPException(400, _("saw_machine_name"))
        m = SM.SawMachine(name=inp.machine.name.strip(), cut=cut)
        sm.machines.append(m)
    SM.stamp(m, login)
    if inp.make_default or not sm.default_id:
        sm.default_id = m.id
    return _out(SM.save(sm), user)


class PwIn(BaseModel):
    password: Optional[str] = None


@router.post("/{mid}/delete")
def delete_machine(mid: str, inp: PwIn, user: dict = Depends(current_user)):
    confirm_password(user, inp.password)
    sm = SM.load()
    if mid not in {m.id for m in sm.machines}:
        raise HTTPException(404, _("saw_machine_not_found"))
    if len(sm.machines) <= 1:
        raise HTTPException(400, _("saw_machine_last"))
    sm.machines = [m for m in sm.machines if m.id != mid]
    sm.user_machine = {k: v for k, v in sm.user_machine.items() if v != mid}
    if sm.default_id == mid:
        sm.default_id = sm.machines[0].id
    return _out(SM.save(sm), user)
