# C. Listli kroy optimizatori — spetsifikatsiya (CS)

Reference implementatsiya: `backend/app/services/optimizer.py` (testlangan, `tests/test_v2.py`).
Algoritm mustaqil yozilgan; parametrlar ma'nosi GibLab qo'llanmasidagi tavsifga mos.

## C1. Kirish / chiqish

```
optimize(items: list[Item], stock: list[StockSheet], cut: CSCutParams, mat: CSMaterialParams,
         time_budget_s=20) -> CuttingResult
Item(part_id, uid, l, w, can_rotate, members=None, block_axis=None, block_gap=0)
```
* `items` — har bir detal NUSXASI alohida (ОК − МК marta), o'lcham = **пильный** (B2).
* `can_rotate = not (use_grain and part.grain)`.
* `stock` — ombordagi qoldiqlar avval (kichigidan kattasiga), keyin to'liq listlar kiritilgan tartibda.
* Natija: kartalar (`CutMap`), qoldiqlar, buyruqlar, statistika, `unplaced`, `warnings`.

## C2. Gilyotina modeli (rekursiv)

```
daraja 1  C1 : list → POLOSALAR (Y bo'ylab), har biri butun foydali uzunlik bo'ylab
daraja 2  C2/P2 : polosa → USTUNLAR (X bo'ylab); ustun eni = birinchi detal uzunligi
daraja 3  C3/P3 : ustun qoldig'i → QATORLAR (Y bo'ylab)  [«Сложные полосы» ✓ bo'lsa]
daraja 4+ : qator qoldig'i → yana ustunlar …  (max_rotations gacha)
```
Har bo'lak = birinchi detal + uning yonidagi qoldiq soha (keyingi darajada rekursiv to'ldiriladi).
Detal bo'lakni ko'ndalang to'liq egallamasa — ajratish uchun +1 daraja kerak;
agar daraja `max_rotations` dan oshsa, faqat aniq mos detal qo'yiladi.

`first_cut`:
| Qiymat | Xatti-harakat |
|---|---|
| Любое (0) | ikkala yo'nalish sinab ko'riladi, yaxshisi olinadi |
| По длине (1) | faqat polosalar uzunlik bo'ylab (gorizontal birinchi kesishlar) |
| По ширине (2) | faqat en bo'ylab (list 90° burilgan: buyruqlar `R` bilan boshlanadi) |
| По длине/ширине предпочтительно (3/4) | eng yaxshisi olinadi; oxirgi to'liq bo'lmagan list afzal yo'nalishda qayta joylanadi (qoldiq kerakli tomonda qolishi uchun) |

## C3. Cheklovlar

| Parametr | Qoida |
|---|---|
| `kerf` | har kesim orasida propil |
| `trim_*`, `end_offset_*`, `trim_includes_kerf` | foydali zona (B3) |
| `use_grain` | ☐ bo'lsa barcha detallar aylantiriladi |
| `complex_strips` | ☐: ustun ichiga (3-daraja) detal qo'yilmaydi — polosa «bitta detal bilan boshlanadi» |
| `max_rotations` 1..6 | daraja chegarasi; 2 da faqat polosa balandligiga aniq teng detallar; 1 da (W10) faqat birinchi kesim — detal polosani to'liq egallashi shart |
| `min_trim_cut` | kesimdan keyin qoladigan chiqindi tilimi 0 yoki ≥ min_trim bo'lishi kerak (ichki: qoldiq ≥ propil+min; list chetida: qoldiq + otstup ≥ propil+min). 0 — o'chiq |
| `min_strip_width` | polosa balandligi kamida shuncha (stanok qisqichlari uchun) |
| `max_strip_width` | polosa balandligi ko'pi bilan shuncha (0 — cheksiz) |
| `max_strip_length` | polosa uzunligi stanokka sig'masa — birinchi kesish yo'nalishi almashtiriladi; ikkalasi ham sig'masa ogohlantirish |
| `max_part_types_per_map` | kartadagi turli detallar soni (0 — cheksiz) |
| `min_part_size` (material) | tomoni kichik detallar kroyga kirmaydi + ogohlantirish |
| `strip_sort`, `in_strip_sort` | kroydan keyin polosalar/ustunlar tartibi: kamayish, o'sish, «torlar o'rtaga» (kattalar chetlarga — materialdagi kuchlanish kamayadi), saralamaslik |
| `prefer_big_pack` | bir xil kartani ko'proq takrorlaydigan variant afzal |
| `multiplicity` | paket = ⌈C / karralik⌉ |
| guruh (blok) | detal `group_by` (uzunlik/en), `group_min..group_max` dona bitta blok bo'lib joylanadi, a'zolar orasida `kerf_group` (bo'lmasa kerf); kartada a'zolar alohida ko'rsatiladi (`Placement.block`) |

## C4. Evristika (reference)

1. Har list turi uchun, list tugaguncha:
   * 15 variant (3 rejim × 5 saralash) sinaladi: rejim `fill` (polosa to'lishi %), `area`
     (polosadagi maydon), `ffd` (eng katta detal balandligi); saralash: maydon, katta tomon, en, uzunlik, perimetr.
   * Polosa nomzodlari — birinchi 16 detalning balandliklari (hech biri bo'lmasa — hammasi).
   * **Oldindan ko'rish**: eng yaxshi 4 nomzodning har biri bilan list oxirigacha to'ldirib, eng ko'p
     maydon joylaydigani tanlanadi (≤120 detal va vaqt byudjetining 40% igacha).
   * Ichki sohalar ochko'z: aniq mos (ko'ndalang to'liq) detal birinchi, keyin eng balandi, keyin maydoni.
2. Tanlangan list sxemasi qolgan detallar yetguncha **takrorlanadi** (`copies`), ombordagi list soni chegarasida.
3. Ikkala yo'nalish (ruxsat etilganlari) solishtiriladi: kirmay qolganlar → listlar soni → ishlatilgan maydon → oxirgi listda kamroq detal (katta qoldiq).
4. Saralash qoidalari qo'llanadi, qoldiqlar tasniflanadi, buyruqlar jadvali tuziladi.

Benchmark (xodimlar loyihasi «Detskiy kravat», 19 detal, 2750×1830, propil 3, torsovka 2, min kesish 5):
**2 list, 1-list 92.83 %** (GibLab: 2 list, 93.87 %). 573 detal ≈ 13 s (Python).
Yaxshilash mumkin (masalan, chuqurroq qidiruv/Rust modul) — lekin testlar yashil qolsin va benchmark yomonlashmasin.

## C5. Buyruqlar jadvali (tartib)

```
[R0 90]                    — list burilgan bo'lsa
T1 <yuqori torsovka>
C1 <polosa balandligi>     — har polosa uchun
  T2 <chap torsovka>       — har polosada
  P2 <ustun eni> ref       — ustun = bitta aniq detal
  C2 <ustun eni>           — ustun ichida bir nechta detal
    P3 <detal balandligi> ref
    W3 <qoldiq>
  W2 <polosa oxiri qoldig'i> [ref qoldiq №]
W1 <list oxiri qoldig'i> [ref qoldiq №]
```
Ketma-ket bir xil `C`/`P` buyruqlari birlashtiriladi (`К` = soni). Blok ichidagi ajratish — keyingi darajadagi `P` (ref = a'zolar).

## C6. Statistika

Karta: `parts_count`, `cut_length_m` (1 list), `cuts_count`, `fill_percent`, `waste_percent`
(delovoy qoldiqsiz), `parts_area_m2`, `sheet_area_m2`, `offcut_area_m2`, `copies`, `packs`.
LT/CT qoidasi (onlayn tizim bilan bir xil, `X_1015_ONLAYN_AUDIT_MCP.md` §12): buyruqlar jadvalining har qatori (T, C, P; K marta) —
bitta arra yurishi, uzunligi — kesilayotgan bo'lakning ko'ndalang o'lchami (1-daraja — list tomoni to'liq, 2-daraja — polosa eni,
3-daraja — bo'lak o'lchami …); propil qo'shilmaydi, har stackda oxirgi kesim ham sanaladi; o'rtadagi chiqindi (W dan keyin bo'lak) — kesim.
Jami: listlar, paketlar, detallar, kesish uzunligi/soni (× copies), `material_qty_m2`
(= material − delovoy), `business_area_m2`, `waste_area_m2`, `total_fill_percent`.

## C7. «До кроить» (qolganini kroy qilish)

`POST .../optimize?mode=remaining`: faqat `left_qty > 0` detallar, qolgan list soni bilan;
yangi kartalar oxiriga qo'shiladi, mavjud kartalar va raqamlar **o'zgarmaydi**; qoldiq raqamlari davom etadi.

## C8. Qo'lda tahrir (Редактирование раскроя) — frontend talablari

Oyna: chapda detallar ro'yxati (Товар, Длина, Ширина, Кол-во, Исп., Остаток, Наименование), o'ngda
kartalar miniatyurasi + katta karta; «Горизонтальный интерфейс» almashtirgich; Ок/Отмена.
Harakatlar: Отменить Ctrl+Z, Вернуть Ctrl+Y, karta qo'shish/o'chirish, Торцовка, boshiga Ctrl+←,
oxiriga Ctrl+→, klon Ctrl+C, rezlarni aylantirish Ctrl+R, polosani kengaytirish Ctrl+Q, o'chirish Del,
nol qoldiqlilarni filtr Ctrl+F, ↑↓.
Sichqoncha: **Shift** — tahrir rejimi; chap tugma — detalni qo'yish; **Alt/Ctrl** — detalni burish;
o'ng tugma — detal/polosani o'chirish. Guruhlangan (blok) detallar blok sifatida qo'yiladi.
Saqlashda backend `PUT .../result` ga to'liq natija yuboriladi; frontend gilyotina to'g'riligini tekshiradi
(ustma-ust tushmaslik, list ichida, propil).
Kartada: sichqoncha g'ildiragi — masshtab; detalni bosish — shu detalning barcha nusxalari
to'qroq rangda; ikki marta bosish — detal xossalari oynasi.
