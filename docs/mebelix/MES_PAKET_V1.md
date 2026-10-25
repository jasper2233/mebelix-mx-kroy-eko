# MES paketi v1 — tayyor kroyni MebeliX Kroy dan MES ga topshirish shartnomasi

> Holat: **taklif (v1, kelishiladi)** · Sana: 2026-10-18 · Tomonlar: MebeliX Kroy (MX) jamoasi va MES dasturchilari.
> MX tomonda paket **quruvchi** tayyor: `GET /api/projects/{id}/mes-package?version=1` (hech qayerga yubormaydi).
> MES tomonda qabul qiluvchi (ingest) — MES jamoasi yozadi. Bu hujjatdagi barcha misollar **sintetik** (haqiqiy mijoz,
> buyurtma yoki korxona fayllari ishlatilmagan).

## 1. Maqsad va qisqa tavsif

MES bugun buyurtmaga texnolog yuklagan kroy loyihasi faylidan detal, nusxa (QR), marshrut, kesish xaritasi va foydali
qoldiqlarni oladi. MX bu oqimda **kroy dasturining o'rnini** egallaydi: kroy MX da qilinadi, tayyor natija esa bitta JSON
paket bilan MES ga topshiriladi. Paket MES dagi ichki tuzilmalarga to'g'ridan-to'g'ri o'giriladi:

| Paket bo'limi | MES dagi joyi (ingest) |
|---|---|
| `products[]` | `ParsedProduct` → `Product` |
| `parts[]` | `ParsedPart` → `Part` (kod, o'lcham, qalinlik, `material_name`, `edges` l/r/t/b, `txt`) |
| `parts[].instances[]` | `PartInstance` (`qr_text`, `pattern_no`, `cell_index`) |
| `materials[]`, `edge_bands[]` | `ParsedMaterial` (sheet / band), keyin katalog kodi bilan bog'lanadi |
| `cut_maps[]` | `CutmapModel.materials[] → CutmapSheet (no, L, W, mult, parts=cells, cuts)` |
| `remnants[]` | `WasteItem` (`qr_text = ATX-…`, `sheet_no`, `length`, `width`, `material_name`) |
| `consumption[]` | `order.material_usage` + ombor hujjati (sarf avtomatik — foydalanuvchi qarori) |
| `xnc_programs[]` | `Part.xnc_summary` (statistika); ishlov dasturining o'zi — postprotsessor faylida |
| `xnc_tools` | moliya: har asbob ishi (teshik / metr) — 4.10b |
| `postprocessor_files[]` | `OrderFile` (kind: SCX / saw / cnc — kelishiladi), `part_id` bilan bog'lanadi |

Asosiy qoida: **MES ishlov (stanok) oqimi faqat shu paketda tegishli postprotsessor fayli kelgan bo'lsa ishga tushadi**
(`machining`). Fayl kelmagan stanok uchun MES marshrutda ishlov qadamini ochmaydi yoki texnologga «fayl yo'q» deb ko'rsatadi.

## 2. Transport (taklif — kelishiladi)

1. MX dagi «MES» tugmasi (keyingi bosqich, hozir yo'q) loyiha uchun paketni quradi va MES ga yuboradi:
   `POST {MES}/api/v1/orders/{mes_order_id}/kroy-package`, `Content-Type: application/json`, tana — shu paket.
2. MES javobi: `201 {"order_id": …, "order_number": "B-YYYY-NNN", "redirect_url": "/orders/{id}"}` yoki xato
   `{"detail": "<o'zbekcha matn>"}` (MES xato formati).
3. Muvaffaqiyatda MX foydalanuvchini MES dashboardiga (`redirect_url`) o'tkazadi.
4. Qayta yuborish = MES dagi «qayta yuklash» qoidasi: hech bir postda skan bo'lmagan bo'lsa avvalgi natija almashtiriladi,
   aks holda MES rad etadi (409 + sabab).
5. Paket hajmi: postprotsessor fayllari inline (base64) — standart; juda katta bo'lsa (`files=meta`) fayl o'rniga MX dagi
   `url` beriladi va MES uni servis tokeni bilan oladi (kelishiladi).

## 3. MX endpointi (tayyor)

`GET /api/projects/{id}/mes-package?version=1` — paketni quradi va JSON qaytaradi; loyiha o'zgarmaydi.

| Parametr | Qiymat | Ma'nosi |
|---|---|---|
| `version` | `1` | boshqasi — 400 |
| `pp` | `enabled` (standart) · `all` · `none` · `machine:holzma_ptx,tpa` | qaysi stanok fayllari kiradi: `enabled` — ochilgan, «Станок используется на предприятии» belgilangan va ishlaydigan stanoklar; `all` — barcha ochilgan va ishlaydiganlar; ro'yxat — aniq stanoklar (**yopiq stanok so'ralsa 403**, noma'lum — 400) |
| `files` | `inline` (standart) · `meta` | fayl mazmuni base64 da yoki faqat nom/hajm/sha256 + `url` |
| `mes_order_id` | butun son | MES `order.id` (MX hozir saqlamaydi — MES tugmasi oqimida beriladi) |
| `mes_order_number` | `B-YYYY-NNN` | MES buyurtma raqami; berilmasa loyihaning `mes_order_ref` i shu shaklda bo'lsa o'sha olinadi |

`GET /api/mes-package/schema?version=1` — paketning JSON sxemasi (6-bo'limdagi bilan bir xil, koddan hosil qilinadi).

Kod: `backend/app/services/mes_package.py` (pydantic modellar, quruvchi), `backend/app/api_mes_package.py` (endpoint),
testlar: `backend/tests/test_mes_package_x1018.py`.

## 4. Paket tuzilmasi

Birliklar: uzunlik — **mm**, maydon — m², kromka — m. Koordinatalar — listning chap-yuqori burchagidan, `x` list
uzunligi (`L`) bo'ylab o'ngga, `y` list eni (`W`) bo'ylab pastga. Barcha `ref` / `*_ref` maydonlari — paket ichidagi
havolalar (MX operatsiya id lari), MES ularni saqlashi shart emas.

### 4.1 `package`
`format` = `"mebelix.kroy.mes-package"`, `version` = `1`, `generated_at` (UTC ISO 8601), `generator`, `checksum_algorithm`
= `"sha256"`, `units`. MES `format` va `version` ni tekshiradi; noma'lum versiya — rad etiladi.

### 4.2 `source` — manba
| Maydon | Tavsif |
|---|---|
| `project_id`, `project_number`, `project_name` | MX loyihasi (id — matn, raqam — MX «Заказ ID») |
| `customer` | buyurtmachi (ma'lumot uchun; MES dagi mijoz — MES ning o'zi) |
| `mes_order_id`, `mes_order_number` | MES buyurtmasi bilan bog'lanish; `mes_order_number` QR va ATX ID larga kiradi |
| `mes_order_ref` | MX dagi xom havola |
| `kind` | `bazis_file` — Bazis fayli importi (mahsulotda `product.import` belgisi), `project_file` — boshqa kroy loyihasi fayli importi, `manual` — qo'lda kiritilgan |
| `order_date`, `ready_date`, `currency` | MX sarlavhasidan |

### 4.3 `products[]` — mahsulotlar
`mx_id`, `code` (QR ga kiradi; kodi bo'sh bo'lsa — nomi, MES dagi kabi), `name`, `qty`. Faqat detali bor mahsulotlar.

### 4.4 `materials[]` va `edge_bands[]`
- Material: `ref`, `kind` (`sheet` — listli, `linear` — pogonaj, `nest` — nesting), `code`, `name`, `thickness`, `catalog_id`.
- Kromka: `ref`, `code`, `name`, `symbol` (detal chekidagi belgi), `thickness`, `width`, `work_m` (yopishtirish uzunligi),
  `material_m` (zaxira bilan sarf), `catalog_id`.
- MES detallarda material va kromkani **nom** bilan saqlaydi — paketda **kod ham, nom ham** bor. Katalog kodi bilan
  bog'lash (`catalog_id` = MES `M-…` kodi) — kelishiladigan savol.

### 4.5 `parts[]` — detallar va nusxalar
| Maydon | Tavsif |
|---|---|
| `mx_id`, `mx_uid` | MX detal id va loyiha ichidagi raqami (MX etiketkasidagi «ID») |
| `key` | `{mahsulot}_{detal}` — MES `ParsedPart.key` bilan bir xil |
| `product_code`, `product_mx_id`, `code`, `name` | detal kodi bo'sh bo'lsa — `uid` 3 xonali (`007`) |
| `material_ref`, `length`, `width`, `thickness`, `grain` | tayyor o'lcham (mm); `grain` — tekstura (aylantirilmaydi) |
| `qty_total`, `qty_from_stock` | ОК = detal soni × mahsulot soni; МК — omborda tayyor (kesilmaydi) |
| `edges` | `l` / `r` / `t` / `b` → `{ref, symbol, name}` (MX: top/bottom — uzunlik bo'yicha, left/right — eni bo'yicha) |
| `xnc_refs` | bog'langan XNC dasturlari (`xnc_programs[].mx_op_id`) |
| `instances[]` | har jismoniy nusxa: `n`, `qr`, `pattern_no`, `cell_index`, `sheet_copy` |

**QR qoidasi (MES `instance_qr`):** `{buyurtma}_{mahsulot}_{detal}` — nusxa bitta bo'lsa suffikssiz, bir nechta bo'lsa
`_1 … _n`. Misol: `B-2026-001_SH01_001_1`. Buyurtma raqami noma'lum bo'lsa `qr = null` (MES `key` va `n` dan o'zi quradi).
Kodlar skaner o'qiy oladigan **ko'rinadigan ASCII** bo'lishi kerak (MES `_scannable`); mos kelmasa paket `warnings` ga
yozadi (MX rad etmaydi — MES rad etishi mumkin). Takror `key` — detal kodiga `-2`, `-3` qo'shiladi va ogohlantiriladi.

**Nusxa ↔ katak:** nusxalar kesish xaritasidagi kataklarga tartib bilan bog'lanadi: `pattern_no` = `cut_maps[].sheets[].no`,
`cell_index` = shu andozadagi `cells[].cell`, `sheet_copy` = andozaning nechanchi jismoniy listi (1 … `mult`). Joyi yo'q
nusxa (kroyga kirmagan) — `pattern_no = null` va `warnings` da ro'yxat.

### 4.6 `sheets[]` — ishlatilgan listlar
`material_ref`, `length`, `width`, `qty`, `source` (`new` — butun list, `remnant` — ombordagi qoldiqdan), `remnant_id`.

### 4.7 `cut_maps[]` — kesish xaritasi (har list geometriyasi)
Har material uchun: `material_ref`, `kind`, `kerf` (propil, mm), `sheets[]`:
| Maydon | Tavsif |
|---|---|
| `no` | **global andoza raqami** (barcha materiallar bo'ylab 1 dan) — MES `CutmapSheet.no` |
| `index` | MX ichidagi karta raqami |
| `L`, `W`, `mult` | list o'lchami va shu andozadan nechta list kesiladi |
| `is_remnant`, `remnant_id` | ombordagi qoldiqdan kesilganmi |
| `fill_percent`, `cut_length_m` | to'ldirish % va kesish uzunligi (m) |
| `cells[]` | detal va qoldiq kataklari: `cell`, `x`, `y`, `w` (L bo'ylab), `h` (W bo'ylab), `waste`, `part_uid`, `part_key`, `rot`, `eW` = [chap, o'ng], `eH` = [tepa, past] — joylashgan holatdagi kromka belgilari; qoldiqda `business`, `remnant_no`; nestingda `angle`, `outline` |
| `cuts[]` | gilyotina kesish chiziqlari `{x1, y1, x2, y2}` (chiziq — bo'lakning oxirgi chegarasi, propil shu yerdan); torsovka chiziqlari ham. `linear` / `nest` da bo'sh |
| `commands[]` | arra buyruqlari: `R` burish, `T` torsovka, `C` kesish, `P` detal, `W` chiqindi; `level` — kesim darajasi, `size`, `count`, `ref` |

### 4.8 `remnants[]` — foydali (деловой) qoldiqlar → ombor
Har **jismoniy** qoldiq alohida yozuv (andoza `mult > 1` bo'lsa har list uchun — MES TODO #7 shu bilan yopiladi):
`id` = `ATX-{buyurtma}-{n}` (material/list tartibida raqamlanadi; buyurtma noma'lum bo'lsa `null`), `n`, `material_ref`,
`material_code`, `material_name`, `thickness`, `sheet_no`, `sheet_copy`, `remnant_no` (MX «Д» raqami), foydali o'lcham
`length`×`width` (torsovkadan keyin) va xom o'lcham `raw_length`×`raw_width` (omborga shu yoziladi), `to_warehouse`
(`false` — mijoz olib ketadi, MX «Исп. кол-во»). Mayda (foydali emas) qoldiqlar faqat `cells[]` da (`business=false`).

### 4.9 `consumption[]` — sarf (avtomatik hujjat)
MX «Требование на склад» qatorlari: `material_ref`, `type` (CS / CL / CN / EL / SP / O), `code`, `name`, `unit`
(`sheets`, `pcs`, `m`, `m2` …), `qty`, `remnant_id` (ombordagi qoldiqdan ishlatilgan list). Foydalanuvchi qarori:
sarf va qoldiq kirimi MES da **avtomatik** yoziladi (omborchi tasdig'isiz) — qachon (paket qabul qilinganda yoki ARRA
skanida) — 8-bo'lim savoli.

### 4.10 `xnc_programs[]`
`mx_op_id`, `code`, `name`, `qty`, `part_uid`, `part_key`, `stats` (`drills` — teshiklar soni, `mill_m` — frezalash m,
`saw_m` — arra m). Dasturning stanok formatidagi o'zi — `postprocessor_files[]` da.

### 4.10b `xnc_tools` — XNC ishi asbob bo'yicha (2026-10-25, MES moliya uchun)
Foydalanuvchi qarori: MES moliya bo'limi har bir asbob ishiga **alohida narx** qo'yadi — parma uchun **teshik soni**, freza va
arra uchun **metr**. MX buyurtmadagi XNC detallar soni va har asbob qilgan ishni yuboradi (narxni MX hisoblamaydi).
`GET /api/projects/{pid}/xnc-tools` — xuddi shu ma'lumot alohida.

| Maydon | Ma'nosi |
|---|---|
| `xnc_ops` | XNC operatsiyalar soni |
| `xnc_parts` | XNC ishlovi bor detallar soni (dona; ОК − МК, mahsulot soni bilan) |
| `tools[].kind` | `drill` (parma) · `mill` (freza) · `saw` (arra pazi) |
| `enabled` | «XNC → MES» sozlamasida yuborish o'chirilgan bo'lsa — `false` va bo'sh ro'yxat |
| `tools[].key`, `mes_code` | asbob kaliti (`kind\|nom\|diametr\|tomon\|teshib_o'tadi`) va MES (moliya) dagi kodi — MX da «Настройки → MES интеграция → XNC → MES» da beriladi |
| `tools[].name`, `d` | asbob nomi (dasturdagi `T`; bo'sh bo'lsa `D{diametr}`) va diametri, mm |
| `tools[].side`, `through` | parma: `face` (yuza) / `side` (yon, qirra); `through` — yuza teshigi detalni teshib o'tadi |
| `tools[].depths` | uchragan chuqurliklar, mm |
| `tools[].holes` | parma: teshiklar soni (buyurtma bo'yicha jami, massivlar yoyilgan) |
| `tools[].mill_m` | freza: kontur uzunligi, m (chiziq + yoy, to'rtburchak / ellips; cho'ntak C=3 kirmaydi) |
| `tools[].mill_pass_m` | freza: chuqurlik qadamlari (SDP) bilan o'tilgan yo'l, m |
| `tools[].saw_m` | arra pazi: metr × o'tishlar |
| `tools[].parts`, `ops` | nechta detal (dona) va nechta XNC operatsiyada |
| `tools[].uses[]` | operatsiyalar bo'yicha: `op_id`, `code`, `part_id`, `part_uid`, `part_name`, `qty`, 1 dona uchun `holes` / `mill_m` / `saw_m` |
| `errors[]` | hisoblanmagan dasturlar (`op_id`, `code`, `error`); dasturda bajarib bo'lmaydigan kontur bo'lsa frezalash 0 |
| `tools[].known` | asbob korxonaning «bizning asboblar» ro'yxatida va faol (`false` — ro'yxatda yo'q yoki «Исп.» o'chirilgan; ro'yxat bo'sh bo'lsa hammasi `true`). MES narxni faqat `known` asboblar uchun qo'yadi, qolganini operatorga ko'rsatadi |
| `tools[].mismatch` | asbob nomidagi raqam diametrga mos emas (masalan `Bore35`, D 5) — XNC dasturida xato bo'lishi mumkin |
| `warnings[]` | `unknown_tool:<nom> D<d>` va `name_diameter_mismatch:<nom> D<d>` qatorlari |

Sozlamada o'chirilgan qiymatlar (masalan arra yoki o'tishlar metri, batafsil `uses`) 0 / bo'sh yuboriladi.
Teshiklar va metrlar yig'indisi `xnc_programs[].stats` bilan aynan bir xil (60 ta korxona loyihasi, 2898 XNC dastur — farq 0).

### 4.11 `postprocessor_files[]` — stanok fayllari
**Faqat mijoz uchun ochilgan postprotsessorlar** (MX «Postprotsessorlarga kirish», 7-bo'lim) va ishlaydigan
(o'rnatilgan generator yoki biriktirilgan shablon) stanoklar. Yopiq postprotsessor paketga hech qachon kirmaydi.

| Maydon | Tavsif |
|---|---|
| `format_id` | `machine:<kalit>` |
| `machine` | `{key, name, label, group (saw / cnc), mes_machine_id}` — stanokka bog'lanish; `mes_machine_id` — MES `machine.id`, bog'lash jadvali kelishiladi |
| `source` | `native` (MX o'rnatilgan generatori) / `template` (korxona shabloni) |
| `op_ref`, `part_keys` | arra fayli — material (`material_ref`); ishlov markazi fayli — XNC dasturi va uning detali (`key`) |
| `file_name`, `media_type`, `size` | fayl nomi, turi, hajmi (bayt) |
| `sha256` | xom baytlar nazorat summasi (hex) — MES qabul qilganda tekshiradi |
| `content_base64` / `url` | `files=inline` — mazmun; `files=meta` — MX dan olish yo'li (Bearer token bilan) |

`machining`: `saw_ready` / `cnc_ready` — shu turdagi kamida bitta fayl bor; `files` — fayllar soni; `rule` — qoida matni.
**MES qoidasi:** ishlov qadami (ARRA fayli, PRISADKA/ROVER dasturi) faqat fayl kelgan stanok va detal uchun ochiladi.

### 4.12 `warnings[]`
O'zbekcha matnlar: buyurtma raqami yo'qligi, skaner o'qiy olmaydigan kodlar, takror kalitlar, kroy qilinmagan
materiallar, joyi yo'q nusxalar, chiqmagan fayllar (masalan stanok formati kesim darajasini qo'llamaydi — avval MX da
qayta kroy kerak). MES ularni texnologga ko'rsatadi.

## 5. Sintetik misol (qisqartirilgan)

Bitta mahsulot «SH01 Shkaf», 3 xil detal (6 dona), bitta kromka, bitta XNC dasturi; ochilgan postprotsessorlar —
HOLZMA (*.ptx) arra va TPA ishlov markazi. Ro'yxatlar va base64 mazmun qisqartirilgan (`…`).

```json
{
 "package": {
  "format": "mebelix.kroy.mes-package",
  "version": 1,
  "generated_at": "2026-10-18T07:22:34Z",
  "generator": "MebeliX Kroy",
  "checksum_algorithm": "sha256",
  "units": {
   "length": "mm",
   "area": "m2",
   "edge": "m"
  }
 },
 "source": {
  "system": "mebelix-kroy",
  "project_id": "a811e43e8633",
  "project_number": 1000001,
  "project_name": "Namuna shkaf",
  "customer": "Namuna mijoz",
  "mes_order_id": null,
  "mes_order_number": "B-2026-001",
  "mes_order_ref": "B-2026-001",
  "kind": "manual",
  "order_date": "2026-10-18",
  "ready_date": "2026-10-18",
  "currency": "UZS"
 },
 "products": [
  {
   "mx_id": "5a9739626c87",
   "code": "SH01",
   "name": "Shkaf",
   "qty": 1
  }
 ],
 "materials": [
  {
   "ref": "c83528d035d4",
   "kind": "sheet",
   "code": "LDSP-16-OQ",
   "name": "LDSP 16 oq",
   "thickness": 16.0,
   "catalog_id": null
  }
 ],
 "edge_bands": [
  {
   "ref": "c657fcd348b3",
   "code": "PVC-0.4-19",
   "name": "PVC 0.4x19 oq",
   "symbol": "A",
   "thickness": 0.0,
   "width": 19.0,
   "work_m": 4.9,
   "material_m": 5.02,
   "catalog_id": null
  }
 ],
 "parts": [
  {
   "mx_id": "ddb8f6085a5a",
   "mx_uid": 1,
   "key": "SH01_001",
   "product_code": "SH01",
   "product_mx_id": "5a9739626c87",
   "code": "001",
   "name": "Yon devor",
   "material_ref": "c83528d035d4",
   "length": 2000.0,
   "width": 560.0,
   "thickness": 16.0,
   "qty_total": 2,
   "qty_from_stock": 0,
   "grain": true,
   "edges": {
    "t": {
     "ref": "c657fcd348b3",
     "symbol": "A",
     "name": "PVC 0.4x19 oq"
    }
   },
   "xnc_refs": [],
   "instances": [
    {
     "n": 1,
     "qr": "B-2026-001_SH01_001_1",
     "pattern_no": 1,
     "cell_index": 1,
     "sheet_copy": 1
    },
    {
     "n": 2,
     "qr": "B-2026-001_SH01_001_2",
     "pattern_no": 1,
     "cell_index": 2,
     "sheet_copy": 1
    }
   ]
  },
  {
   "mx_id": "5ebbc182e3bd",
   "mx_uid": 2,
   "key": "SH01_002",
   "product_code": "SH01",
   "product_mx_id": "5a9739626c87",
   "code": "002",
   "name": "Tom",
   "material_ref": "c83528d035d4",
   "length": 900.0,
   "width": 560.0,
   "thickness": 16.0,
   "qty_total": 1,
   "qty_from_stock": 0,
   "grain": true,
   "edges": {
    "t": {
     "ref": "c657fcd348b3",
     "symbol": "A",
     "name": "PVC 0.4x19 oq"
    }
   },
   "xnc_refs": [
    "9ba7fbd96bad"
   ],
   "instances": [
    {
     "n": null,
     "qr": "B-2026-001_SH01_002",
     "pattern_no": 1,
     "cell_index": 3,
     "sheet_copy": 1
    }
   ]
  }
 ],
 "sheets": [
  {
   "material_ref": "c83528d035d4",
   "length": 2750.0,
   "width": 1830.0,
   "qty": 2,
   "source": "new",
   "remnant_id": null
  }
 ],
 "cut_maps": [
  {
   "material_ref": "c83528d035d4",
   "kind": "sheet",
   "kerf": 3.0,
   "sheets": [
    {
     "no": 1,
     "index": 1,
     "L": 2750.0,
     "W": 1830.0,
     "mult": 1,
     "is_remnant": false,
     "remnant_id": null,
     "fill_percent": 87.04,
     "cut_length_m": 13.648,
     "cells": [
      {
       "cell": 1,
       "x": 5.0,
       "y": 5.0,
       "w": 2000.0,
       "h": 560.0,
       "waste": false,
       "part_uid": 1,
       "part_key": "SH01_001",
       "rot": false,
       "eW": [
        null,
        null
       ],
       "eH": [
        "A",
        null
       ]
      },
      {
       "cell": 2,
       "x": 5.0,
       "y": 568.0,
       "w": 2000.0,
       "h": 560.0,
       "waste": false,
       "part_uid": 1,
       "part_key": "SH01_001",
       "rot": false,
       "eW": [
        null,
        null
       ],
       "eH": [
        "A",
        null
       ]
      },
      {
       "cell": 3,
       "x": 5.0,
       "y": 1131.0,
       "w": 900.0,
       "h": 560.0,
       "waste": false,
       "part_uid": 2,
       "part_key": "SH01_002",
       "rot": false,
       "eW": [
        null,
        null
       ],
       "eH": [
        "A",
        null
       ]
      },
      {
       "cell": 5,
       "x": 2008.0,
       "y": 5.0,
       "w": 737.0,
       "h": 1820.0,
       "waste": true,
       "rot": false,
       "business": true,
       "remnant_no": 1
      }
     ],
     "cuts": [
      {
       "x1": 5.0,
       "y1": 0.0,
       "x2": 5.0,
       "y2": 1830.0
      },
      {
       "x1": 2745.0,
       "y1": 0.0,
       "x2": 2745.0,
       "y2": 1830.0
      },
      {
       "x1": 5.0,
       "y1": 5.0,
       "x2": 2745.0,
       "y2": 5.0
      }
     ],
     "commands": [
      {
       "code": "T",
       "level": 1,
       "size": 2.0,
       "count": 1,
       "ref": ""
      },
      {
       "code": "C",
       "level": 1,
       "size": 2000.0,
       "count": 1,
       "ref": ""
      },
      {
       "code": "T",
       "level": 2,
       "size": 2.0,
       "count": 1,
       "ref": ""
      },
      {
       "code": "P",
       "level": 2,
       "size": 560.0,
       "count": 2,
       "ref": "1"
      }
     ]
    }
   ]
  }
 ],
 "remnants": [
  {
   "id": "ATX-B-2026-001-1",
   "n": 1,
   "material_ref": "c83528d035d4",
   "material_code": "LDSP-16-OQ",
   "material_name": "LDSP 16 oq",
   "thickness": 16.0,
   "sheet_no": 1,
   "sheet_copy": 1,
   "remnant_no": 1,
   "length": 737.0,
   "width": 1820.0,
   "raw_length": 742.0,
   "raw_width": 1830.0,
   "to_warehouse": true
  }
 ],
 "consumption": [
  {
   "material_ref": "c657fcd348b3",
   "type": "EL",
   "code": "PVC-0.4-19",
   "name": "PVC 0.4x19 oq",
   "unit": "m",
   "qty": 5.02,
   "remnant_id": null
  },
  {
   "material_ref": "c83528d035d4",
   "type": "CS",
   "code": "LDSP-16-OQ",
   "name": "LDSP 16 oq",
   "unit": "sheets",
   "qty": 2.0,
   "remnant_id": null
  }
 ],
 "xnc_programs": [
  {
   "mx_op_id": "9ba7fbd96bad",
   "code": "SH01_002",
   "name": "Tom",
   "qty": 1,
   "part_uid": 2,
   "part_key": "SH01_002",
   "stats": {
    "drills": 1.0,
    "mill_m": 0.0,
    "saw_m": 0.0
   }
  }
 ],
 "postprocessor_files": [
  {
   "format_id": "machine:holzma_ptx",
   "machine": {
    "key": "holzma_ptx",
    "name": "HOLZMA PTX",
    "label": "Пильный центр HOLZMA (*.ptx)",
    "group": "saw",
    "mes_machine_id": null
   },
   "source": "native",
   "op_ref": "c83528d035d4",
   "part_keys": [],
   "file_name": "1000001_Namuna_shkaf_LDSP_16_oq.ptx",
   "media_type": "application/octet-stream",
   "size": 1190,
   "sha256": "2db626f7f650fe67d8bfe615b8eedea6cd0b3676e2c2a8333fce900539b8f93f",
   "content_base64": "SEVBREVSLDEuMTMsMTAwMDAwMV9OYW11…",
   "url": null
  },
  {
   "format_id": "machine:tpa",
   "machine": {
    "key": "tpa",
    "name": "TPA",
    "label": "Обрабатывающий центр TPA Genesis Evolution 8.9",
    "group": "cnc",
    "mes_machine_id": null
   },
   "source": "native",
   "op_ref": "9ba7fbd96bad",
   "part_keys": [
    "SH01_002"
   ],
   "file_name": "SH01_002.CNC",
   "media_type": "application/octet-stream",
   "size": 400,
   "sha256": "af8dfa145d818b2c45fd6b2b4d7a0e4be36ea81d39397a2c21e04e5bd62a2009",
   "content_base64": "VFBBXEFMQkFUUk9TXEVESUNBRFwwMS4w…",
   "url": null
  }
 ],
 "machining": {
  "rule": "MES ishlov oqimi faqat shu paketda postprotsessor fayli kelgan stanok/detal uchun ishga tushadi",
  "saw_ready": true,
  "cnc_ready": true,
  "files": 2
 },
 "warnings": []
}
```

## 6. JSON sxema (v1)

Koddan hosil qilingan (`MesPackageV1.model_json_schema()`, `GET /api/mes-package/schema?version=1`). Qo'shimcha
maydonlar taqiqlangan (`additionalProperties: false`) — v1 doirasida yangi maydon faqat yangi versiyada.

<details><summary>Sxemani ochish</summary>

```json
{
 "$defs": {
  "Consumption": {
   "additionalProperties": false,
   "properties": {
    "material_ref": {
     "title": "Material Ref",
     "type": "string"
    },
    "type": {
     "title": "Type",
     "type": "string"
    },
    "code": {
     "title": "Code",
     "type": "string"
    },
    "name": {
     "title": "Name",
     "type": "string"
    },
    "unit": {
     "title": "Unit",
     "type": "string"
    },
    "qty": {
     "title": "Qty",
     "type": "number"
    },
    "remnant_id": {
     "anyOf": [
      {
       "type": "integer"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "title": "Remnant Id"
    }
   },
   "required": [
    "material_ref",
    "type",
    "code",
    "name",
    "unit",
    "qty"
   ],
   "title": "Consumption",
   "type": "object"
  },
  "CutCell": {
   "additionalProperties": false,
   "properties": {
    "cell": {
     "title": "Cell",
     "type": "integer"
    },
    "x": {
     "title": "X",
     "type": "number"
    },
    "y": {
     "title": "Y",
     "type": "number"
    },
    "w": {
     "title": "W",
     "type": "number"
    },
    "h": {
     "title": "H",
     "type": "number"
    },
    "waste": {
     "default": false,
     "title": "Waste",
     "type": "boolean"
    },
    "part_uid": {
     "anyOf": [
      {
       "type": "integer"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "title": "Part Uid"
    },
    "part_key": {
     "anyOf": [
      {
       "type": "string"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "title": "Part Key"
    },
    "rot": {
     "default": false,
     "title": "Rot",
     "type": "boolean"
    },
    "eW": {
     "anyOf": [
      {
       "items": {
        "anyOf": [
         {
          "type": "string"
         },
         {
          "type": "null"
         }
        ]
       },
       "type": "array"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "title": "Ew"
    },
    "eH": {
     "anyOf": [
      {
       "items": {
        "anyOf": [
         {
          "type": "string"
         },
         {
          "type": "null"
         }
        ]
       },
       "type": "array"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "title": "Eh"
    },
    "business": {
     "anyOf": [
      {
       "type": "boolean"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "title": "Business"
    },
    "remnant_no": {
     "anyOf": [
      {
       "type": "integer"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "title": "Remnant No"
    },
    "angle": {
     "anyOf": [
      {
       "type": "number"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "title": "Angle"
    },
    "outline": {
     "anyOf": [
      {
       "items": {
        "items": {
         "type": "number"
        },
        "type": "array"
       },
       "type": "array"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "title": "Outline"
    }
   },
   "required": [
    "cell",
    "x",
    "y",
    "w",
    "h"
   ],
   "title": "CutCell",
   "type": "object"
  },
  "CutCommand": {
   "additionalProperties": false,
   "properties": {
    "code": {
     "enum": [
      "R",
      "T",
      "C",
      "P",
      "W"
     ],
     "title": "Code",
     "type": "string"
    },
    "level": {
     "title": "Level",
     "type": "integer"
    },
    "size": {
     "title": "Size",
     "type": "number"
    },
    "count": {
     "title": "Count",
     "type": "integer"
    },
    "ref": {
     "default": "",
     "title": "Ref",
     "type": "string"
    }
   },
   "required": [
    "code",
    "level",
    "size",
    "count"
   ],
   "title": "CutCommand",
   "type": "object"
  },
  "CutLine": {
   "additionalProperties": false,
   "properties": {
    "x1": {
     "title": "X1",
     "type": "number"
    },
    "y1": {
     "title": "Y1",
     "type": "number"
    },
    "x2": {
     "title": "X2",
     "type": "number"
    },
    "y2": {
     "title": "Y2",
     "type": "number"
    }
   },
   "required": [
    "x1",
    "y1",
    "x2",
    "y2"
   ],
   "title": "CutLine",
   "type": "object"
  },
  "CutMapMaterial": {
   "additionalProperties": false,
   "properties": {
    "material_ref": {
     "title": "Material Ref",
     "type": "string"
    },
    "kind": {
     "enum": [
      "sheet",
      "linear",
      "nest"
     ],
     "title": "Kind",
     "type": "string"
    },
    "kerf": {
     "default": 0,
     "title": "Kerf",
     "type": "number"
    },
    "sheets": {
     "items": {
      "$ref": "#/$defs/CutSheet"
     },
     "title": "Sheets",
     "type": "array"
    }
   },
   "required": [
    "material_ref",
    "kind"
   ],
   "title": "CutMapMaterial",
   "type": "object"
  },
  "CutSheet": {
   "additionalProperties": false,
   "properties": {
    "no": {
     "title": "No",
     "type": "integer"
    },
    "index": {
     "title": "Index",
     "type": "integer"
    },
    "L": {
     "title": "L",
     "type": "number"
    },
    "W": {
     "title": "W",
     "type": "number"
    },
    "mult": {
     "title": "Mult",
     "type": "integer"
    },
    "is_remnant": {
     "default": false,
     "title": "Is Remnant",
     "type": "boolean"
    },
    "remnant_id": {
     "anyOf": [
      {
       "type": "integer"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "title": "Remnant Id"
    },
    "fill_percent": {
     "default": 0,
     "title": "Fill Percent",
     "type": "number"
    },
    "cut_length_m": {
     "default": 0,
     "title": "Cut Length M",
     "type": "number"
    },
    "cells": {
     "items": {
      "$ref": "#/$defs/CutCell"
     },
     "title": "Cells",
     "type": "array"
    },
    "cuts": {
     "items": {
      "$ref": "#/$defs/CutLine"
     },
     "title": "Cuts",
     "type": "array"
    },
    "commands": {
     "items": {
      "$ref": "#/$defs/CutCommand"
     },
     "title": "Commands",
     "type": "array"
    }
   },
   "required": [
    "no",
    "index",
    "L",
    "W",
    "mult"
   ],
   "title": "CutSheet",
   "type": "object"
  },
  "EdgeBand": {
   "additionalProperties": false,
   "properties": {
    "ref": {
     "title": "Ref",
     "type": "string"
    },
    "code": {
     "title": "Code",
     "type": "string"
    },
    "name": {
     "title": "Name",
     "type": "string"
    },
    "symbol": {
     "title": "Symbol",
     "type": "string"
    },
    "thickness": {
     "title": "Thickness",
     "type": "number"
    },
    "width": {
     "title": "Width",
     "type": "number"
    },
    "work_m": {
     "title": "Work M",
     "type": "number"
    },
    "material_m": {
     "title": "Material M",
     "type": "number"
    },
    "catalog_id": {
     "anyOf": [
      {
       "type": "string"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "title": "Catalog Id"
    }
   },
   "required": [
    "ref",
    "code",
    "name",
    "symbol",
    "thickness",
    "width",
    "work_m",
    "material_m"
   ],
   "title": "EdgeBand",
   "type": "object"
  },
  "MachineRef": {
   "additionalProperties": false,
   "properties": {
    "key": {
     "title": "Key",
     "type": "string"
    },
    "name": {
     "title": "Name",
     "type": "string"
    },
    "label": {
     "title": "Label",
     "type": "string"
    },
    "group": {
     "enum": [
      "saw",
      "cnc"
     ],
     "title": "Group",
     "type": "string"
    },
    "mes_machine_id": {
     "anyOf": [
      {
       "type": "integer"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "title": "Mes Machine Id"
    }
   },
   "required": [
    "key",
    "name",
    "label",
    "group"
   ],
   "title": "MachineRef",
   "type": "object"
  },
  "Machining": {
   "additionalProperties": false,
   "properties": {
    "rule": {
     "default": "MES ishlov oqimi faqat shu paketda postprotsessor fayli kelgan stanok/detal uchun ishga tushadi",
     "title": "Rule",
     "type": "string"
    },
    "saw_ready": {
     "default": false,
     "title": "Saw Ready",
     "type": "boolean"
    },
    "cnc_ready": {
     "default": false,
     "title": "Cnc Ready",
     "type": "boolean"
    },
    "files": {
     "default": 0,
     "title": "Files",
     "type": "integer"
    }
   },
   "title": "Machining",
   "type": "object"
  },
  "Material": {
   "additionalProperties": false,
   "properties": {
    "ref": {
     "title": "Ref",
     "type": "string"
    },
    "kind": {
     "enum": [
      "sheet",
      "linear",
      "nest"
     ],
     "title": "Kind",
     "type": "string"
    },
    "code": {
     "title": "Code",
     "type": "string"
    },
    "name": {
     "title": "Name",
     "type": "string"
    },
    "thickness": {
     "title": "Thickness",
     "type": "number"
    },
    "catalog_id": {
     "anyOf": [
      {
       "type": "string"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "title": "Catalog Id"
    }
   },
   "required": [
    "ref",
    "kind",
    "code",
    "name",
    "thickness"
   ],
   "title": "Material",
   "type": "object"
  },
  "PackageMeta": {
   "additionalProperties": false,
   "properties": {
    "format": {
     "const": "mebelix.kroy.mes-package",
     "default": "mebelix.kroy.mes-package",
     "title": "Format",
     "type": "string"
    },
    "version": {
     "const": 1,
     "default": 1,
     "title": "Version",
     "type": "integer"
    },
    "generated_at": {
     "title": "Generated At",
     "type": "string"
    },
    "generator": {
     "default": "MebeliX Kroy",
     "title": "Generator",
     "type": "string"
    },
    "checksum_algorithm": {
     "const": "sha256",
     "default": "sha256",
     "title": "Checksum Algorithm",
     "type": "string"
    },
    "units": {
     "additionalProperties": {
      "type": "string"
     },
     "title": "Units",
     "type": "object"
    }
   },
   "required": [
    "generated_at"
   ],
   "title": "PackageMeta",
   "type": "object"
  },
  "PackagePart": {
   "additionalProperties": false,
   "properties": {
    "mx_id": {
     "title": "Mx Id",
     "type": "string"
    },
    "mx_uid": {
     "title": "Mx Uid",
     "type": "integer"
    },
    "key": {
     "title": "Key",
     "type": "string"
    },
    "product_code": {
     "title": "Product Code",
     "type": "string"
    },
    "product_mx_id": {
     "anyOf": [
      {
       "type": "string"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "title": "Product Mx Id"
    },
    "code": {
     "title": "Code",
     "type": "string"
    },
    "name": {
     "title": "Name",
     "type": "string"
    },
    "material_ref": {
     "title": "Material Ref",
     "type": "string"
    },
    "length": {
     "title": "Length",
     "type": "number"
    },
    "width": {
     "title": "Width",
     "type": "number"
    },
    "thickness": {
     "title": "Thickness",
     "type": "number"
    },
    "qty_total": {
     "title": "Qty Total",
     "type": "integer"
    },
    "qty_from_stock": {
     "default": 0,
     "title": "Qty From Stock",
     "type": "integer"
    },
    "grain": {
     "default": false,
     "title": "Grain",
     "type": "boolean"
    },
    "edges": {
     "additionalProperties": {
      "$ref": "#/$defs/PartEdge"
     },
     "title": "Edges",
     "type": "object"
    },
    "xnc_refs": {
     "items": {
      "type": "string"
     },
     "title": "Xnc Refs",
     "type": "array"
    },
    "instances": {
     "items": {
      "$ref": "#/$defs/PartInstance"
     },
     "title": "Instances",
     "type": "array"
    }
   },
   "required": [
    "mx_id",
    "mx_uid",
    "key",
    "product_code",
    "code",
    "name",
    "material_ref",
    "length",
    "width",
    "thickness",
    "qty_total"
   ],
   "title": "PackagePart",
   "type": "object"
  },
  "PartEdge": {
   "additionalProperties": false,
   "properties": {
    "ref": {
     "title": "Ref",
     "type": "string"
    },
    "symbol": {
     "title": "Symbol",
     "type": "string"
    },
    "name": {
     "title": "Name",
     "type": "string"
    }
   },
   "required": [
    "ref",
    "symbol",
    "name"
   ],
   "title": "PartEdge",
   "type": "object"
  },
  "PartInstance": {
   "additionalProperties": false,
   "properties": {
    "n": {
     "anyOf": [
      {
       "type": "integer"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "title": "N"
    },
    "qr": {
     "anyOf": [
      {
       "type": "string"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "title": "Qr"
    },
    "pattern_no": {
     "anyOf": [
      {
       "type": "integer"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "title": "Pattern No"
    },
    "cell_index": {
     "anyOf": [
      {
       "type": "integer"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "title": "Cell Index"
    },
    "sheet_copy": {
     "anyOf": [
      {
       "type": "integer"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "title": "Sheet Copy"
    }
   },
   "title": "PartInstance",
   "type": "object"
  },
  "PostprocessorFile": {
   "additionalProperties": false,
   "properties": {
    "format_id": {
     "title": "Format Id",
     "type": "string"
    },
    "machine": {
     "$ref": "#/$defs/MachineRef"
    },
    "source": {
     "enum": [
      "native",
      "template"
     ],
     "title": "Source",
     "type": "string"
    },
    "op_ref": {
     "title": "Op Ref",
     "type": "string"
    },
    "part_keys": {
     "items": {
      "type": "string"
     },
     "title": "Part Keys",
     "type": "array"
    },
    "file_name": {
     "title": "File Name",
     "type": "string"
    },
    "media_type": {
     "title": "Media Type",
     "type": "string"
    },
    "size": {
     "title": "Size",
     "type": "integer"
    },
    "sha256": {
     "title": "Sha256",
     "type": "string"
    },
    "content_base64": {
     "anyOf": [
      {
       "type": "string"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "title": "Content Base64"
    },
    "url": {
     "anyOf": [
      {
       "type": "string"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "title": "Url"
    }
   },
   "required": [
    "format_id",
    "machine",
    "source",
    "op_ref",
    "file_name",
    "media_type",
    "size",
    "sha256"
   ],
   "title": "PostprocessorFile",
   "type": "object"
  },
  "Product": {
   "additionalProperties": false,
   "properties": {
    "mx_id": {
     "title": "Mx Id",
     "type": "string"
    },
    "code": {
     "title": "Code",
     "type": "string"
    },
    "name": {
     "title": "Name",
     "type": "string"
    },
    "qty": {
     "title": "Qty",
     "type": "integer"
    }
   },
   "required": [
    "mx_id",
    "code",
    "name",
    "qty"
   ],
   "title": "Product",
   "type": "object"
  },
  "Remnant": {
   "additionalProperties": false,
   "properties": {
    "id": {
     "anyOf": [
      {
       "type": "string"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "title": "Id"
    },
    "n": {
     "title": "N",
     "type": "integer"
    },
    "material_ref": {
     "title": "Material Ref",
     "type": "string"
    },
    "material_code": {
     "title": "Material Code",
     "type": "string"
    },
    "material_name": {
     "title": "Material Name",
     "type": "string"
    },
    "thickness": {
     "title": "Thickness",
     "type": "number"
    },
    "sheet_no": {
     "title": "Sheet No",
     "type": "integer"
    },
    "sheet_copy": {
     "title": "Sheet Copy",
     "type": "integer"
    },
    "remnant_no": {
     "title": "Remnant No",
     "type": "integer"
    },
    "length": {
     "title": "Length",
     "type": "number"
    },
    "width": {
     "title": "Width",
     "type": "number"
    },
    "raw_length": {
     "title": "Raw Length",
     "type": "number"
    },
    "raw_width": {
     "title": "Raw Width",
     "type": "number"
    },
    "to_warehouse": {
     "default": true,
     "title": "To Warehouse",
     "type": "boolean"
    }
   },
   "required": [
    "n",
    "material_ref",
    "material_code",
    "material_name",
    "thickness",
    "sheet_no",
    "sheet_copy",
    "remnant_no",
    "length",
    "width",
    "raw_length",
    "raw_width"
   ],
   "title": "Remnant",
   "type": "object"
  },
  "SheetUse": {
   "additionalProperties": false,
   "properties": {
    "material_ref": {
     "title": "Material Ref",
     "type": "string"
    },
    "length": {
     "title": "Length",
     "type": "number"
    },
    "width": {
     "title": "Width",
     "type": "number"
    },
    "qty": {
     "title": "Qty",
     "type": "integer"
    },
    "source": {
     "enum": [
      "new",
      "remnant"
     ],
     "title": "Source",
     "type": "string"
    },
    "remnant_id": {
     "anyOf": [
      {
       "type": "integer"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "title": "Remnant Id"
    }
   },
   "required": [
    "material_ref",
    "length",
    "width",
    "qty",
    "source"
   ],
   "title": "SheetUse",
   "type": "object"
  },
  "Source": {
   "additionalProperties": false,
   "properties": {
    "system": {
     "const": "mebelix-kroy",
     "default": "mebelix-kroy",
     "title": "System",
     "type": "string"
    },
    "project_id": {
     "title": "Project Id",
     "type": "string"
    },
    "project_number": {
     "title": "Project Number",
     "type": "integer"
    },
    "project_name": {
     "title": "Project Name",
     "type": "string"
    },
    "customer": {
     "default": "",
     "title": "Customer",
     "type": "string"
    },
    "mes_order_id": {
     "anyOf": [
      {
       "type": "integer"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "title": "Mes Order Id"
    },
    "mes_order_number": {
     "anyOf": [
      {
       "type": "string"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "title": "Mes Order Number"
    },
    "mes_order_ref": {
     "anyOf": [
      {
       "type": "string"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "title": "Mes Order Ref"
    },
    "kind": {
     "enum": [
      "bazis_file",
      "project_file",
      "manual"
     ],
     "title": "Kind",
     "type": "string"
    },
    "order_date": {
     "default": "",
     "title": "Order Date",
     "type": "string"
    },
    "ready_date": {
     "default": "",
     "title": "Ready Date",
     "type": "string"
    },
    "currency": {
     "default": "UZS",
     "title": "Currency",
     "type": "string"
    }
   },
   "required": [
    "project_id",
    "project_number",
    "project_name",
    "kind"
   ],
   "title": "Source",
   "type": "object"
  },
  "XncProgram": {
   "additionalProperties": false,
   "properties": {
    "mx_op_id": {
     "title": "Mx Op Id",
     "type": "string"
    },
    "code": {
     "title": "Code",
     "type": "string"
    },
    "name": {
     "title": "Name",
     "type": "string"
    },
    "qty": {
     "title": "Qty",
     "type": "integer"
    },
    "part_uid": {
     "anyOf": [
      {
       "type": "integer"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "title": "Part Uid"
    },
    "part_key": {
     "anyOf": [
      {
       "type": "string"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "title": "Part Key"
    },
    "stats": {
     "additionalProperties": {
      "type": "number"
     },
     "title": "Stats",
     "type": "object"
    }
   },
   "required": [
    "mx_op_id",
    "code",
    "name",
    "qty"
   ],
   "title": "XncProgram",
   "type": "object"
  }
 },
 "additionalProperties": false,
 "properties": {
  "package": {
   "$ref": "#/$defs/PackageMeta"
  },
  "source": {
   "$ref": "#/$defs/Source"
  },
  "products": {
   "items": {
    "$ref": "#/$defs/Product"
   },
   "title": "Products",
   "type": "array"
  },
  "materials": {
   "items": {
    "$ref": "#/$defs/Material"
   },
   "title": "Materials",
   "type": "array"
  },
  "edge_bands": {
   "items": {
    "$ref": "#/$defs/EdgeBand"
   },
   "title": "Edge Bands",
   "type": "array"
  },
  "parts": {
   "items": {
    "$ref": "#/$defs/PackagePart"
   },
   "title": "Parts",
   "type": "array"
  },
  "sheets": {
   "items": {
    "$ref": "#/$defs/SheetUse"
   },
   "title": "Sheets",
   "type": "array"
  },
  "cut_maps": {
   "items": {
    "$ref": "#/$defs/CutMapMaterial"
   },
   "title": "Cut Maps",
   "type": "array"
  },
  "remnants": {
   "items": {
    "$ref": "#/$defs/Remnant"
   },
   "title": "Remnants",
   "type": "array"
  },
  "consumption": {
   "items": {
    "$ref": "#/$defs/Consumption"
   },
   "title": "Consumption",
   "type": "array"
  },
  "xnc_programs": {
   "items": {
    "$ref": "#/$defs/XncProgram"
   },
   "title": "Xnc Programs",
   "type": "array"
  },
  "postprocessor_files": {
   "items": {
    "$ref": "#/$defs/PostprocessorFile"
   },
   "title": "Postprocessor Files",
   "type": "array"
  },
  "machining": {
   "$ref": "#/$defs/Machining"
  },
  "warnings": {
   "items": {
    "type": "string"
   },
   "title": "Warnings",
   "type": "array"
  }
 },
 "required": [
  "package",
  "source"
 ],
 "title": "MesPackageV1",
 "type": "object"
}
```

</details>

## 7. Avtorizatsiya, «MES» tugmasi va kirish huquqi

### 7.1 Postprotsessorlarga kirish (MX da bajarilgan)
- Ikki qatlam: **ochilgan (litsenziya)** — admin hal qiladi (`GET/PUT /api/postprocessors/access`, saqlanadi
  `settings_profiles.scope = "pp_access"`, umumiy sozlamalar yo'li va zaxira orqali o'zgartirib bo'lmaydi) va
  **yoqilgan/sozlangan** — texnolog («Настройки → Постпроцессоры»: stanokni yoqish, shablon, parametrlar).
- Ishlaydi = ochilgan ∧ (o'rnatilgan generator ∨ (yoqilgan ∧ shablon biriktirilgan)).
- Standart (admin hali saqlamagan): bugun ishlayotganlarning hammasi ochiq (o'rnatilgan ∪ yoqilgan ∪ shablonli).
- Yopiq postprotsessor ro'yxatlarda nomi bilan, kulrang fonda, bosilmaydi («Постпроцессор не подключён — обратитесь
  к администратору»); server uni **403** bilan rad etadi (UI, MCP, API — hammasi): kroy fayli, XNC fayli, «Выделить все»
  zip, MES paketi.
- MebeliX'ning o'z formatlari va stanoksiz korxona shablonlari ham admin tomonidan yopiladi (standart — ochiq; PUT
  `closed_extra`): `mx:csv`, `mx:commands`, `mx:dxf`, `mx:json` (kroy), `mx:xnc_json`, `mx:mes_export`
  (`/projects/{id}/mes-export`, `GET /mes/orders/{ref}`), **`mx:mes_package`** (shu paket — yopiq bo'lsa
  `GET /projects/{id}/mes-package` → 403; `/mes-package/schema` ochiq), `pp:<id>`.

### 7.2 «MES» tugmasi (keyingi bosqich — MES tomoni tayyor bo'lgach)
1. Foydalanuvchi MX da loyihani ochib «MES» ni bosadi.
2. MX paketni quradi (`pp=enabled`, `files=inline`), MES ga yuboradi (2-bo'lim).
3. Muvaffaqiyat — MX brauzerni MES dashboardiga (`redirect_url`) yo'naltiradi; xato — MES matnini ko'rsatadi.

### 7.3 Kirish modeli (taklif — **kelishiladi**)
- Standart: foydalanuvchi **faqat kroy** (MX) ga kira oladi; MES — yopiq, ruxsat berilmaguncha «MES» tugmasi ko'rinmaydi.
- Ruxsatni MX qanday biladi — ikki variant:
  - **A (tavsiya):** MES JWT/sessiya tokeni ichida da'vo: `roles` da `mes` (yoki `mes_user`), yoki alohida
    `"mes": true`. MX tokenni allaqachon tekshiradi (`backend/app/auth.py`, HS256/RS256, `roles`) — tugma faqat shu
    da'vo bo'lsa ko'rinadi. MES baribir o'z tomonida `require_roles` bilan tekshiradi.
  - **B:** MX har sessiyada `GET {MES}/api/v1/users/me` ni foydalanuvchi cookie / tokeni bilan chaqiradi va javobdagi
    `permissions` / `roles` dan `mes` ni qidiradi (MES qisqa muddatli kesh).
- Paketni yuborish — foydalanuvchi nomidan (texnolog roli) yoki MX servis tokeni bilan (`X-Kroy-User` sarlavhasida
  kim yuborgani); qaysi biri — kelishiladi.
- Postprotsessorlarni ochish/yopish — MX admin roli (`admin`); birlashuvda MES `admin` roli bilan almashadi.

## 8. MES jamoasi uchun ochiq savollar

1. Qabul qiluvchi yo'l va tana: `POST /api/v1/orders/{id}/kroy-package` mosmi? Javobda `redirect_url` qaytariladimi?
2. Paket qaysi buyurtma holatida qabul qilinadi (`TECHNICAL_REVIEW` / `PRODUCTION`)? Qayta yuborish qoidasi — `.project`
   qayta yuklash bilan bir xilmi?
3. `mes_order_id` / `mes_order_number` ni MX qayerdan oladi: MES buyurtma yaratilganda MX loyihasini yaratib beradimi
   (MES → MX), yoki texnolog MX da qo'lda kiritadimi?
4. Nusxa QR: MX `qr` ni o'zi quradimi (hozir — ha) yoki MES `key` + `n` dan qayta quradimi? Kirill kodli detal — MX
   ogohlantiradi; MES rad etsinmi yoki MX paketni umuman yubormasinmi?
5. `cells[].cell` / `cell_index` raqamlash: MX avval detallar, keyin qoldiqlar. MES `CutmapCell.cell` bilan mosmi?
   `eW` / `eH` belgilari MES chekidagi tartib bilan bir xilmi (`eW = [chap, o'ng]`, `eH = [tepa, past]`)?
6. `cuts[]` chiziqlari (bo'lak oxiri, propil boshi) va torsovka chiziqlari MES ARRA ekraniga yetarlimi? `dims[]`
   (o'lcham zanjiri) kerakmi?
7. ATX qoldiq ID: raqamlash MX da (material/list tartibi, har jismoniy list alohida) — MES shuni qabul qiladimi?
   Mijoz olib ketadigan qoldiq (`to_warehouse=false`) — `WasteItem` yaratilsinmi?
8. Avtomatik sarf: list sarfi va qoldiq kirimi qachon yoziladi — paket qabul qilinganda yoki ARRA «list tugadi» skanida?
   Qaysi ombor (Mahsulotlar ombori yoki alohida «Qoldiqlar ombori»)?
9. Katalog: `materials[].catalog_id` / `edge_bands[].catalog_id` MES katalog kodi (`M-LD-…`) bo'lishi kerakmi? Mos
   jadvalni kim yuritadi?
10. Stanok bog'lanishi: MX stanok kaliti (`holzma_ptx`, `tpa` …) ↔ MES `machine.id` jadvali qayerda saqlanadi
    (`mes_machine_id`)? Bitta formatda bir nechta stanok bo'lsa?
11. Postprotsessor fayli `OrderFile.kind`: arra va ishlov markazi fayllari uchun yangi turlar kerakmi (`saw`, `cnc`) yoki
    `scx` ga o'xshash? Detal skanida faylni `part_id` bo'yicha topish — `part_keys` yetarlimi?
12. MES o'zining SCX generatsiyasi bilan MX fayllari to'qnashsa qaysi biri ustun?
13. Fayl hajmi chegarasi: inline base64 qancha MB gacha? Kattasi uchun `url` + servis tokeni mosmi?
14. Kirish modeli (7.3): A yoki B variant? Da'vo nomi (`mes`, `mes_user`)? Kim beradi?
15. Xato formati: MES `{"detail": "..."}` — MX shuni foydalanuvchiga ko'rsatadi; maydon bo'yicha xatolar kerakmi?

## 9. Keyingi qadamlar
1. MES jamoasi bilan 8-bo'lim savollari bo'yicha kelishuv; kerak bo'lsa v1 sxemasiga tuzatish (versiya oshmaguncha).
2. MES tomonda qabul qiluvchi: paket → `ParsedProject` + `CutmapModel` + `WasteItem` + `OrderFile`.
3. MX da «MES» tugmasi: yuborish + dashboardga yo'naltirish + kirish huquqi tekshiruvi (7.2–7.3) — MES tayyor bo'lgach.
4. Staging'da sinov: bitta sintetik buyurtma — paket → MES → ARRA terminali xaritasi va cheklar solishtiriladi.
