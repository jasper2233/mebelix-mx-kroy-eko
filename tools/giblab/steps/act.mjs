// Amallar ketma-ketligi (JSON fayl): [{t:"text",s:"Добавить карту кроя"}, {t:"click",x,y,mods:["Shift"],button}, {t:"move",x,y},
//   {t:"down",k:"Shift"}, {t:"up",k:"Shift"}, {t:"wait",ms}, {t:"shot",f:"a.png"}, {t:"row",s:"sokl"}]  run act.mjs <amallar.json>
import fs from "node:fs";
export default async ({ page, drv, args }) => {
  const acts = JSON.parse(fs.readFileSync(args[0], "utf8"));
  const out = [];
  for (const a of acts) {
    if (a.t === "text") out.push(await drv.clickText(a.s).then(() => "ok").catch((e) => String(e).slice(0, 80)));
    else if (a.t === "click") {
      for (const m of a.mods ?? []) await page.keyboard.down(m);
      await page.mouse.move(a.x - 8, a.y - 8); await page.waitForTimeout(250);
      await page.mouse.move(a.x, a.y, { steps: 4 }); await page.waitForTimeout(500);
      await page.mouse.click(a.x, a.y, { button: a.button ?? "left" }); await page.waitForTimeout(900);
      for (const m of (a.mods ?? []).reverse()) await page.keyboard.up(m);
    } else if (a.t === "move") { await page.mouse.move(a.x, a.y, { steps: 4 }); await page.waitForTimeout(400); }
    else if (a.t === "down") await page.keyboard.down(a.k);
    else if (a.t === "up") await page.keyboard.up(a.k);
    else if (a.t === "wait") await page.waitForTimeout(a.ms);
    else if (a.t === "shot") { await page.screenshot({ path: a.f, timeout: 120_000 }); out.push(a.f); }
    else if (a.t === "row") {
      const r = await drv.evaluate(`(() => { const d = [...document.querySelectorAll(".gwt-DialogBox")].pop();
        const tr = d && [...d.querySelectorAll("tr")].find((r) => r.cells.length >= 6 && [...r.cells].some((c) => (c.innerText || "").trim() === ${JSON.stringify(a.s)}));
        if (!tr) return null; const b = tr.getBoundingClientRect(); return { x: b.x + 150, y: b.y + b.height / 2 }; })()`);
      if (r) { await page.mouse.click(r.x, r.y); await page.waitForTimeout(700); }
      out.push(r ? "row" : "no row");
    }
  }
  return out;
};
