# FastPanel — `.ocm` (ManualPattern XML) postprotsessori

**Manba namunalar:** `post prtsessorlar/PILNIY APPARAT/FastPanel/<buyurtma_raqami>/*.ocm` — 13 ta fayl.
**Taqqoslash uchun:** GibLab `.project` fayllari (`giblab project/2 shogirt/<buyurtma>/`) va xuddi shu
buyurtmalarning Nanxing NXCutSaw `.CUT` (AutoCUT XML) fayllari (`Nanxing (NXCutSaw)/<buyurtma>/`).
**Tushunish darajasi:** to'liq (format sodda, barcha 13 faylda tekshirildi; ochiq savollar faqat stanok
tomonidagi talqin — torsovka ikki tomonlamami, kasr sonlar formati va h.k.).

> Mijoz ismlari hujjatda «mijoz» bilan almashtirilgan. Detal nomlari (masalan `01.001 bok`) mijoz
> ma'lumoti emas, ular saqlab qolindi.

---

## 1. Qanday fayllar chiqadi

| Xususiyat | Qiymat |
|---|---|
| Kengaytma | `.ocm` |
| Fayl soni | **bitta buyurtma × bitta material (CS operatsiyasi) = bitta fayl**. Bir faylda shu materialning barcha listlari (kartalari) bor. |
| Nom shabloni | `<loyiha nomi>_<material nomi>.ocm`. Bo'shliqlar ketma-ketligi → bitta `_` (oxiridagi bo'shliq ham `_` bo'ladi). Misollar: loyiha `2027 mijoz` + material `LDSP UD ` → `2027_mijoz_LDSP_UD_.ocm`; material `XDF 2800x2070 mm  5.8 kv` (ikki bo'shliq) → `..._XDF_2800x2070_mm_5.8_kv.ocm`. Apostrof (`'`) o'zgarishsiz qoladi. |
| Papka | Namunalarda fayllar buyurtma raqami nomli papkalarga qo'yilgan (`2027`, `2028`, … `2037`). Bu **yillar emas — buyurtma raqamlari** (fayl nomining birinchi 4 raqami bilan bir xil). Papkani postprotsessor emas, operator yaratgan bo'lishi ehtimoli katta. `2033`, `2034`, `2036`, `2037` papkalari **bo'sh** — bu buyurtmalar uchun FastPanel fayli chiqarilmagan. |
| ZIP | Yo'q, oddiy fayl. |
| Kodlash | Faqat ASCII baytlar (13 faylning hammasi). BOM yo'q, `<?xml ...?>` deklaratsiyasi **yo'q**. Kirill harfli material nomi bo'lsa qanday kodlanishi noma'lum (savol). |
| Qator oxiri | **Umuman yo'q** — butun XML bitta qatorda, oxirida ham `\n` yo'q. |
| Sonlar | Hamma joyda butun son, mm. Kasr qismi uchrashmadi (kasr ajratgich — savol). |
| Atributlar tartibi | Alifbo tartibida: `PanelInfo` → `BladeThickness Length Quantity Thickness TrimSize Width`; `Entry` → `Distance Quantity`. (Ehtimol serializer avtomatik saralaydi — biz ham shunday yozamiz.) |
| Bo'sh element | Bolasi yo'q `Entry` va `PanelInfo` — `<.../>` (bo'shliqsiz `"/>`). |

Fayllar o'lchami: 552 B … 13 659 B. Fayllarning yaratilish vaqti (27.09, 20:49–21:05) NXCutSaw `.CUT`
fayllaridan (19:34) keyinroq — ya'ni ular **alohida, qayta kroy qilingan** natijadan chiqarilgan
(pastga qarang, §4.3).

---

## 2. To'liq tuzilma

```
ManualPattern  @JobName
 ├─ PanelInfo  @BladeThickness @Length @Quantity @Thickness @TrimSize @Width     ┐ juftlik,
 └─ Pattern                                                                         ┘ har bir karta uchun
     └─ Entry @Distance @Quantity          ← 1-daraja: polosalar (Length o'qi bo'ylab)
         └─ Entry @Distance @Quantity      ← 2-daraja: polosa ichidagi kesimlar (Width o'qi bo'ylab)
             └─ Entry @Distance @Quantity  ← 3-daraja: qayta kesish (yana Length o'qi bo'ylab)
```

`ManualPattern` ichida `PanelInfo` va `Pattern` **navbatma-navbat** keladi: `PanelInfo, Pattern,
PanelInfo, Pattern, …`. Har bir juftlik — bitta karta (raskroy sxemasi). Boshqa element turlari yo'q.

### 2.1 `ManualPattern`

| Atribut | Turi | Ma'nosi | Kuzatilgan |
|---|---|---|---|
| `JobName` | satr | Fayl nomi kengaytmasiz (13/13 faylda aynan teng) | `2027_mijoz_LDSP_UD_` |

### 2.2 `PanelInfo` (karta boshi)

| Atribut | Turi/birlik | Ma'nosi | Kuzatilgan qiymatlar | Doimiy/ma'lumot |
|---|---|---|---|---|
| `BladeThickness` | int, mm | Arra qalinligi (kerf) = `tool.cutting/@swSawthick` | 3 (52/52) | sozlama (loyihadan) |
| `Length` | int, mm | Listning **1-darajali kesimlar o'lchanadigan** tomoni (pastga qarang) | 2750, 1830, 2800, 2070 | ma'lumot |
| `Width` | int, mm | Listning ikkinchi tomoni | 1830, 2750, 2070, 2800, **1160** (qoldiq list) | ma'lumot |
| `Quantity` | int | Shu sxema bo'yicha kesiladigan bir xil listlar soni | 1, 2, 4 | ma'lumot |
| `Thickness` | int, mm | Material qalinligi = material `good/@t` | 16 (LDSP/LMDF), 3 (XDF) | ma'lumot |
| `TrimSize` | int, mm | List chetidan torsovka (обрезка) | 5 (52/52) | sozlama (stanok/postprotsessor; loyihadagi `cTrimL/W=2` bilan **mos emas**!) |

**`Length`/`Width` yo'nalishi** — eng muhim qoida. `Length` doim list uzun tomoni emas: u 1-darajali
(polosa) kesimlar qaysi o'q bo'ylab ketma-ket joylashishini ko'rsatadi.
- `Length=2750 Width=1830` — polosalar 2750 mm tomon bo'ylab terilgan (kesim chiziqlari 1830 tomonga parallel).
- `Length=1830 Width=2750` — xuddi o'sha list, lekin 90° ga burilgan sxema: polosalar 1830 tomon bo'ylab.
Bir faylda ikkala variant aralash keladi (masalan, 2027 LDSP faylida 7 kartadan 4 tasi `1830×2750`).
NXCutSaw `.CUT` bilan solishtirganda: `.CUT` `Layout/@Cut="true"` ⇔ `.ocm` `Length = X` (2750),
`Cut="false"` ⇔ `Length = Y` (1830) — mos keluvchi barcha kartalarda tasdiqlandi.

Qoldiq (delovoy) list ishlatilganda `PanelInfo` o'sha qoldiq o'lchamini oladi: 2029 «Ldsp oq» —
loyihada `sheet l=2750 w=1160 count=1` → `.ocm` da `Length="2750" Width="1160"`.

### 2.3 `Pattern` va `Entry`

`Pattern` — atributsiz konteyner, ichida 1-darajali `Entry` lar.

| Atribut | Turi | Ma'nosi |
|---|---|---|
| `Distance` | int, mm | Bo'lakning shu darajadagi kesish o'qi bo'yicha o'lchami (polosa eni / detal uzunligi va h.k.). Arra kesimi (kerf) **kiritilmaydi**. |
| `Quantity` | int ≥1 | Shu bo'lak **ketma-ket necha marta takrorlanadi** (bir xil `Distance` bilan necha marta kesiladi). Agar `Entry` ning bolalari bo'lsa, har bir nusxa o'sha ichki sxemaga ega. |

Daraja (chuqurlik) bo'yicha ma'no:

| Daraja | O'q | Mavjud joy | Bolasiz `Entry` (barg) ma'nosi |
|---|---|---|---|
| 1 | `Length` | `Length` (boshida `TrimSize`) | Uchramaydi — 1-darajada har doim bolalar bor (136/136) |
| 2 | `Width` | `Width` (boshida `TrimSize`) | **Detal**: o'lchami = (ota 1-daraja `Distance`) × (o'z `Distance`) |
| 3 | `Length` | Ota 1-darajali polosaning `Distance` i (torsovkasiz) | **Detal**: o'lchami = (o'z `Distance`, Length o'qi) × (ota 2-daraja `Distance`, Width o'qi) |

- Maksimal chuqurlik **3** (barcha namunalarda). 4-daraja uchramadi (savol: stanok qo'llaydimi?).
- 3-darajali `Entry` lar doim barg (bolasiz).
- **Har bir barg — bitta detal (×Quantity × ota Quantity lar × PanelInfo Quantity).** Chiqindi /
  qoldiq bo'laklar faylda **yozilmaydi**: polosa yoki bo'lakning oxirida qolgan joy shunchaki
  hech qanday `Entry` siz qoladi. `.CUT` dagi `Spare="True"` (delovoy qoldiq) bo'laklar `.ocm` ga
  tushmaydi.
- Detal nomi, kodi, ID, etiketka, kromka, tola yo'nalishi, burilish burchagi — **hech biri yo'q**.
  Fayl faqat geometriya (kesish dasturi).

Kuzatilgan `Quantity` taqsimoti (barcha fayllar, 688 `Entry`): 1-daraja: q=1 ×131, q=2 ×5;
2-daraja: q=1…5; 3-daraja: q=1…6.

### 2.4 Geometrik cheklovlar (namunalardan chiqarilgan)

Har bir daraja uchun (n = shu darajadagi bo'laklar soni, Quantity hisobga olingan):

```
1–2-daraja:  TrimSize + Σ(Distance·Quantity) + BladeThickness·(n−1)  ≤  mavjud o'lcham − 5
3-daraja:               Σ(Distance·Quantity) + BladeThickness·(n−1)  ≤  ota polosa Distance − 5   (yoki aniq teng)
```
Tekshiruv: 52 karta, 136 ta 1-daraja, 136 ta 2-daraja guruhi, 159 ta 3-daraja guruhi — **hech bir
buzilish yo'q**; minimal qoldiq (slack) har uchala darajada aynan **5 mm** (masalan 1820 mm li polosa
1830 listda: 5 + 1820 = 1825, 5 mm qoladi). Bu oxirgi tomonda ham 5 mm torsovka yoki
`swMinPruning=5` (minimal kesib tashlanadigan bo'lak) ekanini ko'rsatadi. Generator uchun xavfsiz
qoida: **ikkala chetda `TrimSize`, oxirgi bo'lakdan keyin kamida 5 mm yoki aniq 0**.

---

## 3. Kroy rejasining kodlanishi

1. **Listlar/kartalar**: har bir `PanelInfo+Pattern` — bitta noyob karta; `PanelInfo/@Quantity` —
   shu kartadagi listlar soni (pachka/kitob emas, shunchaki takror). Faylning barcha `Quantity`
   yig'indisi = materialning ishlatilgan listlar soni (`cMaterialCount`) — mos keluvchi fayllarda
   tasdiqlandi (2027 LDSP: 7 karta, 8 list; 2032 LMDF: 16 karta, 18 list = `.CUT` dagi `Layout/@Count`
   yig'indisi 18).
2. **Kesish ketma-ketligi**: element tartibi = jismoniy tartib, torsovka chetidan boshlab
   (`.CUT` dagi `Px`/`Py` o'sish tartibi bilan bir xil). Avval 1-daraja (polosalar, «продольный рез»),
   so'ng har bir polosa ichida 2-daraja («поперечный»), so'ng 3-daraja (qayta kesish / «третий рез»).
   Burilishlar (rotation) soni = sxema chuqurligi − 1; maksimal 3 daraja → 2 burilish.
3. **Takror (`Quantity`) qoidasi**: ketma-ket kelgan **bir xil detal qatori** (loyihadagi bitta
   `part`, bitta UID) bo'laklari bitta `Entry` ga `Quantity=N` bilan birlashtiriladi; o'lchami bir xil,
   lekin **boshqa** loyiha qatori bo'lgan detallar alohida `Entry` bo'lib qoladi. Masalan, 2029 METALIK:
   `01_002 pb-bok` va `01_003 pb-bok` (ikkalasi 704×500, count=1) → ikki alohida `Entry Distance="704"`;
   2030 XDF: `01_017 XDF ort` (count=2) → bitta `Entry Distance="1139" Quantity="2"`. Bu `.CUT` dagi
   `Grouped="N"` atributi bilan aynan mos (N ta ketma-ket bir xil bo'lak — guruh). Ichki sxemali
   (bolali) bo'laklar ham shunday guruhlanadi (2028: `Entry 738 q=2` ichida `350 q=2`).
   Karta darajasida ham xuddi shunday: 2032 XDF faylida ikki ketma-ket bir xil karta birlashtirilmagan
   (detallar har xil qatorlardan) — bu xato emas.
4. **Qoldiqlar**: faylda yo'q. Stanok oxirgi bo'lakdan keyingi joyni chiqindi deb biladi.
5. **Etiketka, kitob (stack) balandligi**: faylda yo'q. `Thickness` bor, lekin
   `swPackageHeight=40` (pachka balandligi) yoki pachkadagi listlar soni yozilmaydi.

---

## 4. Loyiha ma'lumotlari → maydonlar

| Loyiha (.project) | `.ocm` |
|---|---|
| `project/@name` + CS material `good/@name` | fayl nomi va `JobName` (bo'shliqlar → `_`) |
| `tool.cutting/@swSawthick` | `PanelInfo/@BladeThickness` |
| material `good/@t` | `PanelInfo/@Thickness` |
| ishlatilgan list (`sheet` part `l,w`, qoldiq bo'lsa uning `l,w`) | `PanelInfo/@Length,@Width` (sxema yo'nalishiga qarab almashgan bo'lishi mumkin) |
| (doimiy 5) — `cTrimL/cTrimW=2` **ishlatilmagan** | `PanelInfo/@TrimSize` |
| detal `part/@l`, `@w` (= `cl`,`cw`, kesish o'lchami; kromka/prifugovka hisobga olingan) | barg `Entry` lar juftligi (`Distance` lar) |
| detal `part/@count` | barglar soni (Quantity·ota Quantity·PanelInfo Quantity) yig'indisi |
| nom, kod, kromka (`elt…`), `txt` (tola) | **yozilmaydi** |

**Muhim:** barglar o'lchami `l/w` (= `dl/dw` bu loyihalarda) ga teng, **`jl/jw` ga emas** — masalan
`01.001 bok`: `l=2000 w=350 jl=2000 jw=349` → `.ocm` da 2000×350. Ya'ni stanokka pilniy (kesish)
o'lchami beriladi.

### 4.1 Tekshiruv natijalari (detal to'plami, o'lchamlar multimnojestvosi bo'yicha)

| `.ocm` (anonim) | Mos loyiha / CS | Detal soni (.ocm / loyiha) | Farq |
|---|---|---|---|
| 2027_mijoz_LDSP_UD_ | `2027 mijoz.project`, LDSP UD | 73 / 73 | 0 |
| 2027_mijoz_XDF… | `2027 mijoz.project`, XDF | 4 / 4 | 0 |
| 2028_mijoz_LDSP_OQ_GLYANETS | `2028_mijoz.project` | 23 / 23 | 0 |
| 2029_mijoz_LDSP_METALIK_SHAGREN | `2029_mijoz.project` | 16 / 16 | 0 |
| 2029_mijoz_Ldsp_oq | `2029_mijoz.project` (qoldiq list 2750×1160) | 23 / 23 | 0 |
| 2030_mijoz_LMDF… | `01 Shkaf` + `02 Servant` loyihalari birgalikda | 35 / 17+18 | 0 |
| 2030_mijoz_XDF… | `2030_mijoz.project` | 5 / 5 | 0 |
| 2030_mijoz_LDSP… | `2030_mijoz.project` | 34 / 33 | +1 dona 600×2028 (keyingi versiyada LMDF ga ko'chirilgan) |
| 2031_mijoz_LDSP…, 2031_mijoz_XDF… | `2031 mijoz.project` | 47/47, 8/8 | 0 |
| 2032_mijoz_* (3 fayl) | aniq versiya papkada yo'q | 249, 37, 9 | loyiha versiyasi topilmadi |

### 4.2 Aniq misollar

**(a) 2028, LDSP OQ GLYANETS** (detallar: `00.001 pol` 770×1820 ×3; `01.001 bok` va `01.002 bok`
2000×350 ×5 dan; `01.005 tom` 738×350 ×6; `02.003 tom` 868×350 ×4; 3 list):
```xml
<PanelInfo BladeThickness="3" Length="1830" Quantity="1" Thickness="16" TrimSize="5" Width="2750"/>
<Pattern>
  <Entry Distance="1820" Quantity="1">          <!-- polosa 1820 (1830 − 2×5), uzunligi 2750 -->
    <Entry Distance="770" Quantity="1"/>        <!-- 00.001 pol 770×1820 -->
    <Entry Distance="350" Quantity="1">         <!-- 350 enli bo'lak -->
      <Entry Distance="868" Quantity="2"/>      <!-- 02.003 tom 868×350 ×2 (3-daraja) -->
    </Entry>
    <Entry Distance="770" Quantity="2"/>        <!-- 00.001 pol ×2 -->
  </Entry>
</Pattern>
<PanelInfo ... Length="2750" Width="1830" .../>
<Pattern>
  <Entry Distance="2000" Quantity="1"><Entry Distance="350" Quantity="5"/></Entry>  <!-- 01.001 bok ×5 -->
  ...
```
Jami: 3 + 5 + 5 + 6 + 4 = 23 = loyiha. `.CUT` dagi 3 ta `Layout` bilan geometriya 1:1 bir xil.

**(b) 2029, LDSP METALIK SHAGREN**: 1 list, `Length=2750`. Polosa `1442` ichida `500` (q=1) →
`704`,`704` (ikki **turli** qator `01_002 pb-bok` va `01_003 pb-bok`, shuning uchun Quantity=2 emas);
`397` → `717`,`717` (`02_005 Fasad` ning ikki qatori). Barglar 16 ta = loyiha 16.

**(c) 2030, XDF 2800×2070 (t=3)**: `01_017 XDF ort` 2059×1139 count=2 →
`<Entry Distance="1139" Quantity="2"><Entry Distance="2059" Quantity="1"/></Entry>`;
`01_021 XDF ort` 1879×599 count=2 → `<Entry Distance="599" Quantity="2">…1879…`. `Thickness="3"`.

**(d) 2029, Ldsp oq (qoldiq listda)**: `PanelInfo Length="2750" Width="1160"` — loyihadagi
`sheet l=2750 w=1160 count=1 usedCount=1` qoldig'i. 23 detal.

### 4.3 `.CUT` (NXCutSaw) bilan solishtirish

`.CUT` daraxtini `.ocm` ga o'girish qoidasi: `Layout` ning yuqori `Part` lari `Py=0` bo'lsa →
`Length=X`, aks holda `Length=Y`; har darajada `Distance` = navbat bilan `X`/`Y`; `Spare="True"`
tashlanadi; `Grouped="N"` → oldingi N−1 bo'lak bilan birlashtirib `Quantity=N`. Natija:
**6 ta faylda 100 % bir xil** (2027 XDF, 2028, 2029 ×2, 2031 XDF, 2032 KASHMIR). Qolgan 5 tasida
(2027 LDSP, 2030 LDSP/LMDF, 2031 LDSP, 2032 DUB) birinchi polosadanoq butunlay boshqa sxema — ya'ni
`.ocm` keyinroq qayta optimallashtirilgan natijadan chiqarilgan (list soni bir xil, joylashuv boshqa).
Demak `.ocm` va `.CUT` bitta kroy natijasining ikki xil serializatsiyasi.

---

## 5. Minimal qayta tiklangan misol

Material «LDSP TEST», 16 mm, list 2750×1830, kerf 3, torsovka 5. Detallar: `A` 1000×500 ×2 (bitta
qator), `B` 600×400 ×1. Bitta list:

```xml
<ManualPattern JobName="9999_mijoz_LDSP_TEST"><PanelInfo BladeThickness="3" Length="2750" Quantity="1" Thickness="16" TrimSize="5" Width="1830"/><Pattern><Entry Distance="1000" Quantity="1"><Entry Distance="500" Quantity="2"/><Entry Distance="400" Quantity="1"><Entry Distance="600" Quantity="1"/></Entry></Entry></Pattern></ManualPattern>
```
Fayl nomi: `9999_mijoz_LDSP_TEST.ocm`, bitta qator, `\n` siz, ASCII.
Tekshiruv: 1-daraja 5+1000 = 1005 ≤ 2750−5; 2-daraja 5+500+3+500+3+400 = 1411 ≤ 1830−5;
3-daraja 600 ≤ 1000−5.

Generator algoritmi (MebeliX `CutMap` dan):
1. Har bir material uchun fayl; har bir noyob karta uchun `PanelInfo`(+`Quantity` = shu kartadagi listlar).
2. Karta birinchi kesim yo'nalishiga qarab `Length`/`Width` ni tanlash.
3. Gilyotin daraxtini (polosa → bo'lak → qayta kesish) chuqurlikdan birinchi aylanib chiqish;
   chiqindi bo'laklarni tashlash; ketma-ket bir xil (bir xil detal qatori + bir xil ichki sxema)
   bo'laklarni `Quantity` ga birlashtirish.
4. Atributlarni alifbo tartibida, bo'shliqsiz, bitta qatorga yozish.

---

## 6. Noaniqliklar va foydalanuvchiga savollar

1. **`TrimSize`** — torsovka faqat boshlang'ich chetdami yoki ikkala chetdami? (Namunalarda oxirida
   har doim ≥5 mm qoladi.) Va nega loyihadagi `cTrimL/W=2` emas, 5? Bu FastPanel postprotsessor
   sozlamasimi (o'zgartirish mumkinmi)?
2. 1-darajada polosa listning **butun** `Width` iga cho'ziladi deb hisoblanadimi (ya'ni stanok polosa
   uzunligini `Width − trim` deb oladimi)? Hozircha shunday talqin qilindi.
3. 3-darajadan chuqur (4-daraja, ya'ni 3 burilish) sxemalarni FastPanel qabul qiladimi? Namunalarda
   maksimal 3 daraja.
4. Kasr o'lchamlar (masalan 349.5) qanday yoziladi — nuqta bilanmi? Namunalarda faqat butun sonlar.
5. Kirill harfli material/loyiha nomlari `JobName` va fayl nomida qanday kodlanadi (UTF-8 yoki
   transliteratsiya)? Namunalarda faqat lotin.
6. `.ocm` ni stanok qanday nomlaydi/import qiladi — `JobName` fayl nomi bilan mos bo'lishi shartmi?
7. Pachka (kitob) balandligi / bir vaqtda kesiladigan listlar soni stanokda qo'lda kiritiladimi?
   (Faylda yo'q.)
8. `2033`–`2037` buyurtmalari uchun FastPanel fayllari nima uchun yo'q (stanok ishlatilmaganmi)?
9. 2032 buyurtmasi uchun `.ocm` yaratilgan aniq loyiha versiyasi papkada yo'q — kerak bo'lsa bering.
10. Ketma-ket bir xil kartalar (2032 XDF) birlashtirilmagani stanokka farq qiladimi? Biz
    `Quantity` bilan birlashtirsak bo'ladimi?
