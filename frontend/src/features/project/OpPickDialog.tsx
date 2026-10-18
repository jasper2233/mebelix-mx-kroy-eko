// Operatsiyalarni katakcha bilan tanlash oynasi (xodimlar o'rgangan «Объединить» oynasidek): sarlavha satrida joriy operatsiya va
// uchta ikonka («Выбрать все», «Снять выделение», «Сортировка»), jadval №/Выб/Тип/Код/Наименование, pastda Ок / Отмена.
// «Объединить» (bir xil turdagi operatsiyalar → joriyga) va «Выбрать элементы для печати» (П-ть belgilari) shu oynani ishlatadi.
import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import type { AgGridReact } from "ag-grid-react";
import { useTranslation } from "react-i18next";
import type { ColDef } from "ag-grid-community";
import { ArrowDownAZ, ListChecks, ListX } from "lucide-react";
import type { OpType, Operation } from "../../api/types";
import { Grid } from "../../shared/grid/Grid";
import { Btn, IconBtn, Modal } from "../../shared/ui";
import { OpBadge } from "./opmeta";

export function OpPickDialog(props: { title: string; head?: ReactNode; ops: Operation[]; initial?: string[]; testid: string;
  empty?: string; onOk: (ids: string[]) => void; onClose: () => void }) {
  const { t } = useTranslation();
  const [sel, setSel] = useState<Set<string>>(() => new Set(props.initial ?? []));
  const [sorted, setSorted] = useState(false);
  const grid = useRef<AgGridReact<Operation>>(null);
  const selRef = useRef(sel);
  selRef.current = sel;
  // katakcha holati jadval qiymatidan (valueGetter) olinadi; tanlov o'zgarsa ustun qayta chiziladi
  useEffect(() => { grid.current?.api?.refreshCells({ columns: ["sel"], force: true }); }, [sel]);
  const rows = useMemo(() => (sorted
    ? [...props.ops].sort((a, b) => `${a.code}\u0000${a.name}`.localeCompare(`${b.code}\u0000${b.name}`, "ru"))
    : props.ops), [props.ops, sorted]);
  // belgi qator bosilganda almashadi (katakcha ham qator ichida — ikki marta almashmasin, u faqat ko'rsatadi)
  // belgi qator bosilganda almashadi (katakcha faqat ko'rsatadi — ikki marta almashmasin)
  const toggle = (id: string) => setSel((s) => { const n = new Set(s); if (n.has(id)) n.delete(id); else n.add(id); return n; });
  const cols = useMemo<ColDef<Operation>[]>(() => [
    { colId: "n", headerName: "№", valueGetter: (p) => (p.node?.rowIndex ?? 0) + 1, width: 44, cellClass: "num rownum" },
    { colId: "sel", headerName: t("ops.col.sel"), width: 52, cellClass: "center",
      valueGetter: (p) => (p.data ? selRef.current.has(p.data.id) : false),
      cellRenderer: (p: { data?: Operation; value: boolean }) => p.data
        ? <input type="checkbox" checked={!!p.value} readOnly tabIndex={-1} style={{ pointerEvents: "none" }}
          data-testid={`${props.testid}-chk-${p.data.id}`} />
        : null },
    { headerName: t("ops.col.type"), field: "type", width: 72, cellRenderer: (p: { value: OpType }) => <OpBadge type={p.value} /> },
    { headerName: t("catalog.code"), field: "code", width: 140 },
    { headerName: t("ops.col.name"), field: "name", flex: 1, minWidth: 160 },
  ], [t]); // eslint-disable-line react-hooks/exhaustive-deps
  return (
    <Modal title={props.title} onClose={props.onClose} width={640} height={360} testid={props.testid}
      footer={<><Btn kind="primary" label={t("app.ok")} testid={`${props.testid}-ok`} onClick={() => props.onOk(rows.filter((o) => sel.has(o.id)).map((o) => o.id))} />
        <Btn label={t("app.cancel")} onClick={props.onClose} /></>}>
      <div className="oppick">
        <div className="oppick-head">
          <span className="oppick-title">{props.head}</span>
          <IconBtn icon={ListChecks} title={t("ops.pick_all")} onClick={() => setSel(new Set(props.ops.map((o) => o.id)))}
            testid={`${props.testid}-all`} />
          <IconBtn icon={ListX} title={t("ops.pick_none")} onClick={() => setSel(new Set())} />
          <IconBtn icon={ArrowDownAZ} title={t("app.sort")} active={sorted} onClick={() => setSorted(!sorted)} />
        </div>
        {props.ops.length === 0 && props.empty ? <p className="muted">{props.empty}</p> : (
          <Grid<Operation> ref={grid} className="grow" rowData={rows} columnDefs={cols} getRowId={(p) => p.data.id} testid={`${props.testid}-grid`}
            onRowClicked={(e) => { if (e.data) toggle(e.data.id); }} />
        )}
      </div>
    </Modal>
  );
}
