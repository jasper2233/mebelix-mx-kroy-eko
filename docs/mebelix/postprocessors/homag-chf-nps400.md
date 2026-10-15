# HOMAG CHF 41.44..44 (NPS400) — `.zip` (ichida `pattern.NNN`)

Manba: `D:\cloude giblab jasur\post prtsessorlar\PILNIY APPARAT\HOMAG CHF 41.44..44 (NPS400)\` — 10 ta zip (buyurtmalar 2027–2037), jami **51 ta pattern fayl, 827 ta `#CUT` yozuv**.
Loyihalar: `D:\cloude giblab jasur\giblab project\2 shogirt\<NNNN ...>\*.project`.

Holat: **to'liq (kesish rejasi bo'yicha)** — format juda sodda, 8 ta buyurtmada detal soni va o'lchamlari loyihaga 100% mos keldi. Faqat doimiy (har doim 0) maydonlarning ma'nosi noma'lum.

---

## 1. Ishlab chiqariladigan fayllar

| Xususiyat | Qiymat |
|---|---|
| Tashqi fayl | `<loyiha nomi>_<material nomi>.zip` — material nomidagi bo'shliqlar `_` ga almashtiriladi (masalan material `"LDSP UD "` → `..._LDSP_UD_.zip`, oxirgi bo'shliq ham `_` bo'ladi; `Ldsp oq` → `..._Ldsp_oq.zip`; apostrof saqlanadi). Loyiha nomi = `.project` dagi `<project name="NNNN_mijoz">`. |
| Zip soni | **1 zip = 1 material (bitta `CS` operatsiyasi)**. Har buyurtma uchun har material alohida zip. |
| Zip ichi | Papkasiz, tekis: `pattern.001`, `pattern.002`, … (3 xonali, 1 dan boshlab, nol bilan to'ldirilgan). |
| Pattern fayllar soni | **1 fayl = 1 fizik list (plita)**. Bir xil kesiladigan listlar uchun ham alohida fayl yoziladi — miqdor (kitob/stack) maydoni yo'q. Tekshiruv: `cMaterialCount` = fayl soni (2028: 3=3, 2029: 1=1, 2033: 5=5, 2034: 5=5, 2036: 2=2, 2037: 5=5). |
| Zip parametrlari | Deflate (`compress_type=8`), flag `0x0808` (UTF‑8 nom bayrog'i + data descriptor), `create_system=0`, versiya 20, izoh yo'q. |
| Kodirovka | Barcha 51 faylda faqat ASCII baytlar uchradi. Material nomida kirill bo'lsa qaysi kodirovka bo'lishi noma'lum (savol). |
| Qator oxiri | `CRLF` (`\r\n`), oxirgi qator ham `CRLF` bilan tugaydi. |
| Ajratgich | Vergul `,`; **har qator oxirida ham vergul bor** (trailing comma). |
| O'nli ajratgich | Nuqta `.` (`0.00`, `2.0`, `0.00000`). O'lchamlar namunalarda doim butun son (`770`), kasr o'lcham qanday yozilishi ko'rilmadi. |
| Birlik | mm. |

## 2. Fayl tuzilishi

Har bir `pattern.NNN` qat'iy tartibda:

```
#REMARK,<buyurtma>,<material>,
#DIMENSION,<X>,<Y>,<qalinlik>,0,
#SPEEDS,0.00,0.00,0.00,0.00,
#TRIMS,2.0,2.0,0.0,0.0,0,
#CUT,<daraja>,<o'lcham>,<takror>,0,0,0,0,0,0.00000,0,0,0,0,
... (#CUT qatorlari, 1 ta va undan ko'p)
```

Yozuv statistikasi (51 fayl): `#REMARK` 51, `#DIMENSION` 51, `#SPEEDS` 51, `#TRIMS` 51, `#CUT` 827. Boshqa yozuv turi yo'q.

### `#REMARK`
| Poz. | Ma'no | Misol | Manba |
|---|---|---|---|
| 1 | `#REMARK` | | |
| 2 | Buyurtma: raqam + bo'shliq + mijoz | `2028 mijoz` | `product.order` (yoki loyiha nomi `_`→bo'shliq) |
| 3 | Material nomi (o'zgarishsiz, bo'shliqlar saqlanadi: `LDSP UD `, plain HOMAG'da `LDSP  PIKARD`) | `LDSP OQ GLYANETS` | `good typeId="sheet"` → `name` |
Faqat ma'lumot (izoh). Vergul nom ichida bo'lsa nima bo'lishi noma'lum.

### `#DIMENSION`
| Poz. | Ma'no | Qiymatlar |
|---|---|---|
| 2 | **X** — 1‑darajali kesimlar (polosalar) o'lchanadigan o'q bo'yicha list o'lchami | 2750 / 1830 |
| 3 | **Y** — polosa uzunligi (ikkinchi o'q) | 1830 / 2750 / 1160 |
| 4 | Qalinlik, mm | 16 (hamma) |
| 5 | noma'lum, doim `0` | 0 |

Muhim: X/Y tartibi **listning burilishini** bildiradi. 29 faylda `1830,2750`, 21 faylda `2750,1830`, 1 faylda `2750,1160` (qoldiq list). Ya'ni optimizator listni qaysi tomondan birinchi kesishni tanlasa, shu tomonni X qilib yozadi. Qoldiqdan (`<part>` ichidagi stock, masalan 2029: `l=2750 w=1160 usedCount=1`) foydalanilganda DIMENSION = qoldiq o'lchami.

### `#SPEEDS`
`0.00,0.00,0.00,0.00` — barcha namunalarda doimiy. Ehtimol arra tezliklari (0 = mashina standarti). **Sozlama.**

### `#TRIMS`
`2.0,2.0,0.0,0.0,0` — doimiy. Loyihadagi `cTrimL="2" cTrimW="2"` ga mos. Taxmin: pos2 = X o'qidagi (1‑daraja) old kesim, pos3 = Y o'qidagi (2‑daraja) old kesim, pos4–5 = 3/4‑daraja trim (0), pos6 = butun son bayroq. Ikkala qiymat ham 2 bo'lgani uchun pos2/pos3 qaysi biri `cTrimL` ekanini ajratib bo'lmadi (savol).

### `#CUT`
| Poz. | Ma'no | Tur | Ko'rilgan qiymatlar |
|---|---|---|---|
| 1 | `#CUT` | | |
| 2 | **Kesim darajasi kodi** | int | `1`, `2`, `3`, `7` (7 = 4‑daraja) |
| 3 | **Bo'lak o'lchami** (kesim yo'nalishiga perpendikulyar kenglik), mm | int (namunada) | 50…2740 |
| 4 | **Takror soni** — shu o'lchamdagi bo'lak ketma‑ket necha marta kesiladi | int | 1–6 |
| 5–9 | noma'lum, doim `0` | int | 0 |
| 10 | noma'lum, doim `0.00000` | float 5 xona | 0.00000 |
| 11–14 | noma'lum, doim `0` | int | 0 |
| oxiri | bo'sh maydon (trailing comma) | | |

Daraja × takror taqsimoti (827 ta): `1`: 143 (takror 1/2), `2`: 358 (takror 1–6), `3`: 271 (takror 1–4), `7`: 55 (takror 1–3).

## 3. Kesish rejasi qanday kodlanadi

Fayl — gilyotina kesish **daraxtining pre‑order (chuqurlik bo'yicha birinchi)** yoyilmasi. Har `#CUT` qatori oldingi, darajasi bittaga past bo'lgan qatorning bolasi:

| Kod | Daraja | O'lcham qaysi o'q bo'yicha | Ichida kesiladi |
|---|---|---|---|
| `1` | 1 — bo'ylama polosa (rip) | X | butun list (X − trim) |
| `2` | 2 — ko'ndalang | Y | ota‑polosa (uzunligi Y) |
| `3` | 3 — qayta bo'ylama (recut) | X | ota‑bo'lak, eni = 1‑daraja o'lchami |
| `7` | 4 — qayta ko'ndalang | Y | ota‑bo'lak, uzunligi = 2‑daraja o'lchami |

(Daraja 4 uchun `4` emas, `7` kodi ishlatiladi — 55 holatning barchasida geometriya shuni tasdiqlaydi: masalan 2036 p001 da `2,680` → `3,100` → `7,310 ×2`: 310+310+kerf ≤ 680.)

Qoidalar (barcha 51 faylda tekshirildi, birorta istisno yo'q):
1. Daraja hech qachon sakramaydi: `n` darajali qator faqat `n‑1` dan keyin (yoki o'zidan/yuqoridan keyin) keladi.
2. **Bargli tugun (bolasi yo'q) = detal.** Bolasi bor bo'lak — oraliq bo'lak, detal emas.
3. **Chiqindi/qoldiq yozilmaydi**: har darajada bo'laklar ota‑bo'lakning boshidan zich joylashadi, qolgan qism (oxiridagi slack) avtomatik chiqindi. Alohida offcut/qoldiq yozuvi yo'q.
4. **Takror (pos4)** butun pastki daraxtga ta'sir qiladi: `#CUT,1,80,2` + bolalari → ikkita bir xil 80 mm polosa, har biri o'z bolalari bilan. Detal soni = barcha ota takrorlari ko'paytmasi.
5. Bir xil o'lchamli qo'shni bo'laklar ba'zan bitta `takror` ga birlashmaydi (`2,567,2` + `2,567,1`; `3,100,1` + `3,100,2`). Tahlil: bular **turli loyiha detal yozuvlari** (part id) chegarasida bo'linadi (2029: part 21 cnt 2 = 1+1, part 20 cnt 2 = `3,100,2`). Mashina uchun fizik natija bir xil.
6. 1‑darajali polosalar barcha 51 faylda **kamayish tartibida** (eng keng polosa birinchi). 2/3‑darajada tartib qat'iy emas.
7. Detal o'lchami: barg darajasiga qarab
   - 2‑daraja barg: `(X = s1, Y = s2)`
   - 3‑daraja barg: `(X = s3, Y = s2)`
   - 4‑daraja (`7`) barg: `(X = s3, Y = s4)`
8. Kerf (arra qalinligi) faylda **yo'q** — mashina sozlamasi. Geometrik tekshiruv: `kerf=3` (loyihadagi `swSawthick="3"`) bilan barcha 402 ota‑bo'lakda Σ(o'lcham×takror) + takrorlar_soni×3 ≤ ota‑o'lcham; 1/2‑darajada qo'shimcha ≥7 mm zaxira qoladi (2+2 trim sig'adi). `kerf=4` bilan 2036 p001 da sig'maydi → kerf 3 mm.
9. Bitta polosa 1‑darajada bargli bo'lib keladigan holat (polosaning o'zi detal) namunalarda uchramadi.
10. Detal nomi, kodi, etiketka, kromka, stack (kitob) balandligi — **faylda yo'q**. `swPackageHeight="40"` (paket balandligi) ham faylga chiqmaydi.

### Tola yo'nalishi (tekstura)
Faylda alohida bayroq yo'q; yo'nalish DIMENSION tartibi + daraja orqali aniqlanadi. Listning uzun tomoni (2750, loyihadagi `sheet l`) bo'yicha detal o'lchami = detalning `l`/`cl` qiymati bo'lishi kerak. Tekshiruv: 2033 (yagona hisoblangan, teksturali loyiha, `csTexture="true"`) — 18 ta `txt="true"` detalning hammasi `cl` list uzunligi bo'ylab joylashgan (masalan `Fasad 1949×532` → L=1949). Teksturasiz (`txt="false"`) detallar erkin buriladi (2028: `738×350` detal L=350, W=738 bo'lib kesilgan).

## 4. Loyiha → fayl moslashuvi

| Loyiha maydoni | Fayldagi joyi |
|---|---|
| `project/@name` | zip nomi prefiksi |
| `product.order` ("NNNN mijoz") | `#REMARK` pos2 |
| `good[@typeId=sheet]/@name` | `#REMARK` pos3 va zip nomi qo'shimchasi |
| `sheet @l/@w` yoki ishlatilgan stock/qoldiq `<part l w>` | `#DIMENSION` X,Y (burilish bilan) |
| `sheet @t` | `#DIMENSION` pos4 |
| `operation[CS] @cTrimL/@cTrimW` | `#TRIMS` pos2/pos3 (2.0) |
| `tool.cutting @swSawthick` | faylda yo'q (mashinada 3 mm) |
| `part @cl/@cw` (kesish o'lchami) | barg `#CUT` o'lchamlari |
| `part @count` | barg bo'laklar soni (takrorlar ko'paytmasi bilan) |
| `part @txt` + `csTexture` | faqat joylashuv yo'nalishi orqali |
| kromka (`ell/elr/elt/elb`), `jl/jw`, nom, kod | **yozilmaydi** |

Kesish o'lchami: barcha mos loyihalarda `cl==l`, `cw==w` (kromkali `Fasad lrtb`: `l=1949`, `jl=1947`, faylda **1949**). Ya'ni faylga kromka bilan birga tayyor o'lcham = `cl/cw` yoziladi, `jl/jw` emas. (`elWidthPreJoint` / `cSizeMode` boshqacha bo'lganda `cl` o'zgarishi mumkin — generator `cl/cw` ni olishi kerak.)

### Tekshiruv natijalari (detal soni va o'lcham multiset'i)

| Buyurtma | Fayllar | Detal (faylda) | Mos loyiha / CS op | Natija |
|---|---|---|---|---|
| 2027 | 8 | 73 | `2027 «mijoz».project` op 3 | 73 = 73, o'lchamlar MOS |
| 2028 | 3 | 23 | `2028_«mijoz».project` op 2 (`cMaterialCount=3`) | MOS |
| 2029 | 1 | 23 | `2029_«mijoz».project` op 3 (`Ldsp oq`, qoldiq 2750×1160) | MOS |
| 2030 | 3 | 35 | — | saqlangan loyihalar keyin o'zgartirilgan, mos kelmadi |
| 2031 | 3 | 47 | `2031 «mijoz».project` op 2 | MOS |
| 2032 | 16 | 201 | — | mos loyiha topilmadi |
| 2033 | 5 | 36 | `2033_«mijoz».project` op 3 (`cMaterialCount=5`) | MOS |
| 2034 | 5 | 67 | `2034_«mijoz».project` op 3 (`cMaterialCount=5`) | MOS |
| 2036 | 2 | 35 | `2036_«mijoz».project` op 4 (`cMaterialCount=2`) | detallar MOS (lekin stock farqi, quyida) |
| 2037 | 5 | 44 | `2037_«mijoz».project` op 3 (`cMaterialCount=5`) | MOS |

**Misol A — 2028, pattern.001** (`#DIMENSION,1830,2750` → X=1830):
```
#CUT,1,1820,1   polosa 1820 (X bo'ylab, 1830−2−… ichida)
#CUT,2,770,1    → barg: 1820×770  = "00.001 pol" (l=770,w=1820)  ×1
#CUT,2,350,1    → oraliq bo'lak 350
#CUT,3,868,2    →   barg: 868×350 = "02.003 tom" ×2
#CUT,2,770,2    → barg: 1820×770 ×2
```
Jami 5 detal. Uchta fayl bo'yicha: `pol 770×1820` 1+2=3 (loyihada `count=3`), `02.003 868×350` 2+2=4 (count 4), `01.005 738×350` 2+4=6 (count 6), `bok 2000×350` 5+5=10 (01.001 ×5 + 01.002 ×5). Jami 23 = `cPartCount 23`.

**Misol B — 2029** (qoldiq list `2750×1160`, bitta fayl, 23 detal): polosalar `704,704,400,367,168,80×2` (kamayish tartibi). `704` polosa: `2,500`,`2,500` → `704×500` (pb-bok), `2,100` → `3,310 ×2` → `310×100` (03_007/03_008, teksturasiz — burilgan). `1,80,2` → ikkita 80 polosa, har birida `368` va `768` → `pb-pl 368×80` jami 4 (03_009 cnt2 + 04_006 + 04_007), `768×80` jami 4 (01_006 cnt2 + 02_006 cnt2). Jami 23 = `cPartCount 23`.

**Misol C — 2036, pattern.001** (`1830,2750`): `1,784` → `2,500 ×5` (5 ta `784×500 pb-bok`) + `2,100 ×2` → `3,400`, `3,310` … ; `1,520` polosada `2,680` → `3,100` → `7,310`,`7,310` (4‑daraja: `310×100` tr) va `3,80` → `7,324 ×2` (`324×80` pb-pl, 04_005/04_006). Ikki fayl bo'yicha jami 35 detal, loyihadagi 27 yozuvning count yig'indisi 35 bilan mos.

## 5. Minimal qayta tiklangan misol (anonim)

Zip: `1001_mijoz_LDSP_OQ.zip` → ichida bitta `pattern.001` (ASCII, CRLF):
```
#REMARK,1001 mijoz,LDSP OQ,
#DIMENSION,2750,1830,16,0,
#SPEEDS,0.00,0.00,0.00,0.00,
#TRIMS,2.0,2.0,0.0,0.0,0,
#CUT,1,700,2,0,0,0,0,0,0.00000,0,0,0,0,
#CUT,2,400,2,0,0,0,0,0,0.00000,0,0,0,0,
#CUT,2,300,1,0,0,0,0,0,0.00000,0,0,0,0,
#CUT,3,400,1,0,0,0,0,0,0.00000,0,0,0,0,
#CUT,3,250,1,0,0,0,0,0,0.00000,0,0,0,0,
#CUT,7,140,2,0,0,0,0,0,0.00000,0,0,0,0,
```
Ma'nosi: 2750 bo'ylab ikkita 700 mm polosa; har birida 2×(700×400) detal, so'ng 300 mm bo'lak → 400×300 detal va 250 mm bo'lak → 4‑darajada 2×(250×140). Natija: 4× 700×400, 2× 400×300, 4× 250×140 = 10 detal. Sig'ish: 1‑d. 1400+2·3 ≤ 2746; 2‑d. 1100+3·3 ≤ 1826; 3‑d. 650+2·3 ≤ 700; 4‑d. 280+2·3 ≤ 300. (Bizning parser bilan tekshirildi.)

### Generator algoritmi (MebeliX Kroy uchun)
1. Har material (CS natija) → bitta zip; har fizik list → `pattern.%03d`.
2. List gilyotina daraxtini 4 darajagacha qurish (kod 1,2,3,7). 4 dan chuqur daraja formatda yo'q (`swMaxturns="4"` ham shuni bildiradi).
3. X = 1‑darajali kesimlar perpendikulyar bo'lgan o'q bo'yicha list o'lchami; agar optimizator listni "burgan" bo'lsa X=1830, Y=2750 yoziladi.
4. Pre‑order yozish; ketma‑ket bir xil o'lcham + bir xil pastki daraxt → `takror` ga birlashtirish (ixtiyoriy).
5. Chiqindini yozmaslik — har darajada detallar boshidan zich joylashishi kerak (oraliq chiqindi bo'lsa uni ifodalab bo'lmaydi; kerak bo'lsa barg bo'lmagan "bo'sh" bo'lak qo'shish mumkinmi — savol).
6. O'lchamlar `cl/cw`, butun mm (kasr formatini aniqlash kerak).

## 6. Noma'lum / savollar

1. `#CUT` pos5–14 (`0,0,0,0,0,0.00000,0,0,0,0`) — nima uchun? (ehtimol: arra/tezlik rejimi, burish bayrog'i, etiketka/detal raqami, chiqindi bayrog'i). Mashina hujjatini (NPS400 / HOMAG "pattern" ASCII importi) ko'rish mumkinmi?
2. `#DIMENSION` 5‑maydon (`0`) — list soni (kitob) yoki tekstura bayrog'imi? Hozir har list alohida fayl; agar `>0` bo'lsa stack qilinadimi?
3. `#TRIMS` pos2/pos3 — qaysi biri uzunlik (`cTrimL`), qaysi biri eni? pos4–5 (0.0) va pos6 (0) ma'nosi? Trim bir tomonlami yoki ikki tomonlami?
4. Nega 4‑daraja kodi `4` emas `7`? `4`, `5`, `6` kodlari boshqa ma'noga egami (masalan bosh kesim / head cut, rotatsiya)? Namunalarda bosh kesim (list oldindan bo'linishi) yo'q.
5. Kasr o'lchamlar (masalan 717.5) qanday yoziladi — `717.5` yoki `717.50`?
6. Material nomida kirill yoki vergul bo'lsa — kodirovka (cp1251/cp866?) va ekranlash qanday?
7. 1000 tadan ortiq list bo'lsa fayl nomi (`pattern.1000`?).
8. Oraliq chiqindi (bo'laklar orasidagi chiqindi) yoki 1‑darajali bargli polosa — mashina qabul qiladimi?
9. 2036 loyihasida `cMaterialCount=2`, lekin stock yozuvida 1020×1485 qoldiq `usedCount=1` ko'rsatilgan, fayllardagi ikkala DIMENSION esa to'liq 1830×2750 — eksport paytidagi holat loyihada saqlanmaganmi?
10. Plain `HOMAG` papkasidagi zip'lar bilan farq: bir qarashda format bir xil (`pattern.NNN`, xuddi shu yozuvlar). Ikkalasi bir postprotsessormi yoki faqat mashina profili (kerf/trim sozlamasi) bilan farq qiladimi?
