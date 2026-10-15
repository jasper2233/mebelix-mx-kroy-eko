# Nanxing NXCutSAW — `.CUT` (AutoCUT XML), tekis papka

> Manba: `post prtsessorlar\PILNIY APPARAT\Nanxing NXCutSAW\*.CUT` (14 fayl, buyurtmalar 3167–3182).
> **Format to'liq bir xil** — `Nanxing (NXCutSaw)` bilan: barcha element/atribut ta'riflari, qoidalar, generator
> algoritmi va savollar [nanxing-nxcutsaw.md](nanxing-nxcutsaw.md) da. Bu hujjat — shu papkaning o'ziga xos
> jihatlari va alohida tekshiruvi. Mijoz ismlari «mijoz» bilan almashtirilgan.

**Tushunish darajasi: to'liq.** 14 faylning hammasi avtomatik tekshiruvdan xatosiz o'tdi.

---

## 1. Fayllar

| Xususiyat | Qiymat |
|---|---|
| Kengaytma / format | `.CUT`, XML `AutoCUT ver="500"` |
| Kodirovka, qator | UTF-8 BOM'siz, bitta qator, oxirida `\n` yo'q |
| O'nlik | nuqta, faqat `F4`/`F5` (`1400.00`) |
| Papka | **tekis** — buyurtma bo'yicha pastki papka yo'q |
| Nomi | `<buyurtma>_<mijoz>_<material>.CUT` (bo'sh joy/qavslar → `_`), masalan `3181_mijoz_LDSP_UD_110197__diffuseOriginal.CUT` |
| Har buyurtmaga | **faqat bitta fayl** — loyihadagi **birinchi** CS operatsiyasi (asosiy LDSP/LMDF material) |

`Nanxing (NXCutSaw)` dan farqi faqat tashkiliy: u yerda har buyurtma o'z papkasida va bir nechta material
(XDF, AKRIL …) fayllari bor; bu yerda esa bitta material. Masalan 3178 loyihasida 5 ta CS operatsiyasi
(`LDSP LIZA BEJIVIY`, `LDSP OQ TEKSTURA`, `LDSP KASHMIR SHAGREN`, `LDSP UD`, `XDF …`) bor, fayl esa faqat
birinchisi uchun; 3167, 3168, 3169 … loyihalaridagi XDF uchun fayl yo'q. Barcha 14 holatda eksport qilingan
material = loyihadagi birinchi CS. Fayllar bitta seansda yaratilgan (`Update` 27.09.2026 16:45–16:47).
3172, 3176 raqamli buyurtmalar umuman yo'q.

| Buyurtma | Material | Layout | Listlar | `Objective` qatorlari | Detal soni | Qoldiq (`Spares`) | Chuqurlik | `Condition` |
|---|---|---|---|---|---|---|---|---|
| 3167 | LDSP KASHMIR SHAGREN | 11 | 13 | 82 | 117 | 0 | 6 | 3 (2 qoldiq list + 11 butun) |
| 3168 | LDSP KASHMIR SHAGREN | 8 | 9 | 67 | 90 | 1 | 4 | 1 |
| 3169 | LDSP METALIK SHAGREN 5.03 kv | 4 | 4 | 82 | 104 | 0 | 4 | 1 |
| 3170 | LDSP KASHMIR SHAGREN | 2 | 2 | 32 | 40 | 0 | 4 | 1 |
| 3171 | LDSP DUB VATAN TEKSTURA | 2 | 4 | 6 | 28 | 0 | 4 | 1 |
| 3173 | LDSP KASHMIR SHAGREN | 9 | 10 | 53 | 77 | 1 | 4 | 1 |
| 3174 | LDSP KASHMIR SHAGREN | 10 | 11 | 70 | 112 | 0 | 4 | 2 (2750×450 ×1 + 2750×1830 ×10) |
| 3175 | LDSP KASHMIR SHAGREN | 3 | 4 | 14 | 32 | 1 | 4 | 1 |
| 3177 | LDSP KAPUCHINO | 4 | 4 | 74 | 87 | 1 | 4 | 1 |
| 3178 | LDSP LIZA BEJIVIY | 3 | 3 | 15 | 30 | 0 | 4 | 1 |
| 3179 | LMDF OQ GLYANETS | 6 | 6 | 84 | 104 | 1 | 4 | 1 |
| 3180 | LDSP DUB VATAN TEKSTURA | 5 | 5 | 51 | 69 | 0 | 4 | 1 |
| 3181 | LDSP UD (110197)_diffuseOriginal | 5 | 5 | 37 | 69 | 1 | 6 | 5 (hammasi `Count=1`) |
| 3182 | LDSP KASHMIR SHAGREN | 8 | 9 | 82 | 117 | 0 | 4 | 1 |

Chuqurlik `swMaxturns` ga mos: 3167 va 3181 da asbob `swMaxturns=6` → 6 daraja; qolganlarida ≤ 4.

## 2. Tuzilma

[nanxing-nxcutsaw.md §2](nanxing-nxcutsaw.md#2-toliq-tuzilma) bilan aynan bir xil. Bu papkada barcha 14 faylda
konstantalar: `ver=500`, `Memo=""`, `Sx=Sy=5`, `Flag=True`, `SolveGap=3`, `NestGap=3`, `CutCount=0`,
`Spares/Shape Turn=False`; `Data.Type` hech birida yo'q (LDSP/LMDF materiallarida `code` bo'sh).
`Ply` = 16 hamma faylda.

## 3. Kesish rejasi

Bir xil: `Layout` (karta, `Count` = bir xil listlar soni), `Cut` (1-kesim yo'nalishi), `Part` daraxti
(gilyotina, yo'nalish almashadi, kerf 3, boshlang'ich torsovka 5), `Grouped`, `Angle="90"`, `Spare`.
Bu papkada `Grouped` naqshlari ham shu qoidaga bo'ysunadi (N ta bir xil ketma-ket qo'shnining oxirgisi).

## 4. Loyiha → fayl tekshiruvi (4 namuna)

Moslash GibLab'da saqlangan `<buyurtma>_mijoz.project` bo'yicha (CS operatsiyasining `part` tartibi).

### 4.1 Buyurtma 3171 — eng kichik, to'liq qo'lda tekshirildi

| Loyiha (`name`, `dl×dw`, `count`, `txt`, kromka) | `Objective` |
|---|---|
| `01_001 oldi bok` 1400×1750, 2, **true**, 4 tomon `(A) 1-19 dub votan` | `Д1 X=1400 Y=1750 Count=2 Turn=false F8=F9=F10=F11="(A) 1-19 dub votan"` |
| `01_002 tom` 1718×584, 2, false, elt | `Д2 Turn=true F8="(A) …"` |
| `01_003 bok` 1400×584, 4, false, elt+ell+elr | `Д3 F8, F10, F11` |
| `01_004 bok` 900×584, 4, false, elt+ell | `Д4 F8, F10` |
| `01_005 pol` 590×583, 6, false, elt | `Д5 F8` |
| `01_006 pol` 548×583, 10, false, elt | `Д6 F8` |

Kartalar: `Layout ID=0 Count=2` — UID 0,1,4,5,5 (5 dona × 2 = 10); `Layout ID=1 Count=2` — UID 3,3,4,2,4,2,5,5,5
(9 × 2 = 18). Jami 28 = loyihadagi 2+2+4+4+6+10 ✓. UID bo'yicha: UID4 = (1+2)×2 = 6 ✓, UID5 = (2+3)×2 = 10 ✓.
Geometriya: `Px=5 X=1400` → keyingi `Px=1408` (5+1400+3) ✓; `Д2` `Angle="90"` bilan 584×1718 ✓;
1-karta 3-polosasida uchta UID5 — oxirgisida `Grouped="3"` ✓.
Faqat `txt=true` bo'lgan `01_001` da `Turn=false` va u aylantirilmagan ✓.

### 4.2 Buyurtma 3175 — qoldiq, `Cut="false"`, XNC kodlari

- 14 qator, jami 32 dona, 3 karta (`Count` 2+1+1 = 4 list). UID6 (`01_009 goli`, 4 dona) 1-kartada 2 marta × 2 ✓;
  UID12 (`01_013 pl` 1090×60) `Angle="90"` bilan 60×1090 ✓.
- `01_004 utalshonka tepa`: elt/elb/elr → `(B) 1-35  Kashmir` (EL `elSymbol="B"`) → `F8, F9, F11` ✓;
  XNC `side="true" code="317501_01_004"` → `F6="317501_01_004"`, `F13="true"` ✓.
- `01_008 goli` ikki qator (bir xil) → `Д5`, `Д6`; XNC ikki tomonlama → `F6="317501_01_008"`,
  `F7="317501_01_008_2"` ✓.
- `01_013 pl` ikki qator, biri `elb`, biri `elt` → `Д13 F9`, `Д14 F8` ✓.
- 2-karta `Cut="false"`: 1-daraja `Px=0 Py=5 X=2750 Y=1700` (gorizontal polosa) ✓.
- 3-karta: `Part Px="929" Spare="True" UID="0" X="1821" Y="1830"` (929+1821=2750) ↔ `Spares О1 1821×1830 Count=1`
  ↔ loyihada qoldiq `l=1816 w=1820 rl=1821 rw=1830 business=true` ✓.

### 4.3 Buyurtma 3167 — ombordagi qoldiq listlar va 6 daraja

Loyiha listlari: `2750×1830 count=11`, `2750×1245 count=1`, `2570×1200 count=1` →
`Condition Count="3"`: `[0] 2570×1200 ×1`, `[1] 2750×1245 ×1`, `[2] 2750×1830 ×11` (tartib loyihadagidan teskari —
yuzasi bo'yicha o'sish). Kartalar: `SheetID=0` ×1, `SheetID=1` ×1, `SheetID=2` — 2+2+1+1+1+1+1+1+1 = 11 ✓
(11 ta butun list to'liq ishlatilgan). 82 qator / 117 dona = joylangan barglar ✓. Daraxt chuqurligi 6
(asbob `swMaxturns=6`).

### 4.4 Buyurtma 3181 — faqat qoldiq listlardan kesish

Material listlari hammasi `count=1`: 1810×534, 2750×1830, 2750×650, 2440×750, 600×530 → `Condition` da 5 ta
`Shape Count="1"` (tartib: 2750×1830, 2750×650, 600×530, 2440×750, 1810×534 — loyiha tartibidan farqli).
5 karta `SheetID` 0,1,2,4,3 — har list bir marta ✓. Loyihadagi chiqqan qoldiq `l=2333 w=740 rl=2338 rw=750`
↔ `Spares О1 2338×750`, joylashuvi `SheetID=3` (2440×750) kartasida `Px=102 X=2338` (102+2338=2440) ✓.
`TypeName="LDSP UD (110197)_diffuseOriginal"` — qavslar bilan to'liq nom, fayl nomida esa `LDSP_UD_110197__diffuseOriginal`.

### 4.5 Umumiy (14 fayl)

- `Σ(barg × Layout.Count)` = `Objective.Count` — 14/14; qoldiqlar soni — 14/14.
- `Turn == not txt` — 14/14 faylda 100%.
- `X,Y = dl,dw` — 3173 dan tashqari 100% (3173 loyihasi keyin tahrirlangan: masalan `01_001 bok` faylda
  2458×597, loyihada hozir 1868×597).
- Kromka `F8..F11 ↔ elt,elb,ell,elr` va `(elSymbol) band.name` — 100%.

## 5. Minimal misol

[nanxing-nxcutsaw.md §5](nanxing-nxcutsaw.md#5-minimal-qayta-tiklangan-misol) dagi misol bu papka uchun ham
to'g'ri (`Data.Type` yo'q, `Ply="16"`). Fayl nomi: `9999_mijoz_LDSP_OQ.CUT`, papkaga to'g'ridan-to'g'ri.

## 6. Savollar (shu papkaga xos)

1. Nima uchun bu stanok uchun faqat **birinchi** material eksport qilingan (XDF, ikkinchi LDSP va h.k. yo'q)?
   Stanok faqat 16 mm LDSP/LMDF kesadimi yoki bu namunani tayyorlashdagi tanlovmi?
2. `Nanxing (NXCutSaw)` va `Nanxing NXCutSAW` — ikki xil stanokmi (yoki ikki xil sex), yoki bitta stanokning ikki
   eksport rejimi? Formatda farq topilmadi.
3. Qolgan umumiy savollar — [nanxing-nxcutsaw.md §6](nanxing-nxcutsaw.md#6-noaniq-joylar--foydalanuvchiga-savollar)
   (torsovka 5 vs 2, paket balandligi, `CutCount`/`Flag`, koordinata boshi, kasr o'lchamlar).
