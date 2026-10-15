# «G CODE» (umumiy) postprotsessori — ishlov markazi

Holat: **yuz teshiklari + freza konturi**. Onlayn parallel sinov namunalari (bitta loyiha, 36 dastur) bilan **36/36 fayl
bayt-ma-bayt bir xil** (1-qatordagi dastur nomi izohi tenglashtirilgach). Qirra teshiklari bu formatga **chiqmaydi**
(namunada ham yo'q); paz namunada yo'q — xato beriladi.

Generator: `backend/app/services/ppfmt/gcode_generic.py` (kalit `gcode`). Tekshiruv:
`tools/bench/pp_online_check_mw_gcode_aes.py`; testlar: `backend/tests/test_ppfmt_mw_gcode_aes.py`.
Manba namunalar: `post prtsessorlar/ONLINE_2026-10-04/yangi_formatlar/gcode.zip` (repoga kirmaydi).
Internet tadqiqoti (`WEB_missing_formats.md` 12-bo'lim): «G CODE» nomli umumiy standart yo'q — bu soddalashtirilgan ISO
dastur, aniq stanokka moslash kerak.

## 1. Fayl

| Xususiyat | Qiymat |
|---|---|
| Nomi | `<XNC kodi>` — **kengaytmasiz**; bir xil kodlar — `kod(1)`, `kod(2)` (probelsiz) |
| Bitta faylda | bitta XNC operatsiyasi |
| Kodlash / qator oxiri | ASCII, `CRLF`; oxirgi qatordan (`M30`) keyin qator ko'chirish **yo'q** |
| Qator raqami | har qator `N10`, `N20`, … (10 qadam) |
| Sonlar | ortiqcha nollarsiz, 4 kasrgacha |

## 2. Tuzilish

```
N10 (generated code in MebeliX Kroy)
N20 G90
N30 G80                      ← faqat oldingi fayl parmalash bilan tugagan bo'lsa (3-bo'lim)
N40 (8MM Bore8)              ← guruh: (<diametr>MM <XNC asbob nomi>)
N50 M06                      ← asbob almashtirish — RAQAMSIZ
N60 S3000 M04
N70 X108 Y102 Z-10           ← teshik: X, Y, Z = −chuqurlik (har doim uchala so'z)
…
N190 G80                     ← keyingi guruh bo'lsa
N200 M05
N210 (10MM Bore10) …
N370 M05
N380 M30
```

Guruh — dastur tartibida ketma-ket kelgan, asbob nomi va diametri bir xil yuz amallari (asbob almashsa — yangi guruh,
keyin yana o'sha asbob kelsa — yana yangi guruh). Qirra teshiklari tashlab yuboriladi (guruhni bo'lmaydi). Yuz amali
bo'lmasa: `N10 …`, `N20 G90`, `N30 M30`.

Freza konturi (guruh ichida):

```
G0 X<x0> Y<y0> Z20
G0 G41 X<x0> Y<y0>           ← C=1 → G41; C=2 → G42; C=0 → G40 (faraz)
Z-<chuqurlik> F100
G3 X… Y… I… J… [Z-…]         ← yoy: XNC dir="true" → G3, "false" → G2; I, J — yoy boshidan markazgacha (nisbiy)
G1 Y147.3135                 ← chiziq; o'zgarmagan X / Y yozilmaydi
G0 Z20
```

Koordinatalar XNC dagidek (Y pastga); orqa tomon dasturi X bo'yicha ag'dariladi (yoy yo'nalishi va korreksiya teskari).

## 3. Paket holati (fayllar orasida saqlanadi)

Namunalardan aniqlangan ikki xususiyat — loyihaning barcha dasturlari bitta paketda chiqarilganda takrorlanadi
(`gcode_batch`, `State`); yakka dastur chiqarilganda holat toza:

1. **`G80`** (parmalash siklini bekor qilish) teshiklar guruhidan keyin darhol emas, balki *keyingi guruh oldidan*
   (`M05` dan oldin) yoki *keyingi fayl boshida* (`G90` dan keyin) yoziladi. Shuning uchun bir xil ikki dasturning
   birinchisida `N30 G80` yo'q, ikkinchisida bor.
2. Freza qatorlarida **`Z`** so'zi faqat oxirgi yozilgan qiymatdan farq qilsa chiqadi; bu qiymat ham fayllar orasida
   saqlanadi (birinchi frezali faylda birinchi yoyda `Z-16` bor, keyingilarida yo'q). Xavfsiz: chuqurlikka kirish
   (`Z-… F100`) har konturda alohida yoziladi.

X / Y so'zlarini tashlash holati esa har kontur boshidagi `G0` nuqtasidan boshlanadi (haqiqiy asbob o'rni).

## 4. Asbob raqamlari

Ishlatilmaydi: `M06` raqamsiz, guruh izohida diametr va XNC asbob nomi (`Bore8`, `BoreTh8`, `Mill8`). «Инструменты»
jadvali bu formatga ta'sir qilmaydi.

## 5. Ochiq savollar

1. Qaysi stanok / kontroller uchun: `M06` raqamsiz, `S3000`, `F100`, xavfsiz `Z20` — o'zgarmaslar; sozlanadigan bo'lishi kerakmi.
2. `G80` va `Z` ning fayllar orasidagi holati — namunaviy tizimning xususiyati; stanok uchun har faylda mustaqil bo'lgani
   to'g'riroq bo'lishi mumkin (hozir paketda namunadagi kabi).
3. C=0 (`G40`) va C=2 (`G42`) konturlar, bir guruhda bir nechta kontur, teshik + freza aralash guruh — namunada yo'q, faraz.
4. Qirra teshiklari umuman chiqmaydi — stanok faqat vertikal ishlov qiladimi?
5. Paz (`Groove`) — namuna kerak. Kontur oxirida `G40` yozilmaydi (namunadagi kabi).
