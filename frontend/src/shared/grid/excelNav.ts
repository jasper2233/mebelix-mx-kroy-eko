// Jadvallarda Excel / onlayn yordamdagi navigatsiya (CS «Листы», CL «Полосы», O materiallari):
//   [TAB], [ENTER]                 — o'ngga, qator oxiridan keyingi qatorga (tahrirda qiymat saqlanadi)
//   [SHIFT TAB], [SHIFT ENTER]     — chapga, qator boshidan oldingi qatorga
//   [CTRL TAB], [CTRL ENTER]       — pastga, keyingi qatorning birinchi katagiga; oxirgi qatorda — yangi qator (`append`)
import type { SuppressKeyboardEventParams } from "ag-grid-community";
import { suppressGridKey, swallowTabRepeat } from "../hotkeys";

export function excelNavKey<T>(p: SuppressKeyboardEventParams<T>, append?: () => void): boolean {
  const ev = p.event;
  if (swallowTabRepeat(ev)) return true;
  if (ev.type === "keydown" && (ev.key === "Enter" || ev.key === "Tab") && !ev.altKey) {
    if (ev.ctrlKey || ev.metaKey) {
      p.api.stopEditing();
      const fc = p.api.getFocusedCell();
      const first = p.api.getAllDisplayedColumns().map((c) => c.getColId()).find((id) => id !== "num");
      if (fc && first) {
        if (fc.rowPinned == null && fc.rowIndex + 1 < p.api.getDisplayedRowCount()) {
          p.api.ensureIndexVisible(fc.rowIndex + 1);
          p.api.setFocusedCell(fc.rowIndex + 1, first);
        } else if (append) append();
      }
      ev.preventDefault();
      return true;
    }
    if (p.editing || ev.key === "Enter") {
      p.api.stopEditing();
      if (ev.shiftKey) p.api.tabToPreviousCell();
      else p.api.tabToNextCell();
      ev.preventDefault();
      return true;
    }
  }
  return suppressGridKey(p);
}
