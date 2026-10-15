// Format ikonkalari: server `icon` kaliti → umumiy (lucide) belgi. Dastur logotiplari ishlatilmaydi (CLAUDE.md 4-qoida).
import {
  Box, Boxes, DraftingCompass, Drill, FileCode, Layers, Ruler, TreePine, type LucideIcon,
} from "lucide-react";

export const IMPORT_ICONS: Record<string, LucideIcon> = {
  "file-code": FileCode, box: Box, boxes: Boxes, ruler: Ruler, "drafting-compass": DraftingCompass, "tree-pine": TreePine,
  drill: Drill, layers: Layers,
};
