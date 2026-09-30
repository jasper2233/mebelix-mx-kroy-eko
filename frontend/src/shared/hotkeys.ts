// Klaviatura yorliqlari (UI_SPEC §10) — maydon (scope) bo'yicha: faol panel yorliqlari birinchi, keyin umumiy.
import { useEffect, useRef } from "react";

export type Handler = (e: KeyboardEvent) => void;
type Scope = string;

const registry = new Map<Scope, Map<string, Handler>>();
let active: Scope = "global";
const stack: Scope[] = [];          // modal oynalar: yuqoridagisi faol

export const HOTKEYS: { keys: string; action: string }[] = [
  { keys: "Ctrl+Z / Ctrl+Y", action: "undo_redo" },
  { keys: "Ctrl+K", action: "clone" },
  { keys: "Del", action: "delete" },
  { keys: "Ctrl+↑ / Ctrl+↓", action: "move_updown" },
  { keys: "Ctrl+Space", action: "properties" },
  { keys: "Ctrl+PgUp (Alt+PgUp, Insert)", action: "insert_row" },
  { keys: "Ctrl+V", action: "paste" },
  { keys: "Ctrl+B", action: "group" },
  { keys: "Ctrl+D / Ctrl+E", action: "grain_off_on" },
  { keys: "Ctrl+W (Alt+W)", action: "swap" },
  { keys: "Ctrl+M", action: "move_to_op" },
  { keys: "Ctrl+P", action: "columns" },
  { keys: "Ctrl+F", action: "filter" },
  { keys: "F1", action: "help" },
  { keys: "Home / ↑ / ↓ / End", action: "maps_nav" },
  { keys: "Ctrl+R / Ctrl+Q / Ctrl+C / Ctrl+← →", action: "editor_keys" },
];

export function comboOf(e: KeyboardEvent): string {
  const parts: string[] = [];
  if (e.ctrlKey || e.metaKey) parts.push("ctrl");
  if (e.altKey) parts.push("alt");
  if (e.shiftKey) parts.push("shift");
  let k = e.key.toLowerCase();
  if (k === " " || e.code === "Space") k = "space";
  else if (k === "del") k = "delete";
  else if (k.length === 1 && e.code.startsWith("Key")) k = e.code.slice(3).toLowerCase();   // kirill tartibida ham
  else if (k.length === 1 && e.code.startsWith("Digit")) k = e.code.slice(5);
  parts.push(k);
  return parts.join("+");
}

function editable(t: EventTarget | null): boolean {
  const el = t as HTMLElement | null;
  if (!el || !el.tagName) return false;
  const tag = el.tagName;
  if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || el.isContentEditable) return true;
  // jadval katagi muharrirlari (ro'yxat popup va h.k.) — Del/Enter/harflar muharrirga tegishli
  return Boolean(el.closest?.("[data-hotkeys-off], .ag-popup-editor, .ag-cell-inline-editing"));
}

// Matn maydonida ham ishlaydigan yorliqlar
const ALWAYS = new Set(["f1"]);

function onKey(e: KeyboardEvent) {
  const combo = comboOf(e);
  if (editable(e.target) && !ALWAYS.has(combo)) return;
  const scope = stack.length ? stack[stack.length - 1] : active;
  const h = registry.get(scope)?.get(combo) ?? (stack.length ? undefined : registry.get("global")?.get(combo));
  if (h) {
    e.preventDefault();
    e.stopPropagation();
    h(e);
  }
}

if (typeof window !== "undefined") window.addEventListener("keydown", onKey, true);

export function setScope(s: Scope) { active = s; }
export function getScope(): Scope { return stack.length ? stack[stack.length - 1] : active; }

/** Panel konteyneriga: sichqoncha/fokus shu panelga tushsa — uning yorliqlari faol. */
export function scopeProps(scope: Scope) {
  return {
    onMouseDownCapture: () => setScope(scope),
    onFocusCapture: () => setScope(scope),
    "data-scope": scope,
  };
}

/** Modal oyna ochiq paytda faqat uning yorliqlari ishlaydi. */
export function useModalScope(scope: Scope, open = true) {
  useEffect(() => {
    if (!open) return;
    stack.push(scope);
    return () => {
      const i = stack.lastIndexOf(scope);
      if (i >= 0) stack.splice(i, 1);
    };
  }, [scope, open]);
}

export function useHotkeys(scope: Scope, map: Record<string, Handler>, enabled = true) {
  const ref = useRef(map);
  ref.current = map;
  useEffect(() => {
    if (!enabled) return;
    const m = registry.get(scope) ?? new Map<string, Handler>();
    registry.set(scope, m);
    const keys = Object.keys(ref.current);
    const own: Record<string, Handler> = {};
    for (const k of keys) {
      for (const alias of k.split(",")) {
        const key = alias.trim();
        const fn: Handler = (e) => ref.current[k]?.(e);
        own[key] = fn;
        m.set(key, fn);
      }
    }
    return () => {
      for (const [key, fn] of Object.entries(own)) if (m.get(key) === fn) m.delete(key);
    };
  }, [scope, enabled, Object.keys(map).join("|")]);
}

/** Brauzer band qiladigan yorliqlar (Ctrl+W, Ctrl+PgUp) — to'liq ekran rejimida Keyboard Lock API bilan ishlaydi. */
export async function enterFullscreenWithKeys() {
  try {
    await document.documentElement.requestFullscreen();
    const kb = (navigator as unknown as { keyboard?: { lock?: (k?: string[]) => Promise<void> } }).keyboard;
    await kb?.lock?.(["KeyW", "PageUp", "PageDown", "KeyN", "KeyT", "KeyP", "KeyF", "KeyD", "KeyE"]);
  } catch { /* qo'llab-quvvatlanmaydi */ }
}

export function exitFullscreen() {
  try {
    const kb = (navigator as unknown as { keyboard?: { unlock?: () => void } }).keyboard;
    kb?.unlock?.();
    if (document.fullscreenElement) void document.exitFullscreen();
  } catch { /* yo'q */ }
}

/** AG Grid: bizning yorliqlarimizni grid o'zi qayta ishlamasin (Del, Ctrl+↑↓ va h.k.). */
const GRID_OWN = new Set(["delete", "ctrl+arrowup", "ctrl+arrowdown", "ctrl+space", "ctrl+k", "ctrl+d", "ctrl+e",
  "ctrl+w", "alt+w", "ctrl+b", "ctrl+m", "ctrl+p", "ctrl+f", "ctrl+z", "ctrl+y", "ctrl+pageup", "alt+pageup",
  "insert", "f1", "ctrl+c", "ctrl+v"]);

export function suppressGridKey(params: { editing: boolean; event: KeyboardEvent }): boolean {
  if (params.editing) return false;
  return GRID_OWN.has(comboOf(params.event));
}
