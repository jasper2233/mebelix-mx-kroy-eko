// Belgilar ranglari: xodimlar o'rgangan tizimdagidek ma'no bo'yicha rangli (foydalanuvchi qarori, 2026-10-21 — belgilar
// o'zimizniki, faqat rang / ma'no uslubi mos): qo'shish va ishga tushirish — yashil, o'chirish — qizil, strelkalar / saqlash /
// bekor qilish — ko'k, asboblar va sozlamalar — jigarrang, papka / ombor — sariq. Yopiq shakllar shu rangning och tusi bilan
// to'ldiriladi. Keyin dizayn qayta chizilganda — faqat shu xarita almashtiriladi.
import type { LucideIcon } from "lucide-react";
import {
  ArrowDown, ArrowDownToLine, ArrowDownUp, ArrowDownWideNarrow, ArrowLeftRight, ArrowLeftToLine, ArrowRightToLine, ArrowUp,
  ArrowUpFromLine, ChevronDown, ChevronFirst, ChevronLast, ChevronLeft, ChevronRight, ChevronUp, CircleQuestionMark, CirclePlay,
  ClipboardPaste, Columns3, Copy, CopyPlus, Cpu, Drill, ExternalLink, Factory, FileDown, FilePlus2, FileText, FileX2,
  TrianglesCenterlineDashedVertical as MirrorHIcon, TrianglesCenterlineDashedHorizontal as MirrorVIcon, FolderOpen, Funnel, Group, Languages, ListChecks, LogOut, Maximize, MessageSquare, MoveDown,
  MoveUp, Pencil, PencilRuler, Play, Plus, PlusSquare, Printer, Redo2, RefreshCw, Replace, RotateCcw, RotateCw, Ruler, Save,
  Settings, Settings2, Square, SquareCheck, SquarePen, SquareX, Tag, Trash, Trash2, Undo2, Wand, Warehouse, Wrench, X,
  LayoutGrid, Layers, SquareStack, Shapes, Library, Merge, Package, Shrink, Scissors, Calculator, Download, Upload,
} from "lucide-react";

export type Tone = { color: string; fill: string };

const T = {
  green: { color: "#1c8f35", fill: "#9be3a9" },
  red: { color: "#d42020", fill: "#f7b0b0" },
  blue: { color: "#1d5bd1", fill: "#a9c6f5" },
  brown: { color: "#a35a00", fill: "#f3cf8f" },
  yellow: { color: "#b98a00", fill: "#ffe17a" },
  slate: { color: "#3f5a7a", fill: "#c9d6e6" },
} satisfies Record<string, Tone>;

const MAP = new Map<LucideIcon, Tone>([
  ...[Plus, PlusSquare, CopyPlus, FilePlus2, Play, CirclePlay, SquareCheck, ListChecks, CircleQuestionMark].map((i) => [i, T.green] as const),
  ...[Trash, Trash2, X, FileX2, SquareX, Square, LogOut].map((i) => [i, T.red] as const),
  ...[ChevronUp, ChevronDown, ChevronLeft, ChevronRight, ChevronFirst, ChevronLast, ArrowUp, ArrowDown, MoveUp, MoveDown,
    ArrowUpFromLine, ArrowDownToLine, ArrowLeftToLine, ArrowRightToLine, ArrowLeftRight, ArrowDownUp, ArrowDownWideNarrow,
    Undo2, Redo2, RotateCcw, RotateCw, RefreshCw, Save, Replace, MirrorHIcon, MirrorVIcon, FileDown, ExternalLink, Copy,
    ClipboardPaste, Maximize, Languages, Merge, Shrink, Download, Upload].map((i) => [i, T.blue] as const),
  ...[Settings, Settings2, Wrench, Wand, Drill, Cpu, PencilRuler, Pencil, SquarePen, Ruler, Tag, Factory, Scissors, Calculator].map((i) => [i, T.brown] as const),
  ...[FolderOpen, Warehouse, Group, Columns3, Funnel, LayoutGrid, Layers, SquareStack, Shapes, Library, Package].map((i) => [i, T.yellow] as const),
  ...[Printer, FileText, MessageSquare].map((i) => [i, T.slate] as const),
]);

/** Belgi rangi (xaritada bo'lmasa — undefined: matn rangi). */
export function toneOf(icon: LucideIcon): Tone | undefined {
  return MAP.get(icon);
}

/** lucide belgisiga beriladigan rang xususiyatlari; `disabled` — rangsiz (kulrang). */
export function toneProps(icon: LucideIcon, disabled?: boolean, color?: string) {
  if (disabled) return {};
  if (color) return { color };
  const t = toneOf(icon);
  return t ? { color: t.color, fill: t.fill, fillOpacity: 0.55 } : {};
}
