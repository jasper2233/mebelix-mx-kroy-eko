/** MebeliX Kroy MCP — sozlamalar (muhit o'zgaruvchilari). */
import os from "node:os";
import path from "node:path";

export type GiblabMode = "off" | "cdp" | "profile";

export interface Config {
  /** MebeliX Kroy backend manzili (REST). */
  mxUrl: string;
  /** JWT (ixtiyoriy; MEBELIX_AUTH_REQUIRED=1 bo'lsa). */
  mxToken?: string;
  /** Fayllar yoziladigan papka (eksport, zip, skrinshot). */
  outDir: string;
  /** Onlayn tizimga ulanish usuli: off — yo'q, cdp — ishlayotgan Chrome (--remote-debugging-port), profile — o'z profili bilan Chrome. */
  giblabMode: GiblabMode;
  giblabCdpUrl: string;
  giblabProfileDir: string;
  giblabUrl: string;
  /** Onlayn loyihalarni o'zgartiradigan amallar (import, kroy, o'chirish, postprotsessor) ruxsati. */
  giblabAllowWrite: boolean;
  /** Yozish amallari faqat shu papka ichida (bo'sh — cheklov yo'q, lekin allowWrite baribir kerak). */
  giblabWorkFolder: string;
  /** Brauzer ko'rinadimi (profile rejimida). */
  giblabHeadless: boolean;
  /** Odam tezligi: har sichqoncha / klaviatura amalidan oldingi tanaffus (ms). Tez bosilsa onlayn tizim qotib qoladi. */
  giblabPaceMs: number;
  /** Kroy uchun standart sifat. */
  quality: "fast" | "normal" | "max";
}

function flag(v: string | undefined, d = false): boolean {
  if (v === undefined || v === "") return d;
  return !/^(0|false|no|off)$/i.test(v);
}

export function loadConfig(env: NodeJS.ProcessEnv = process.env): Config {
  const mode = (env.GIBLAB_MODE || "off").toLowerCase();
  return {
    mxUrl: (env.MX_URL || "http://127.0.0.1:8000").replace(/\/+$/, ""),
    mxToken: env.MX_TOKEN || undefined,
    outDir: env.MX_OUT_DIR || path.join(os.tmpdir(), "mxkroy-mcp"),
    giblabMode: mode === "cdp" || mode === "profile" ? mode : "off",
    giblabCdpUrl: env.GIBLAB_CDP_URL || "http://127.0.0.1:9222",
    giblabProfileDir: env.GIBLAB_PROFILE_DIR || path.join(os.homedir(), ".mxkroy-mcp", "chrome-profile"),
    giblabUrl: env.GIBLAB_URL || "https://giblab.com/",
    giblabAllowWrite: flag(env.GIBLAB_ALLOW_WRITE, false),
    giblabWorkFolder: env.GIBLAB_WORK_FOLDER || "",
    giblabHeadless: flag(env.GIBLAB_HEADLESS, false),
    giblabPaceMs: Math.max(0, Number(env.GIBLAB_PACE_MS ?? 450) || 0),
    quality: (["fast", "normal", "max"].includes(env.MX_QUALITY || "") ? env.MX_QUALITY : "normal") as Config["quality"],
  };
}
