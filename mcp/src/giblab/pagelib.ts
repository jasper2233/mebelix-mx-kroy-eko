/**
 * Onlayn tizim sahifasiga kiritiladigan (page-side) yordamchi kutubxona — `window.__gl`.
 * Faqat DOM ni o'qiydi va matn bo'yicha elementlarni topadi; tizimning o'z kodi / resurslari ishlatilmaydi.
 * Shu matnni Claude in Chrome `javascript_tool` ga ham to'g'ridan-to'g'ri yuborish mumkin.
 */
export const PAGELIB = String.raw`
(function () {
  if (window.__gl && window.__gl.v === 5) return "ok";
  const norm = (s) => (s || "").replace(/\s+/g, " ").trim();
  const vis = (e) => { if (!e || !e.getBoundingClientRect) return false; const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== "hidden"; };
  const rect = (e) => { const r = e.getBoundingClientRect(); return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height), cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; };
  const cellText = (c) => norm(c.innerText);
  const tables = () => [...document.querySelectorAll("table")].filter((t) => vis(t) && t.rows.length > 0);
  const headerOf = (t) => [...(t.rows[0] ? t.rows[0].cells : [])].map(cellText);
  // sarlavha va qatorlar ko'pincha ALOHIDA jadvallarda (GWT DataGrid): sarlavha jadvalidan keyingi, ustunlar soni bir xil jadval
  // qatorlari qo'shib beriladi (natija — rows maydonli oddiy obyekt; qolgan kod t.rows dan boshqasini ishlatmaydi)
  const findTable = (needles) => {
    const all = tables();
    const i = all.findIndex((t) => { const h = headerOf(t).join(" | "); return needles.every((n) => h.includes(n)); });
    if (i < 0) return null;
    const t = all[i];
    if (t.rows.length > 1) return t;
    const n = t.rows[0].cells.length;
    const body = all.slice(i + 1).find((b) => b.rows.length && b.rows[0].cells.length === n && !needles.every((x) => headerOf(b).join(" | ").includes(x)));
    return body ? { rows: [...t.rows, ...body.rows] } : t;
  };
  const rowsOf = (t, skipHeader) => { if (!t) return []; const rs = [...t.rows]; return (skipHeader ? rs.slice(1) : rs).filter(vis).map((r, i) => ({ i, cells: [...r.cells].map(cellText), r: rect(r) })); };
  const byText = (text, opts) => {
    opts = opts || {};
    const want = norm(text);
    const all = [...document.querySelectorAll(opts.selector || "a, button, td, div, span, label, .gwt-Label, .gwt-Anchor, .gwt-TabLayoutPanelTab, .gwt-Button")].filter(vis);
    let hits = all.filter((e) => norm(e.innerText) === want && (!opts.within || opts.within.contains(e)));
    if (!hits.length && opts.partial) hits = all.filter((e) => norm(e.innerText).includes(want));
    hits.sort((a, b) => a.innerText.length - b.innerText.length);              // eng kichik (aniq) element
    return hits;
  };
  const fire = (e, types, extra) => { for (const t of types) { const ev = new MouseEvent(t, Object.assign({ bubbles: true, cancelable: true, view: window, button: 0 }, extra || {})); e.dispatchEvent(ev); } };
  const clickEl = (e) => { if (!e) return false; e.scrollIntoView({ block: "nearest" }); const r = rect(e); fire(e, ["mouseover", "mousedown", "mouseup", "click"], { clientX: r.cx, clientY: r.cy }); return true; };
  const dblclickEl = (e) => { if (!e) return false; const r = rect(e); fire(e, ["mousedown", "mouseup", "click", "mousedown", "mouseup", "click", "dblclick"], { clientX: r.cx, clientY: r.cy, detail: 2 }); return true; };
  const dialogs = () => [...document.querySelectorAll(".gwt-DialogBox, .gwt-PopupPanel, .popupContent")].filter(vis).map((d) => ({
    title: norm((d.querySelector(".Caption, .gwt-DialogBox .Caption, .dialogTop") || {}).innerText || ""),
    text: norm(d.innerText).slice(0, 2000),
    buttons: [...d.querySelectorAll("button, .gwt-Button, input[type=button]")].filter(vis).map((b) => norm(b.innerText || b.value)),
    r: rect(d),
  }));
  const topDialog = () => { const ds = [...document.querySelectorAll(".gwt-DialogBox")].filter(vis); return ds.length ? ds[ds.length - 1] : null; };
  const api = {
    v: 5,
    url: () => location.href,
    tables: () => tables().map((t, i) => ({ i, header: headerOf(t), rows: t.rows.length, r: rect(t) })),
    table: (needles, limit) => { const t = findTable(needles); return t ? { header: headerOf(t), rows: rowsOf(t, true).slice(0, limit || 5000) } : null; },
    /** Loyihalar ro'yxati: papkalar va loyihalar. */
    projects: () => {
      const t = findTable(["Владелец", "Состояние", "Наименование"]);
      if (!t) return null;
      // papka yo'li: eski ko'rinishda .path yorlig'i, yangisida ro'yxat ustidagi havolalar («test uchun /» — gwt-Anchor)
      const lbl = document.querySelector(".gwt-Label.path, .projects-path");
      const crumb = norm(lbl ? lbl.innerText || "" : [...document.querySelectorAll("a.gwt-Anchor")].filter((e) => {
        const r = e.getBoundingClientRect(); return r.height > 0 && r.y >= 0 && r.y < 45 && r.x > 215; }).map((e) => (e.innerText || "").trim()).join(" "));
      const rows = rowsOf(t, true).map((x) => ({ i: x.i, n: x.cells[0], id: x.cells[2], owner: x.cells[3], status: x.cells[4], date: x.cells[5], cost: x.cells[6], name: x.cells[7], kind: x.cells[2] ? "project" : "folder", r: x.r }));
      return { path: crumb, rows };
    },
    /** Loyiha sahifasi: operatsiyalar jadvali. */
    operations: () => {
      const t = findTable(["Тип", "Наименование", "Ст-ть"]);
      if (!t) return null;
      return rowsOf(t, true).map((x) => ({ i: x.i, n: x.cells[0], type: x.cells[1], code: x.cells[2], name: x.cells[3], costMat: x.cells[4], costOp: x.cells[5], cost: x.cells[6], r: x.r, selected: /selected|rowSelected/i.test(t.rows[x.i + 1].className) }));
    },
    header: () => {
      const inp = [...document.querySelectorAll("input")].filter(vis);
      const name = (inp.find((i) => i.value && !/\d{2}\.\d{2}\.\d{4}/.test(i.value)) || {}).value || "";
      const crumb = [...document.querySelectorAll("div, span, td")].filter(vis).map((e) => norm(e.innerText)).find((s) => /^\((CS|CL|CN|EL|GR|XNC|SP|O|LB)\)\s/.test(s)) || "";
      return { name, selectedOp: crumb, dates: inp.map((i) => i.value).filter((v) => /\d{2}\.\d{2}\.\d{4}/.test(v)), url: location.href };
    },
    tabs: () => [...document.querySelectorAll(".gwt-TabLayoutPanelTab, .gwt-TabBarItem, .gwt-TabLayoutPanelTab-selected")].filter(vis).map((e) => ({ text: norm(e.innerText), selected: /selected/i.test(e.className), r: rect(e) })),
    menu: () => [...document.querySelectorAll("a, .gwt-Anchor, .gwt-Label")].filter(vis).filter((e) => e.getBoundingClientRect().x < 220).map((e) => ({ text: norm(e.innerText), r: rect(e), disabled: /disabled|inactive/i.test(e.className) || getComputedStyle(e).color === "rgb(128, 128, 128)" })).filter((m) => m.text),
    find: (text, partial) => byText(text, { partial }).map((e) => ({ text: norm(e.innerText), tag: e.tagName, cls: e.className, r: rect(e) })),
    click: (text, partial) => clickEl(byText(text, { partial })[0]),
    clickAt: (x, y) => { const e = document.elementFromPoint(x, y); return clickEl(e); },
    dblclickRow: (needles, rowIndex) => { const t = findTable(needles); if (!t) return false; const r = rowsOf(t, true)[rowIndex]; if (!r) return false; return dblclickEl(t.rows[r.i + 1].cells[Math.min(3, t.rows[r.i + 1].cells.length - 1)]); },
    clickRow: (needles, rowIndex) => { const t = findTable(needles); if (!t) return false; const r = rowsOf(t, true)[rowIndex]; if (!r) return false; return clickEl(t.rows[r.i + 1].cells[Math.min(3, t.rows[r.i + 1].cells.length - 1)]); },
    rowRect: (needles, rowIndex) => { const t = findTable(needles); if (!t) return null; const r = rowsOf(t, true)[rowIndex]; return r ? r.r : null; },
    dialogs,
    dialogButton: (label) => { const d = topDialog(); if (!d) return false; const b = [...d.querySelectorAll("button, .gwt-Button, input[type=button]")].filter(vis).find((x) => norm(x.innerText || x.value) === norm(label)); if (!b) return false; b.focus(); return clickEl(b); },
    dialogButtonRect: (label) => { const d = topDialog(); if (!d) return null; const b = [...d.querySelectorAll("button, .gwt-Button, input[type=button]")].filter(vis).find((x) => norm(x.innerText || x.value) === norm(label)); return b ? rect(b) : null; },
    /** «Раскрой» holat qatori va kartalar: raqamli ko'rsatkichlar (№/S/C/Ср/LT/F va h.k.) matn bo'yicha. */
    cutPanel: () => {
      const texts = [...document.querySelectorAll("body *")].filter((e) => vis(e) && e.childElementCount === 0 && e.getBoundingClientRect().y > 300).map((e) => norm(e.innerText)).filter(Boolean);
      return texts.slice(0, 400);
    },
    /** Ekran inventari: ko'rinadigan yozuvlar, maslahatlar (title), ro'yxat variantlari — o'xshashlik o'lchovi uchun. */
    inventory: () => {
      const out = [], seen = new Set();
      const add = (k, t) => { t = norm(t); if (!t || t.length > 120) return; const key = k + "|" + t; if (seen.has(key)) return; seen.add(key); out.push([k, t]); };
      for (const e of document.querySelectorAll("body *")) {
        if (!vis(e)) continue;
        if (e.title) add("title", e.title);
        if (e.tagName === "SELECT") { for (const o of e.options) add("option", o.text); continue; }
        if (e.tagName === "INPUT") { if (e.placeholder) add("ph", e.placeholder); add("input", e.type); continue; }
        if (e.childElementCount === 0 && !["OPTION", "SCRIPT", "STYLE"].includes(e.tagName)) add("text", e.textContent);
        else if (!["OPTION", "SCRIPT", "STYLE", "SELECT"].includes(e.tagName)) for (const n of e.childNodes) if (n.nodeType === 3) add("text", n.textContent);
      }
      return out;
    },
    text: () => norm(document.body.innerText).slice(0, 20000),
  };
  window.__gl = api;
  return "ok";
})()
`;
