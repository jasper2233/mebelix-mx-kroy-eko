# AESS Alpha (SS) — `.ss` kesish fayli

> Manba: `post prtsessorlar/PILNIY APPARAT/AESS Alpha (SS)/<buyurtma>/*.ss` — 21 fayl, 10 papka.
> **Format to'liq ta'rifi — [`aes-alpha.md`](aes-alpha.md)** (yozuvlar, maydonlar, kesim daraxti). Bu hujjat AESS
> namunalarini, ularga xos holatlarni va alohida tekshiruvni beradi. Mijoz ismlari «mijoz» bilan almashtirilgan.

## 0. Xulosa: AES Alpha bilan farqi

* Papka nomlaridagi `2027 … 2037` — **yil emas, buyurtma raqami** (fayl nomlari ham `2027_mijoz_…` bilan boshlanadi;
  loyihalar `giblab project/2 shogirt/2027 mijoz/…`). 2035 buyurtmasi yo'q.
* 33 ta faylda (12 AES + 21 AESS) barcha doimiy maydonlar (`BSL3`, `KON1..3`, `LMT1 f2`, `ASP*`, `OZL1 f1/f3/f6..f9`,
  `OZL3`, `URN1 f5/f6`, `PRT1 f5/f6/f12`, `PRT2 f1/f2`, `PRT4 f5/f6`, `PRT5`, `PNL1 f4`, `PNL2..PNL5`) **bir xil**.
  Yozuvlar tartibi, kengliklar, `-0.50` qoidasi, `S/L` ma'nosi ham bir xil. Demak bu **bitta postprotsessor**
  (versiya `From GibLab,1.0`); farq faqat qaysi buyurtmalar va qaysi vaqtda eksport qilinganida
  (AES — hammasi `16:48`; AESS — `17:38 … 17:45`, 27.09.2026).
* AESS da ikkinchi materiallar ham bor (XDF 3 mm, akril 18 mm, qoldiq listlar), AES da faqat asosiy LDSP/LMDF.

## 1. Ishlab chiqarilgan fayllar

Har buyurtma papkasida har bir material (CS operatsiyasi) uchun bitta `.ss`. Nom: `<loyiha nomi _ bilan>_<material>.ss`
(sanitizatsiya — `aes-alpha.md` §1). ASCII, `CRLF`, nuqta o'nlik, `%9.2f`.

| Papka | Material (fayl qismi) | t | Listlar (OZL1: soni × W×L) | URN qatori | Σ dona | Noyob karta | Σ list | S/L | Max daraja | Kromkali qator |
|---|---|---|---|---|---|---|---|---|---|---|
| 2027 | LDSP_UD_ | 16 | 8 × 1830×2750 | 53 | 73 | 8 | 8 | L,S | 4 | 36 |
| 2027 | XDF_2800x2070_mm_5.8_kv | 3 | 2 × 2070×2800 | 3 | 4 | 2 | 2 | S | 2 | 0 |
| 2028 | LDSP_OQ_GLYANETS | 16 | 3 × 1830×2750 | 5 | 23 | 3 | 3 | L,S | 3 | 2 |
| 2029 | LDSP_METALIK_SHAGREN | 16 | 1 × 1830×2750 | 15 | 16 | 1 | 1 | S | 3 | 15 |
| 2029 | Ldsp_oq | 16 | **1 × 1160×2750 (qoldiq) + 0 × 1830×2750** | 16 | 23 | 1 | 1 | S | 3 | 16 |
| 2030 | LDSP_BELI_KARONA_GLYANETS | 16 | 5 × 1830×2750 | 20 | 34 | 5 | 5 | L,S | 4 | 20 |
| 2030 | LMDF_BELI_KARONA_GLYANETS | 16 | 3 × 1830×2750 | 19 | 35 | 3 | 3 | L,S | 4 | 0 |
| 2031 | LDSP_DUB_VATAN_TEKSTURA | 16 | 3 × 1830×2750 | 27 | 47 | 3 | 3 | L,S | 4 | 25 |
| 2031 | XDF_2800x2070_mm_5.8_kv | 3 | 1 × 2070×2800 | 4 | 8 | 1 | 1 | S | 3 | 0 |
| 2032 | LMDF_DUB_VATAN_TEKSTURA | 16 | 18 × 1830×2750 | 154 | 249 | 16 | 18 | L,S | 4 | 114 |
| 2032 | LMDF_KASHMIR_SHAGREN | 16 | 6 × 1830×2750 | 17 | 37 | 3 | 6 | L,S | 3 | 17 |
| 2032 | XDF_2800x2070_mm_5.8_kv | 3 | 6 × 2070×2800 | 7 | 9 | 5 | 6 | L,S | 3 | 0 |
| 2033 | LDSP_ASTANA_TEKSTURA | 16 | 5 × 1830×2750 | 32 | 36 | 5 | 5 | L,S | 4 | 29 |
| 2033 | XDF_2800x2070_mm_5.8_kv | 3 | 2 × 2070×2800 | 3 | 3 | 2 | 2 | L | 2 | 0 |
| 2034 | LDSP_KASHMIR_SHAGREN | 16 | 5 × 1830×2750 | 61 | 67 | 5 | 5 | L,S | 4 | 54 |
| 2034 | XDF_2800x2070_mm_5.8_kv | 3 | 2 × 2070×2800 | 4 | 4 | 2 | 2 | S | 3 | 0 |
| 2036 | AKRIL_KASHMIR | 18 | 1 × 1220×2440 | 10 | 12 | 1 | 1 | S | 4 | 6 |
| 2036 | LDSP_KASHMIR_SHAGREN | 16 | 2 × 1830×2750 | 27 | 35 | 2 | 2 | L,S | 4 | 27 |
| 2036 | XDF_2800x2070_mm_5.8_kv | 3 | 1 × 2070×2800 | 5 | 7 | 1 | 1 | S | 3 | 0 |
| 2037 | LDSP_OQ_GLYANETS | 16 | 5 × 1830×2750 | 29 | 44 | 5 | 5 | L,S | 4 | 20 |
| 2037 | XDF_2800x2070_mm_5.8_kv | 3 | 2 × 2070×2800 | 3 | 5 | 2 | 2 | S | 2 | 0 |

Har bir faylda: `Σ URN1 soni = Σ (karta ichidagi detal KES1 × PNL1 f3)` va `Σ PNL1 f3 = Σ OZL1 f2` — 21/21.

Boshqa papkalar bilan to'plam farqi (eslatma): 2030 uchun XDF `.ss` yo'q (FastPanel da bor); 2032 XDF `.ss` bor,
lekin Nanxing `.CUT` yo'q. Boshqa barcha AESS fayllarining `.CUT` jufti mavjud.

## 2. Tuzilma

`aes-alpha.md` §2 bilan bir xil. AESS ga xos kuzatuvlar:
* `LMT1 f1` / `PRT2 f3` materialga qarab o'zgaradi: 16.00 (LDSP/LMDF), 3.00 (XDF), 18.00 (akril) = `sheet/@t`.
* `OZL1 f4/f5` = list `w`/`l`: 1830/2750, XDF 2070/2800, akril 1220/2440, qoldiq 1160/2750.
* Bir CS da ikki list yozuvi bo'lsa — ikki `OZL` blok (2029 `Ldsp oq`: qoldiq `usedCount=1` → `OZL1 f2=1`;
  butun list `count=1000 usedCount=0` → `OZL1 f2=0`, lekin baribir yoziladi).
* `PRT1 f10` (mahsulot kodi) bo'sh bo'lishi mumkin: 2028 da `PRT1,...,,spalniy matrasli,` (mahsulotda `code` yo'q).
* Bitta faylda bir necha mahsulot: 2030 da `203001|01 Shkaf` va `203002|02 Servant`; 2032 da `203201|01 spalniy`
  va `303001|01 shkaf` (ikkinchisi diskdagi 2032 loyihalarida yo'q — boshqa loyiha birlashtirilgan).

## 3. Kesish rejasi

`aes-alpha.md` §3 qoidalari AESS da ham istisnosiz bajariladi:
* `-0.50` faqat 03/04-daraja guruhlari boshida (AES+AESS jami 465 + 158 holat).
* Chiqindi/qoldiq yozilmaydi; detalning ikkinchi o'lchami hamisha ota-bo'lakka teng.
* AutoCUT `.CUT` bilan geometrik solishtirish: AESS ning 20 ta juftli faylida detallar koordinatalari (Px, Py, X, Y, Count)
  **20/20 aynan mos**; 01-daraja polosalar va `S/L` ham 20/20.

`L` yo'nalish namunasi (2033 XDF, list 2800×2070):
```
PNL1,01,L,1,0
BASLA
KES1,01,  1069.00,0,000     polosa Y=1069, to'liq uzunlik 2800  (CUT: Part Px=0 Py=5 X=2800 Y=1069)
KES1,02,  2499.00,1,001       detal #1 2499×1069                 (CUT: Px=5 Py=5 X=2499 Y=1069)
KES1,01,   549.00,0,000     polosa Y=549                         (CUT: Py=1077 = 5+1069+3)
KES1,02,  1069.00,1,003       detal #3 549×1069, burilgan          (CUT: Angle=90 X=1069 Y=549)
```
Qoldiq listdagi `S` karta (2029 `Ldsp oq`, list 2750×1160):
```
KES1,01,   704.00,0,000      polosa X=704, to'liq Y=1160
KES1,02,   500.00,1,004        detal 704×500
KES1,02,   500.00,1,003        detal 704×500
KES1,02,   100.00,0,000        bo'lak Y=100
KES1,03,    -0.50,0,000          03-daraja markeri
KES1,03,   310.00,1,011          detal 310×100
KES1,03,   310.00,1,011          yana
```
Tekshiruv: 500+500+100 + 3·3 = 1109 ≤ 1160 − 4 − 3.

## 4. Loyiha → maydonlar (AESS namunalarida tekshiruv)

Xarita `aes-alpha.md` §4 dagi bilan bir xil. Natijalar:

1. **2033 XDF** (`2033_mijoz.project`, CS «XDF 2800x2070 mm  5.8 kv», t=3): 3 qator — `01_008 XDF ort` 2499×1069 ×1,
   `02_008 XDF ort` 2499×1069 ×1, `04_005 XDF ort` 549×1069 ×1, kromkasiz, `txt=false` →
   `URN1,    1,    1,  2499.00,  1069.00, ,N` …; PRT3 hammasi bo'sh, PRT4 `0.00`×4; `LMT1,     3.00,    40.00`;
   `OZL1 f2=2` (= 2 karta × 1).
2. **2027 LDSP UD** (`2027 mijoz.project`, 53 qator, 73 dona — teng): `01.001 tom` `l=dl=2132 w=dw=480`
   (`jl=2130 jw=479` — ishlatilmaydi), kromka `b,l,r` → `PRT3` pozitsiyalari chap/o'ng/past to'la, yuqori bo'sh;
   `PRT4 1.00, 0.00, 1.00, 1.00`. `01.020 tr` (faqat `r`) → faqat 3-pozitsiya (o'ng).
   Material `OZL2,LDSP UD ` — oxirida bo'shliq bilan (diskdagi loyihada nom `LDSP UD (110197)_diffuseOriginal`;
   eksport boshqa nusxadan qilingan — AutoCUT va FastPanel fayllarida ham `LDSP UD `).
   Kromka nomi `.ss` da `1-19 dub votan`, diskdagi bu loyihada esa `kromka PVC 1-19 dub votan` — ya'ni eksport qilingan
   loyiha nusxasida lenta qayta nomlangan bo'lgan; postprotsessor nomni o'zgartirmaydi (3179/3180 da `_` li nusxa bilan aynan mos).
3. **2029 Ldsp oq** (`2029_mijoz.project`): CS da list yozuvlari `l=2750 w=1160 count=1 usedCount=1` va
   `l=2750 w=1830 count=1000 usedCount=0` → ikki `OZL` blok `1` va `0`; 16 qator, 23 dona — teng;
   `01_006 pb-pl` 768×80, kromka `b` (`1-19 metlik`) → PRT3 4-pozitsiya, PRT4 `0,0,0,1`.
4. **2034, 2036, 2037** — nomlar 100 %, soni 100 % mos (61/61, 27/27+10/10+5/5, 29/29+3/3).
5. Qisman: 2032 (mahsulot `303001` diskda yo'q), 2030 LMDF (detallar `01 Shkaf.project` / `02 Servant.project` da,
   `l` atributi yo'q → `dl/dw` bilan mos), 2028 (`2028_mijoz.project` da 5/5).

## 5. Minimal namuna

`aes-alpha.md` §5 dagi namuna aynan shu papkadagi 2027 XDF faylidan olingan (anonimlashtirilgan) — u AESS uchun ham
yaroqli. Qoldiq list bilan minimal variant uchun `OZL` bloklarini quyidagicha yozing (karta `PNL1,01,...` qoldiqni oladi):
```
OZL1,*****,    1,   9.860,  1160.00,  2750.00,     2.00,     2.00,     2.00,     2.00
OZL2,Ldsp oq
OZL3,1                ,     2.00,     2.00
OZL1,*****,    0,   9.860,  1830.00,  2750.00,     2.00,     2.00,     2.00,     2.00
OZL2,Ldsp oq
OZL3,1                ,     2.00,     2.00
```

## 6. Savollar (AESS ga xos; umumiy savollar — `aes-alpha.md` §6)

* **Q-A1.** «AES Alpha» va «AESS Alpha (SS)» — bitta stanokmi (ikki nom bilan saqlangan postprotsessor) yoki ikki xil
  stanok? Fayllar bir xil formatda; agar stanoklar har xil bo'lsa, qaysi sozlamalar (kerf, torsovka, paket) farq qiladi?
* **Q-A2.** Ishlatilmagan list (`OZL1 f2 = 0`) ham yozilishi shartmi yoki faqat GibLab odati?
* **Q-A3.** Qoldiq listni stanok qanday taniydi — faqat o'lchamidanmi? (`OZL1 f1 = *****`, `OZL3 f1 = 1` qoldiqda ham o'zgarmaydi.)
* **Q-A4.** Bir faylda bir nechta loyiha/mahsulot (2032: `203201` + `303001`) — bu ataylab birlashtirilganmi?
  MebeliX bir faylga bir necha buyurtmani birlashtirishi kerakmi?
* **Q-A5.** 2030 XDF uchun `.ss` nega yo'q (FastPanel da bor), 2032 XDF uchun esa `.CUT` yo'q?
