# Nanxing CutSaw — `.ncp` binar format (zip ichida)

**Holat: to'liq tushunilgan.** Format `Nanxing (CutSawFG)` bilan **baytma-bayt bir xil tuzilma** —
to'liq maydon jadvallari, daraxt qoidalari va yozuvchi kodi [nanxing-cutsawfg.md](nanxing-cutsawfg.md)
da. Bu yerda — shu papka namunalarining o'z tekshiruvi, farqlar va savollar.

Manba: `post prtsessorlar/PILNIY APPARAT/Nanxing CutSaw/*.zip` — 14 ta zip (buyurtmalar 3167–3182),
80 ta `.ncp`, 1734 tugun, 990 barg (984 detal o'rni + 6 qoldiq), 89 list. Hammasi parserdan xatosiz
o'tdi, `write_ncp` ularni **80/80 baytma-bayt** qayta yaratdi, `Nanxing NXCutSAW/*.CUT` dagi kartalar
bilan 80/80 mos (detal to'plami, o'lchamlari, koordinatalari, `count`, qoldiqlar).

---

## 1. Fayllar

| Xususiyat | Qiymat |
|---|---|
| Tashqi fayl | `<buyurtma>_<mijoz>_<material>.zip` (`3171_mijoz_LDSP_DUB_VATAN_TEKSTURA.zip`), nom `.CUT` bilan bir xil |
| Ichida | `001.ncp … 0NN.ncp`, har noyob karta uchun bitta; 2–11 ta fayl |
| Ichki zip | **bu namunalarda yo'q** — har buyurtmada bitta material eksport qilingan (loyihada XDF/KASHMIR kabi boshqa CS operatsiyalari bo'lsa ham, masalan 3167, 3174, 3181) |
| Zip | Deflate, flag `0x0808`, version 20, papkasiz, kommentariysiz (CutSawFG bilan bir xil) |
| Kodirovka | binar LE; matnlar UTF‑16LE + `0xCC` to'ldirish; etiketkada o'nlik `.` |
| Hajm | `0x1C + N·0x208 + 0x68 + M·0x1000` (3174 `001.ncp`: N=4, M=2 → 10404 bayt) |

## 2. Tuzilma (qisqa — to'liq jadval: nanxing-cutsawfg.md §2)

```
0x00  "\0ZBD" | double L | double W | double qalinlik
0x1C  ildiz yozuvi: double propil | int count | int count | float util | int N | 64 bayt konstanta | tugun tanasi
0x1C+k·0x208  tugun: int −1 | 16×0 | CC×4 | wchar[32] nom | int ota | int bolalar | 8×double
              (L W wL wW tX tY X Y) | 22×{int tur,int soni,double o'lcham} | int yozuvlar soni | CC×4
dum (0x68)   int −1 | 16×0 | CC | double 5.0 | wchar[32] "MATERIAL NAME" | int 1 | int count
etiketkalar  M × wchar[2048] CSV (21 maydon)
```

Bu papkadagi qiymatlar: propil 3 (80/80), torsovka 5 (80/80), qalinlik 16, `count` 1 yoki 2
(9 faylda 2), tugunlar 4…61, kesim yozuvlari ≤ 13, chuqurlik ≤ 6.

## 3. Kesish rejasi

CutSawFG bilan bir xil qoidalar (qarang §3 o'sha hujjatda): daraxt, o'q almashinuvi, 0/1‑darajada 5 mm
torsovka, bo'laklar guruhlanishi, chiqindi `= o'lcham − torsovka − Σ(o'lcham+3)`, teskari bola tartibidagi
pre‑order, Y‑ildizda Y koordinatalari +3, qoldiq qoidasi (`max≥1000`, `min≥500`), `util`.

Bu papkaga xos kuzatuvlar:
- **Qoldiq listlar.** Sarlavhadagi L×W — ishlatilgan list: 3181 da `2750×1830`, `2750×650`, `600×530`,
  `1810×534`, `2440×750` (loyiha CS dagi 5 ta sheet part, `.CUT Condition` 5 ta Shape, `SheetID`);
  3174 `001.ncp` `2750×450`; 3167 `2570×1200`, `2750×1245`. Kichik listlarda ham 5 mm torsovka.
- **Qoldiq chiqishi** (6 ta): masalan 3175 `003.ncp` `$1 1816×1830 @X=929`, etiketka `1816.00,1820.00`,
  `.CUT О1 1821×1830`, loyihada `waste business l=1816 w=1820 rl=1821 rw=1830` — uchala manba mos.
- `count=2` li kartalar (3167, 3168, 3171, 3173, 3174, 3175, 3182): ichidagi detallar 2 marta hisoblanadi.

## 4. Loyiha → fayl (tekshirilgan misollar)

Moslik qoidalari CutSawFG §4 dagi bilan bir xil. 14 materialdan 13 tasida `.CUT Objective` ↔ loyiha CS
`part` ro'yxati qator-qator 100% mos (`Д<n>` = CS dagi n‑detal, `F1=name`, `F4=l`, `F5=w`, `F3=count`);
3173 da loyiha keyin o'zgartirilgan (2458 → 1868). Barcha 14 materialda Σ(barg × `count`) = Σ`count`
(masalan 3167: 117 = 117, 3182: 117 = 117, 3171: 28 = 2+2+4+4+6+10).

**A. 3171, `001.ncp` (`count=2`).** Loyiha CS «LDSP DUB VATAN TEKSTURA» 2750×1830×16, `swSawthick=3`,
`cMinDimRegWaste 1000/500`. Detallar: Д1 `01_001 oldi bok` l=1400 w=1750 ×2 txt=true 4 tomon kromka (A);
Д2 `01_002 tom` 1718×584 ×2 `elt`; Д5 `01_005 pol` 590×583 ×6; Д6 `01_006 pol` 548×583 ×10.
Fayl: ildiz `(2,1,5),(0,1,1400),(0,1,1175)`, chiqindi `2750−5−1403−1178=164`.
```
#1 NONE 1175x1830 @(1408,0)  (3,1,5),(1,1,1718)          wW=1830−5−1721=104
  #2 NONE 1175x1718 @(1408,5) (0,1,584),(0,1,583)        wL=1175−587−586=2
    #3 NONE 583x1718 @(1995,5) (1,1,590),(1,2,548)       wW=23
      #4 Д6 583x548 @(1995,1149)  #5 Д6 @(1995,598)  #6 Д5 583x590 @(1995,5)
    #7 Д2 584x1718 @(1408,5)
#8 NONE 1400x1830 @(5,0) (3,1,5),(1,1,1750) → #9 Д1 1400x1750 @(5,5)   (txt=true → burilmagan)
```
Etiketka: `Д1,3171 mijoz,LDSP DUB VATAN TEKSTURA,01_001 oldi bok,,1,1400.00,1750.00,2,false,(A) 1-19 dub votan,(A) 1-19 dub votan,(A) 1-19 dub votan,(A) 1-19 dub votan,false,false,false,,,,01 parta`.
5 slot (5 barg), 4 noyob detal + 1 bo'sh.

**B. 3175, `003.ncp` (qoldiq).** `01_007 oyoq` 330×1732 ×2 (`elt,elb,elr` → #10,#11,#13; XNC `317501_01_007`
→ #17, parmalash → #16 `true`), `01_008 goli` 250×1700 (XNC old `317501_01_008` + orqa `…_2` → #17/#18).
Ildiz `(2,1,5),(0,1,921)` → chiqindi 1821×1830 ≥ chegaradan → `$1 1816×1830 @X=929`; `util` =
(2·330·1732+250·1700)/(5 032 500−1816·1820) = 0.90780 ✓.

**C. 3168 (paz bayrog'i, etiketka #14).** `02_001 bok`, `02_002 bok` (XNC'da `Cut4` bilan paz, `countCut=3.84`)
→ #14 `true`; `02_003 bok` (pazsiz) → `false`; `02_008 tom` — paz faqat orqa tomon dasturida (`…_2`) →
#14 `true`, #18 = `316801_02_008_2`. Butun korpusda #14 = «XNC dasturida `gr`» 37/37, #15 = frezer, #16 = parmalash (100%).

**D. 3181, `003.ncp` (kichik qoldiq list 600×530).** Ildiz `(2,1,5),(0,1,320),(0,1,94),(0,1,136)`,
chiqindi 36; har polosada `(3,1,5)`; Д32 `01_031 tom` 136×250 count=4 (bu listda 2).

**E. 3174, `001.ncp` (list 2750×450, ildiz Y bo'yicha).** `(3,1,5),(1,1,435)` → polosa `@Y=8` (CUT `Py=5`, +3 qoidasi),
ichida `(2,1,5),(0,1,1340),(0,1,1340)` → Д18 `@(5,8)`, Д19 `@(1348,8)`.

## 5. Minimal misol

CutSawFG §5 dagi misol va `write_ncp` aynan shu stanok uchun ham to'g'ri (bir xil format). Eng kichik
haqiqiy fayl shakli (3174 `001.ncp` asosida, anonim):

```
sarlavha: "\0ZBD", L=2750, W=450, t=16 | propil 3, count 1/1, util=Σ/S, N=4
#0 ildiz 2750x450 waste 2750x7 t=(0,5) [(3,1,5),(1,1,435)] nchild=1
  #1 NONE 2750x435 @(0,8) waste 59x435 t=(5,0) [(2,1,5),(0,1,1340),(0,1,1340)] nchild=2
    #2 Д2 1340x435 @(1348,8)
    #3 Д1 1340x435 @(5,8)
dum: −1, 0…, 5.0, "MATERIAL NAME", 1, 1
etiketka ×2: "Д2,0001 mijoz,LDSP,01_014 Fasad,,2,1340.00,435.00,1,false,(A) …,(A) …,(A) …,(A) …,false,false,true,000101_01_014,,,01 shkaf", "Д1,…"
hajm = 28 + 4·520 + 104 + 2·4096 = 10404
```

## 6. Ochiq savollar

1. **CutSaw va CutSawFG farqi nima?** Fayl formati, sozlamalar (propil 3, torsovka 5, konstantalar) va zip
   tuzilishi namunalarda bir xil. Farq faqat stanokdami (FG modeli?) yoki eksport sozlamasidami
   (masalan, boshqa materiallarni ichki zipga qo'shish)? Bitta generator ikkalasiga yetadimi?
2. 31xx buyurtmalarda faqat bitta material eksport qilingan (3167/3174 da XDF, 3181 da KASHMIR va XDF
   CS operatsiyalari bor, lekin zipda yo'q) — ataylabmi (XDF bu stanokda kesilmaydimi)?
3. Torsovka 5 mm (loyihada `cTrimL/W=2`) — stanok sozlamasimi? Kichik qoldiq listlarda ham 5 kerakmi?
4. Y bo'yicha boshlanadigan kartalarda koordinata +3 (propil) — stanok shuni kutadimi?
5. Qoldiq `$k` raqamlash tartibi va etiketkadagi qisqartirish (−10 faqat to'liq list tomonida) stanok
   uchun muhimmi yoki faqat chop etish uchunmi?
6. Etiketka #19 (material turi) bu papkada doim bo'sh — MebeliX da qaysi maydondan to'ldirish kerak?
