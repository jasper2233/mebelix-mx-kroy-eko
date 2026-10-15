# MebeliX Kroy MCP serveri (`mxkroy-mcp`)

MCP (Model Context Protocol) serveri — Claude Code / Claude Desktop va boshqa MCP mijozlari MebeliX Kroy bilan ishlashi,
onlayn tizim (giblab.com) bilan yonma-yon solishtirishi va korxona `.project` fayllaridagi avvalgi natijalar bilan
taqqoslashi uchun. Hamma narsa noldan yozilgan: onlayn tizimning kodi, resurslari ishlatilmaydi — faqat brauzer sahifasi
o'qiladi va sichqoncha/klaviatura hodisalari yuboriladi.

## O'rnatish va ishga tushirish

```bash
cd mcp
npm install            # @modelcontextprotocol/sdk 1.32, playwright 1.64, zod 4 (tools/node dagi portativ Node 24 ham bo'ladi)
npm run build          # dist/
npm test               # tutun testi (MebeliX Kroy :8000 ishlayotgan bo'lsa mx_* ham sinaladi)
```

Claude Code loyiha ildizidagi `.mcp.json` ni o'zi o'qiydi (`node mcp/dist/server.js`). Qo'lda:

```json
{ "mcpServers": { "mxkroy": { "command": "node", "args": ["D:/.../MebeliX_Kroy/mcp/dist/server.js"],
  "env": { "MX_URL": "http://127.0.0.1:8000", "GIBLAB_MODE": "off" } } } }
```

## Muhit o'zgaruvchilari

| O'zgaruvchi | Standart | Ma'nosi |
|---|---|---|
| `MX_URL` | `http://127.0.0.1:8000` | MebeliX Kroy backend |
| `MX_TOKEN` | — | JWT (`MEBELIX_AUTH_REQUIRED=1` bo'lsa) |
| `MX_OUT_DIR` | `%TEMP%/mxkroy-mcp` | eksport / hisobot / zip / skrinshot fayllari |
| `MX_QUALITY` | `normal` | kroy sifati: `fast` (≤ 2 s) / `normal` (≤ 17 s) / `max` |
| `GIBLAB_MODE` | `off` | `cdp` — ishlayotgan Chrome ga ulanish (`chrome.exe --remote-debugging-port=9222`, foydalanuvchi kirgan sessiya); `profile` — o'z profili bilan Chrome (birinchi marta foydalanuvchi o'zi kiradi) |
| `GIBLAB_CDP_URL` | `http://127.0.0.1:9222` | CDP manzili |
| `GIBLAB_PROFILE_DIR` | `~/.mxkroy-mcp/chrome-profile` | profil papkasi |
| `GIBLAB_HEADLESS` | `0` | `profile` rejimida oynasiz |
| `GIBLAB_ALLOW_WRITE` | `0` | onlayn loyihani o'zgartiruvchi amallar (import, «Раскроить», o'chirish, postprotsessor) ruxsati |
| `GIBLAB_WORK_FOLDER` | — | yozish amallari faqat shu papka ichida (masalan `test uchun`) |

## Vositalar (85 ta)

**`mx_*` — MebeliX Kroy REST**: `mx_health`, `mx_folders`, `mx_projects`, `mx_project` (summary / ops / full), `mx_project_create /
update / delete / copy / undo / redo / import / export`, `mx_operation_add / update / delete / get`, `mx_actions` (merge-same,
split-edges, optimize-ops, recode-xnc, clear, recalc-parametric), `mx_parts` (+ add / update / group_update / delete / move_to /
bulk), `mx_sheets` (+ set / from_warehouse), `mx_cut` (bitta yoki hamma operatsiya; `background=true` — fon vazifasi),
`mx_cut_all` (serverda bitta tarix qadami), `mx_jobs`, `mx_result` (summary / maps / remnants / full), `mx_variants`,
`mx_result_delete`, `mx_map_svg`, `mx_remnants_proposed / commit / rollback`, `mx_warehouse` (+ add / update / delete / request),
`mx_catalog` (+ sync), `mx_report`, `mx_labels`, `mx_postprocessors`, `mx_postprocess`, `mx_postprocess_xnc_all`, `mx_mes_export`,
`mx_mes_order`, `mx_mes_order_get`, `mx_mes_scan`, `mx_mes_webhook_test`, `mx_material_check`, `mx_queue` (buyurtmalar navbati va material bazasi), `mx_settings` (+ set), `mx_api` (istalgan yo'l).

**`compare_*`**: `compare_file_info` (fayldagi saqlangan natija), `compare_project` (import → hamma kroy → fayl bilan jadval:
listlar, F %, деловой m², kesish m, joylashmagan), `compare_job`, `compare_online` (MX ↔ onlayn ochiq loyiha).

**`giblab_*` — onlayn tizim (brauzer)**: `giblab_status`, `giblab_projects` (papka yo'li), `giblab_project_open / close`,
`giblab_operations`, `giblab_select_operation`, `giblab_tab`, `giblab_table` (sarlavha so'zlari bo'yicha), `giblab_cut_stats`
(bitta / `all`), `giblab_menu`, `giblab_dialogs` (tugma / klaviatura), `giblab_click`, `giblab_inventory` (o'xshashlik o'lchovi),
`giblab_screenshot`, `giblab_text`, `giblab_eval`, `giblab_pagelib` (sahifa kutubxonasi matni — Claude in Chrome bilan ham
ishlatiladi), `giblab_set_prompt_answer`; yozuvchilar (`[YOZADI]`): `giblab_cut`, `giblab_project_import`; `giblab_project_export`
faqat yuklab oladi.

## Ish oqimi (misollar)

```
compare_project  path="D:/.../1007 Yangibozor/01 shkaf.project"  quality="normal"
mx_projects q="3120"  →  mx_project pid=1000009  →  mx_cut pid=1000009  →  mx_result pid=… oid=…  →  mx_report pid=…
mx_postprocess pid=… oid=… key="machine:holzma_ptx"   (ro'yxat: mx_postprocessors)
giblab_projects folder="test uchun"  →  giblab_project_open name_or_id="test"  →  giblab_cut_stats all=true
compare_online pid=1000009 cut=true
```

## Eslatmalar

* Onlayn tizim «Раскроить» / «Удаление раскроя» / list tartibini o'zgartirish kabi amallardan keyin loyihani **darhol saqlaydi** —
  haqiqiy loyihalarda ishlatmang; `GIBLAB_WORK_FOLDER` bilan sinov papkasini cheklang.
* Onlayn postprotsessorlar faqat shanba–yakshanba kunlari ochiq (sayt bildirishnomasi).
* Katta loyihada (≈150 operatsiya, 8 karta) onlayn tizimning «Раскрой» varag'i brauzer renderini uzoq band qiladi (2026-10-15 da
  Claude in Chrome bilan tab muzlab qoldi); Playwright drayveri tizim oynalarini (`alert/prompt`) avtomatik yopadi
  (`giblab_set_prompt_answer`), lekin og'ir chizma kutishni talab qiladi.
* Fayllar `MX_OUT_DIR` ga yoziladi; korxona `.project` fayllarida mijoz ismlari bor — natijalarni ommaviy joyga chiqarmang.
