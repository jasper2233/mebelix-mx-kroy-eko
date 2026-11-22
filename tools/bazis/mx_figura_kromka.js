// MebeliX Kroy — figurali detallar kromkasini .project fayliga qo'shish (Bazis-Mebelshchik skripti)
// (2026-11-22) ASOSIY YO'L — korxonaning Bazis eksport skripti 2.00 MX: u mxFigure (v2, XNC koordinatalarida, EL havolasi
// bilan) ni eksportning o'zida yozadi. Bu skript — zaxira: eski eksport bilan olingan .project ga keyin qo'shish uchun (v1).
// ---------------------------------------------------------------------------------------------------
// Nima uchun: Bazis .project eksportida kromka faqat 4 tomonga yoziladi (elt/elb/ell/elr). Egri yoki kesilgan
// (figurali) qirra kromkasi yo'qoladi. Bu skript ochiq Bazis modelidagi har panelning konturini va har kontur
// elementidagi kromkani (Butt.ElemIndex) o'qib, eksport qilingan .project ichidagi mos <part> ga `mxFigure`
// atributi sifatida yozadi. MebeliX Kroy importi shu atributni o'qiydi (backend/app/services/figure.py: bazis_edges).
//
// Ishlatish:
//   1. Bazis'da mahsulot modelini oching va odatdagidek .project eksport qiling.
//   2. Shu skriptni ishga tushiring, so'ralganda o'sha .project faylini tanlang.
//   3. Skript YANGI fayl yozadi: «<nom>_mx.project» (asl fayl o'zgarmaydi). MX ga shu yangi faylni yuklang.
//
// Moslash: <part code="..."> = panel «Артикул» (ArtPos); topilmasa — nom + o'lcham bo'yicha.
// Faqat to'g'ri to'rtburchak bo'lmagan yoki kontur elementlari 4 tadan ko'p panellar yoziladi.
// Atribut formati (JSON, XML uchun ekranlangan): {"v":1,"segs":[{"x1","y1","x2","y2",["cx","cy","ccw"],"mat","sign"}]}

function esc(s) {
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function r2(v) {
  return Math.round(v * 100) / 100;
}

function attr(tag, name) {
  var m = new RegExp("\\s" + name.replace(/\./g, "\\.") + "=\"([^\"]*)\"").exec(tag);
  return m ? m[1] : "";
}

function panelSegs(panel) {
  var butts = {};
  var bl = panel.Butts;
  if (bl) {
    for (var b = 0; b < bl.Count; b++) {
      var bt = bl.Butts ? bl.Butts[b] : bl[b];
      if (bt) butts[bt.ElemIndex] = { mat: bt.Material || "", sign: bt.Sign || "" };
    }
  }
  var segs = [];
  var c = panel.Contour;
  for (var i = 0; i < c.Count; i++) {
    var e = c.Objects ? c.Objects[i] : c[i];
    var k = butts[i] || { mat: "", sign: "" };
    if (e.IsLine && e.IsLine()) {
      var l = e.AsLine();
      segs.push({ x1: r2(l.Pos1.x), y1: r2(l.Pos1.y), x2: r2(l.Pos2.x), y2: r2(l.Pos2.y), mat: k.mat, sign: k.sign });
    } else if (e.IsArc && e.IsArc()) {
      var a = e.AsArc();
      segs.push({ x1: r2(a.Pos1.x), y1: r2(a.Pos1.y), x2: r2(a.Pos2.x), y2: r2(a.Pos2.y),
                  cx: r2(a.Center.x), cy: r2(a.Center.y), ccw: !!a.ArcDir, mat: k.mat, sign: k.sign });
    }
    // aylana / ellips konturli panel — yozilmaydi (MX avtomatik qoidani ishlatadi)
  }
  return segs;
}

function collectPanels() {
  var out = [];
  function walk(list) {
    for (var i = 0; i < list.Count; i++) {
      var o = list.Objects ? list.Objects[i] : list[i];
      if (!o) continue;
      if (o.List) { walk(o.AsList()); continue; }
      var p = o.AsPanel;
      if (p && p.Contour) out.push(p);
    }
  }
  walk(Model);
  return out;
}

function main() {
  var fn = system.askFileName("project");
  if (!fn) return;
  var xml = system.readTextFile(fn);
  if (!xml || xml.indexOf("<project") < 0) { alert("Bu .project fayl emas: " + fn); return; }

  var panels = collectPanels();
  var figs = [];
  for (var i = 0; i < panels.length; i++) {
    var p = panels[i];
    var n = p.Contour.Count;
    var rect = p.IsContourRectangle;
    if (rect && n <= 4) continue;
    var segs = panelSegs(p);
    if (segs.length < 3) continue;
    figs.push({ code: String(p.ArtPos || ""), name: String(p.Name || ""),
                w: p.ContourWidth, h: p.ContourHeight, json: JSON.stringify({ v: 1, segs: segs }) });
  }
  if (!figs.length) { alert("Modelda figurali panel topilmadi."); return; }

  var done = 0, used = {};
  var res = xml.replace(/<part\s[^>]*?\/?>/g, function (tag) {
    if (tag.indexOf(" mxFigure=") >= 0) return tag;
    var code = attr(tag, "code") || attr(tag, "part.code");
    var name = attr(tag, "name");
    var l = parseFloat(attr(tag, "dl") || attr(tag, "l")), w = parseFloat(attr(tag, "dw") || attr(tag, "w"));
    if (!code && !name) return tag;                          // list / qoldiq / havola qatorlari
    var hit = null;
    for (var j = 0; j < figs.length && !hit; j++) {
      var f = figs[j];
      var sizeOk = (Math.abs(f.w - l) < 2 && Math.abs(f.h - w) < 2) || (Math.abs(f.w - w) < 2 && Math.abs(f.h - l) < 2);
      if (f.code && f.code === code && sizeOk) hit = f;
    }
    for (var j2 = 0; j2 < figs.length && !hit; j2++) {
      var f2 = figs[j2];
      var sizeOk2 = (Math.abs(f2.w - l) < 2 && Math.abs(f2.h - w) < 2) || (Math.abs(f2.w - w) < 2 && Math.abs(f2.h - l) < 2);
      if (f2.name && name.indexOf(f2.name) >= 0 && sizeOk2) hit = f2;
    }
    if (!hit) return tag;
    done++;
    used[hit.code + "|" + hit.name] = 1;
    var end = tag.lastIndexOf("/>") >= 0 ? tag.lastIndexOf("/>") : tag.lastIndexOf(">");
    return tag.substring(0, end).replace(/\s+$/, "") + " mxFigure=\"" + esc(hit.json) + "\"" + tag.substring(end);
  });

  var out = fn.replace(/\.project$/i, "") + "_mx.project";
  system.writeTextFile(out, res);
  var miss = 0;
  for (var m = 0; m < figs.length; m++) if (!used[figs[m].code + "|" + figs[m].name]) miss++;
  alert("Tayyor: " + done + " ta detalga figura kromkasi yozildi" + (miss ? (", " + miss + " ta panel faylda topilmadi") : "") +
        ".\nYangi fayl: " + out);
}

main();
