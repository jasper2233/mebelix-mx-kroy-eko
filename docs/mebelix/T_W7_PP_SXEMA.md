# T. W7 — Postprotsessor stanoklari: sozlamalar sxemasi (ParamGrid) va «Данные для этикеток» (v2.2, 2026-10-02)

Manba: `giblab_inventory/06_online_korik.md` §2 va onlayn sozlama sahifalari skrinshotlari (faqat funksional ma'no; parametr kalitlari,
yorliq tarjimalari, jadval ifodalari o'z sxemamiz sifatida yozilgan). Stanok **fayl formati** yozilmaydi — uni korxona dasturchilari
Jinja shablonida yozadi; bizda faqat sozlama, toza ma'lumot konteksti va ifodalarni hisoblash (CLAUDE.md 14-qoida).

## Fayllar
| Fayl | Vazifasi |
|---|---|
| `backend/app/services/pp_machine_schema.py` | 19 pil markazining sxemasi (75 parametr; 10 ta jadval — 8 tasida standart qatorlar, 2 tasi PARTS_UDI), tur/diapazon va jadval tekshiruvi |
| `backend/app/services/pp_machine_ctx.py` | saqlash (`pp_machines`), sxema javobi, maydonlarni hisoblash (`label_vars` + `expr`), shablon konteksti |
| `backend/app/api_pp_machines.py` | `GET …/schema`, `PUT …/params`, `PUT …/label-fields`, `POST …/label-fields/preview` |
| `frontend/src/features/settings/machines/` | `ParamGrid.tsx` (umumiy), `LabelFieldsTable.tsx`, `MachineSettings.tsx`, `machinesApi.ts`, `machines.css` |
| `frontend/scripts/i18n_w7.py` | interfeys matnlari (`ppm.*`) |
| `backend/tests/test_pp_schema_w7.py`, `test_pp_schema_w7_ctx.py` | 28 test |

## Turlar va tekshiruv
`bool` (qat'iy true/false) · `int` (butun, diapazon) · `mm` / `float` (chekli son, diapazon) · `string` · `path` · `choice`.
`path` — **faqat satr**: server fayl tizimiga yozmaydi va o'qimaydi (mavjud bo'lmagan yo'l ham saqlanadi); faqat `< > " | ? *` va boshqaruv
belgilari rad etiladi. `choice` — variantlardan biri; ro'yxati to'liq ma'lum bo'lmagan joyda `custom: true` (boshqa matn ham mumkin).
`enabled_if` — parametr boshqa bool yoqilgandagina faol (UI da xira; server baribir saqlaydi). Parametr guruhlari: Общие, Печать этикеток,
Этикетки, Специализированные, Торцовка, Ограничения.

## API
- `GET /api/postprocessors/machines/{key}/schema` → `{key, name, group, info, groups: [{key, ru, uz, params: [{key, type, ru, uz, default, value,
  modified, min, max, options, custom, enabled_if}]}], values, defaults, modified, label_table: {title, kind: labels|udi, max_rows, rows, defaults, is_default} | null}`.
  Ishlov markazlari (`cnc`) — bo'sh sxema.
- `PUT …/params` `{params: {param: qiymat}}` — **to'liq almashtirish** (yuborilmagan — standart); standartga teng qiymat saqlanmaydi (siyrak).
- `PUT …/label-fields` `{label_fields: [{name, expr}]}` — nom bo'sh/takror/80+ belgi emas; ifoda `expr.compile_check` (bo'sh ifoda = «»);
  ≤ 100 qator; standart jadvalga teng bo'lsa saqlanmaydi («standartga qaytarish» = standart jadvalni yuborish).
- `POST …/label-fields/preview` `{project_id?, op_id?, part_uid?, fields?}` — har ifoda tanlangan detal kontekstida hisoblanadi (loyiha berilmasa —
  namuna loyiha; `fields` — saqlanmagan qoralama). Javob: `fields[{name, expr, ok, type, value, text, error, stage, name_error}]`, `variables[]` (ifoda yordamchisi uchun).
- Xato: noma'lum stanok / parametr kaliti, noto'g'ri qiymat yoki ifoda — **400** `{detail, errors: [...]}`, hech narsa saqlanmaydi (atomik).
  Jadvali yo'q stanokda (`homag_chf`, `elmo3`, … va ishlov markazlari) label-fields/preview — 400.
- Mavjud `GET/PUT /postprocessors/machines` o'zgarmagan; `PUT` endi `params` va `label_fields` ni saqlab qoladi. `POST /postprocessors/preview` ga ixtiyoriy `machine` qo'shildi.

## Saqlash (`pp_machines` sozlamasi)
`{enabled, profile, prefix, params: {stanok: {param: qiymat}}, label_fields: {stanok: [{name, expr}]}}`. Standart qiymatlar kodda (sxema), saqlanadigani — farqlari.

## Postprotsessor konteksti (CS va XNC)
`machine:<kalit>` bilan yuklab olishda (yoki preview da `machine` berilsa): `machine = {key, name, group, params, label_fields}`; boshqa hollarda `machine = None`.
CS: `maps[].placements[].label` / `label_text` va `parts[].label` / `label_text` — har detal uchun hisoblangan `{maydon nomi: qiymat}` (tipli) va `{nom: matn}`
(Java uslubidagi matn: `2.0`, `true`); xato — qiymat `#ERR` (jim 0 emas) va `label_warnings: [{field, expr, message, error, count, part_uid}]`,
javobda `X-Label-Warnings: <soni>` sarlavhasi. Jinja `render` yordamchi jarayonda — kontekst faqat oddiy tiplar. Maydon ifodalari fayl mazmuni
interfeys tiliga bog'liq bo'lmasin deb `ru` sana nomlari bilan hisoblanadi (`pp_machine_ctx.LABEL_LANG`).

## Etiketka o'zgaruvchilari (`label_vars`)
GibLab nomlari taxallus sifatida ishlaydi: `usedCount`, `count`, `totalCount`, `indexInOperation`, `length/width`, `detail.length/width`, `txt`, `waste`,
`ets/ebs/els/ers`, `ett…`, `etn…`, `XNC1/XNC2`, `grtn/grbn/grln/grrn` (+ `grt c/w/d/o`), `mill/drill/groove`. Hammasi 19 stanokning standart jadvallarida
sinalgan (namuna detalda xatosiz hisoblanadi). `grt*` va `indexInOperation` taxalluslarini W9 qo'shgan (aynan shu ma'noda).

## Ochiq savollar
Hisobot oxirida (S_ISH_QOIDALARI.md tuzilishida).
