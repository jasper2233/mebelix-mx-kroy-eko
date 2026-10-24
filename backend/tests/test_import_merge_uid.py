"""Import (ochiq loyihaga qo'shish): fayldagi detal ID lari saqlanadi (2026-10-23 — onlayn «5000 kupe»: 18, 2, 3, 4, 6 …);
joriy loyihada band yoki faylda takror bo'lgani — eng kattasidan keyingi raqam."""
from app.models import Operation, OpType, Part, Project
from app.services.project_merge import append_project


def _proj(uids):
    return Project(name="f", operations=[Operation(type=OpType.CS, name="L", parts=[
        Part(uid=u, name=f"d{u}", length=500, width=300) for u in uids])])


def test_uids_kept_when_free():
    cur = Project(name="cur")
    append_project(cur, _proj([18, 2, 3, 4, 6]))
    assert [pt.uid for pt in cur.operations[0].parts] == [18, 2, 3, 4, 6]


def test_uids_renumbered_on_clash_and_dup():
    cur = _proj([1, 2, 3])
    append_project(cur, _proj([3, 7, 7, 9]))
    assert [pt.uid for pt in cur.operations[1].parts] == [10, 7, 11, 9]
