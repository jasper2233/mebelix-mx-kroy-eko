/**
 * Onlayn drayver testi (ixtiyoriy): GIBLAB_TEST=1 bo'lsa Chrome o'z profili bilan (headless) ochiladi, giblab.com kirish sahifasi
 * yuklanadi, holat o'qiladi. Kirish talab qilinmaydi: faqat ulanish, sahifa kutubxonasi va o'qish yo'li tekshiriladi.
 * CDP rejimi: GIBLAB_TEST=cdp (Chrome --remote-debugging-port=9222 ishlayotgan bo'lishi kerak).
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import os from "node:os";
import path from "node:path";
import { loadConfig } from "../src/config.js";
import { GiblabDriver } from "../src/giblab/driver.js";

const MODE = process.env.GIBLAB_TEST;

test("giblab driver: connect, pagelib, status (login page)", { skip: !MODE ? "GIBLAB_TEST o'rnatilmagan" : false }, async (t) => {
  const cfg = loadConfig({
    ...process.env,
    GIBLAB_MODE: MODE === "cdp" ? "cdp" : "profile",
    GIBLAB_HEADLESS: process.env.GIBLAB_HEADLESS ?? "1",
    GIBLAB_PROFILE_DIR: process.env.GIBLAB_PROFILE_DIR ?? path.join(os.tmpdir(), "mxkroy-mcp-test-profile"),
    GIBLAB_ALLOW_WRITE: "0",
  });
  const g = new GiblabDriver(cfg);
  try {
    await g.ensure();
    const st = await g.status();
    t.diagnostic(JSON.stringify(st));
    assert.match(st.url, /giblab\.com/);
    assert.equal(typeof st.loggedIn, "boolean");
    const inv = await g.inventory();
    assert.ok(inv.length > 3, "sahifa inventari bo'sh");
    const tables = await g.gl<unknown[]>("tables()");
    assert.ok(Array.isArray(tables));
    // yozish amali ruxsatsiz — xato
    await assert.rejects(() => g.cut(), /GIBLAB_ALLOW_WRITE/);
    if (st.loggedIn) {
      const list = await g.openFolderPath("/");
      assert.ok(list && list.rows.length > 0, "loyihalar ro'yxati bo'sh");
      t.diagnostic(`ro'yxat: ${list!.rows.length} qator, papka «${list!.path}»`);
    }
  } finally {
    await g.close();
  }
});
