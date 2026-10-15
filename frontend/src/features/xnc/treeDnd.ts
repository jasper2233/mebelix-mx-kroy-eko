// Daraxt qatorlarini sichqoncha bilan sudrab ko'chirish (W18): XNC «Шаблон» yorlig'i va mahsulot «Программа» si uchun umumiy.
// HTML5 drag-and-drop; mantiq — treeOps.ts::moveTo (toza). Klaviatura (Ctrl+←/→/↑/↓) o'zgarmaydi.
// Tashlash joyi qatorning balandligi bo'yicha: blok qatorida yuqori chorak — «oldin», o'rta — «ichiga», pastki chorak — «keyin»;
// oddiy qatorda yuqori yarmi — «oldin», pastki yarmi — «keyin». Qatorda `data-drop` (before | after | inside) va `data-dragging`.
import { useRef, useState, type DragEvent } from "react";
import type { XncCommand } from "../../api/types";
import { isContainer, moveTo, pathKey, samePath, type DropPos, type Edit, type Path } from "./treeOps";

export const DND_MIME = "text/plain";

/** Qator ichidagi tik o'rin → tashlash joyi. `y` — 0 (tepa) … 1 (past). */
export function dropPosition(y: number, container: boolean): DropPos {
  if (container) return y < 0.25 ? "before" : y > 0.75 ? "after" : "inside";
  return y < 0.5 ? "before" : "after";
}

export interface DndRowProps {
  draggable: true;
  "data-dragging"?: "1";
  "data-drop"?: DropPos;
  onDragStart: (e: DragEvent<HTMLDivElement>) => void;
  onDragOver: (e: DragEvent<HTMLDivElement>) => void;
  onDragLeave: (e: DragEvent<HTMLDivElement>) => void;
  onDrop: (e: DragEvent<HTMLDivElement>) => void;
  onDragEnd: () => void;
}

/**
 * `getProg` — joriy (optimistik) dastur; `onMove(edit)` — ko'chirish natijasi (chaqiruvchi saqlaydi va tanlovni qo'yadi);
 * `onStart(path)` — sudrash boshlanganda (masalan, qatorni tanlash).
 */
export function useTreeDnd(getProg: () => XncCommand[], onMove: (e: Edit) => void, onStart?: (p: Path) => void) {
  const [drag, setDrag] = useState<Path | null>(null);
  const [over, setOver] = useState<{ key: string; pos: DropPos } | null>(null);
  const dragRef = useRef<Path | null>(null);

  const clear = () => { dragRef.current = null; setDrag(null); setOver(null); };

  const rowProps = (path: Path, cmd: XncCommand): DndRowProps => {
    const key = pathKey(path);
    const where = (e: DragEvent<HTMLDivElement>): DropPos => {
      const r = e.currentTarget.getBoundingClientRect();
      return dropPosition(r.height > 0 ? (e.clientY - r.top) / r.height : 0.5, isContainer(cmd));
    };
    return {
      draggable: true,
      "data-dragging": drag && samePath(drag, path) ? "1" : undefined,
      "data-drop": over && over.key === key ? over.pos : undefined,
      onDragStart: (e) => {
        dragRef.current = path;
        setDrag(path);
        e.dataTransfer.effectAllowed = "move";
        e.dataTransfer.setData(DND_MIME, key);                    // Firefox: setData bo'lmasa sudrash boshlanmaydi
        onStart?.(path);
      },
      onDragOver: (e) => {
        const from = dragRef.current;
        if (!from) return;
        const pos = where(e);
        if (moveTo(getProg(), from, path, pos) === null) {         // bu joyga tashlab bo'lmaydi: ko'rsatkich yo'q, kursor «taqiq»
          if (over) setOver(null);
          return;
        }
        e.preventDefault();
        e.dataTransfer.dropEffect = "move";
        if (!over || over.key !== key || over.pos !== pos) setOver({ key, pos });
      },
      onDragLeave: (e) => {
        if (!e.currentTarget.contains(e.relatedTarget as Node | null) && over?.key === key) setOver(null);
      },
      onDrop: (e) => {
        const from = dragRef.current;
        if (!from) return;
        e.preventDefault();
        const edit = moveTo(getProg(), from, path, where(e));
        clear();
        if (edit) onMove(edit);
      },
      onDragEnd: clear,
    };
  };
  return { rowProps, dragging: drag };
}
