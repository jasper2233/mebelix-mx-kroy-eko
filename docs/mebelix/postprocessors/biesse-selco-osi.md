# Biesse Selco OSI — postprotsessor formati (teskari hujjatlash)

> Manba: `post prtsessorlar/PILNIY APPARAT/Biesse Selco OSI/*.xml` — 14 ta fayl (buyurtmalar 3167, 3168, 3169, 3170, 3171, 3173, 3174, 3175, 3177, 3178, 3179, 3180, 3181, 3182) va mos `giblab project/3 Eldor/<NNNN> <mijoz>/<NNNN>_<mijoz>.project`.
> Mijoz ismlari «mijoz» bilan almashtirilgan. Faqat namuna chiqish fayllari va kompaniyaning `.project` XML fayllari o'qilgan.
> 12 ta buyurtma uchun **NC300** namunasi ham bor — kesish dasturlari 64/64 patternda bir xil (qarang: `biesse-selco-nc300.md`).

**Tushunish darajasi: qisman-yuqori.** Tuzilma, barcha maydonlar va loyiha bilan bog'lanish to'liq tasdiqlangan (14/14 fayl bayt-baayt qayta serializatsiya qilindi; 696 ta detal × 30+ atribut loyiha bilan 100 % mos). **Noma'lum:** oxirgi `Cut@Chk` nazorat summasi algoritmi va `TechnoParam` ID 320–335 ma'nosi.

---

## 1. Chiqadigan fayllar

| Xususiyat | Qiymat |
|---|---|
| Fayl | bitta `.xml` har bir buyurtma × material uchun |
| Nomi | `<loyiha nomi>_<material nomi, bo'shliq va maxsus belgilar → "_">.xml`, masalan `3169_<mijoz>_LDSP_METALIK_SHAGREN_5.03_kv.xml`, `3181_<mijoz>_LDSP_UD_110197__diffuseOriginal.xml` (`(`, `)` → `_`, nuqta saqlanadi) |
| Kodlash | UTF-8, BOM yo'q, deklaratsiya `<?xml version="1.0" encoding="UTF-8"?>` |
| Qator oxiri | **yo'q** — butun hujjat bitta qatorda, elementlar orasida bo'sh joy yo'q |
| O'nlik ajratgich | nuqta; `Part@L/W` va `ThkEdge*` — 1 xona (`1400.0`), `Cut@L`, `Piece@L/W` — 2 xona (`1400.00`) |
| Birlik | mm |
| Atributlar tartibi | har elementda **ASCII bo'yicha saralangan** (katta harflar avval: `Code, Desc1, …, W, id, qMin`) — 6409/6409 element |
| Bo'sh elementlar | `<X …/>` (`/>` dan oldin bo'shliq yo'q) |

---

## 2. To'liq tuzilma

```
Order(Code, Comment)
└─ WorkList(Code, Comment, Due, MaterialID, Released)
   ├─ Part × P            (detal turlari, CS operatsiya tartibida)
   ├─ GibLabPart × P(+R)  (har detal uchun etiketka ma'lumoti; +R qoldiq)
   ├─ Job × J             (har pattern/kesish kartasi)
   │  ├─ TechnoParam × 16
   │  ├─ Board
   │  └─ Program
   │     └─ Cut × K
   └─ Piece × Q           (kesiladigan bo'lak turlari)
      ├─ Pid × ≥1
      └─ Sid × ≥1
```
Element guruhlari tartibi qat'iy: avval barcha `Part`, keyin barcha `GibLabPart`, keyin `Job`, oxirida `Piece` (14/14).

### 2.1 `Order`
| Atribut | Misol | Ma'no |
|---|---|---|
| `Code` | `08.09.2026` | loyiha sanasi `dd.MM.yyyy` (`Due` ning sana qismi) |
| `Comment` | `6a29f6d3-…` | UUID — har eksportda yangi (loyiha `project.uuid` ga **teng emas**); hamma `Job@Comment` da takrorlanadi |

### 2.2 `WorkList`
| Atribut | Misol | Ma'no |
|---|---|---|
| `Code` | `3171_<mijoz>_LDSP_DUB_VATAN_TEKSTURA` | fayl nomi (kengaytmasiz) |
| `Comment` | `""` | doim bo'sh |
| `Due` | `2026-09-08 08:56:10` | loyiha `project@date` (ms) — `yyyy-MM-dd HH:mm:ss`; namunada UTC+2 ko'rinishida (savol 4) |
| `MaterialID` | `1` | doimiy |
| `Released` | `2026-09-27 16:13:22` | eksport vaqti (xuddi shu vaqt zonasi) |

### 2.3 `Part` (749 ta) — detal turi

| Atribut | Tur / qiymatlar | Manba (loyiha) | Doimiy? |
|---|---|---|---|
| `Code`, `PartNo` | int, 1..P | detalning CS operatsiyadagi tartib raqami (`indexInOperation`) | ma'lumot |
| `id` | `P<n>` | `"P" + part@id` (loyiha detal id si; `Code` bilan teng bo'lmasligi mumkin) | ma'lumot |
| `Desc1` | `01 shkaf` | `good(product)@name` | ma'lumot |
| `IDesc` | `01_012 polka` | `part@name` | ma'lumot |
| `IIDesc` | `3168 mijoz` | `good(product)@product.order` | ma'lumot |
| `L`, `W` | `852.0`, `287.0` | `part@l`, `part@w` (namunada `l=cl=dl`) | ma'lumot |
| `qMin` | int | `part@count` | ma'lumot |
| `QMax` | `0` | — | doimiy |
| `Grain` | `0/1` | `part@txt="true"` → `1` | ma'lumot |
| `Material` | `LDSP KASHMIR SHAGREN` | sheet `good@name` | ma'lumot |
| `ThkEdgeUp / Lo / L / R` | `0.0` / `1.0` | `elt / elb / ell / elr` → EL operatsiya → band `good@t`; kromka yo'q bo'lsa `0.0` (har doim yoziladi) | ma'lumot |
| `TypEdgeUp / Lo / L / R` | `A…E` | EL operatsiya `elSymbol`; kromka yo'q bo'lsa **atribut yo'q** | ma'lumot |
| `MatEdgeUp / Lo / L / R` | `1-19 kashmir` | band `good@name`; kromka yo'q bo'lsa atribut yo'q | ma'lumot |
| `DrillBarCode2` | `316801_01_001` | shu detalning `XNC` operatsiyasi (`side="true"`, yuz tomoni) `@code`; XNC yo'q bo'lsa atribut yo'q | ma'lumot |
| `DrillBarCode3` | `316701_01_018_2` | ikkinchi (`side="false"`, orqa tomon) XNC `@code` — faqat bor bo'lsa | ma'lumot |
| `DrillCode3` | `true/false` | orqa tomon XNC bo'lsa `false`, aks holda `true` (22/22) | ma'lumot |
| `DrillCode2, 4, 5, 6`, `DrillInfo2..6` | `true` | — | doimiy |
| `EvDate` | `2026-09-27` | eksport sanasi | ma'lumot |
| `Finish` | `S` | — | doimiy |
| `Prio` | `100` | — | doimiy |

### 2.4 `GibLabPart` (755 ta)
`ID="P<n>"` — `Part@id` bilan bir xil; `data` — **NC300 `B_LABEL` dagi #30 maydon bilan bayt-baayt bir xil** blob (base64(zlib(level 6)) ichida 147 kalitli tipli xarita + SVG eskiz; to'liq tavsif — `biesse-selco-nc300.md` §2.2). 692/692 juftlikda aynan teng.
Qoldiq (biznes-qoldiq) uchun qo'shimcha `GibLabPart ID="D<part.id>"` (6 faylda, `waste=true, business=true`, mos `Part` elementi **yo'q**), masalan `D71` → 2740×562.

### 2.5 `Job` (80 ta) — pattern
| Atribut | Misol | Ma'no |
|---|---|---|
| `Code` | `<WorkList@Code>.001` | 3 xonali tartib raqami |
| `Comment` | UUID | `Order@Comment` bilan bir xil |
| `ExeOrder` | 1..J | bajarish tartibi (= `Board@id`) |
| `QBoards`, `ToWork` | `1`, `2` | shu patterndan kesiladigan listlar soni (ikkalasi teng) |
| `Type` | `PROGRAM` | doimiy |
| `Worked` | `0` | doimiy |

`TechnoParam` (16 ta, hammasida bir xil): `320=0, 321=500, 322=500, 323=500, 324=0, 325=500, 326=500, 327=500, 328=0, 329=500, 330=500, 331=500, 332=0, 333=500, 334=500, 335=500` — 4 ta `(0, 500, 500, 500)` guruh; NC300 dagi `B_REF` (`FORZ=0`, trimlar = 500 = 5.00 mm) ga o'xshash. Aniq ma'nosi noma'lum (savol 2).

`Board`:
| Atribut | Misol | Ma'no |
|---|---|---|
| `Code` | `B11`, `B12`, …, `B19`, `B110`, `B111` | `"B1" + id` (80/80; ehtimol `"B" + MatNo + id`) |
| `id` | 1..J | = `ExeOrder` |
| `L`, `W` | `2750`, `1830` (qoldiq listlar: `2570×1200`, `2750×1245`, `2440×750`, `600×530`, `1810×534`, `2750×450`) | list o'lchami, butun mm |
| `Thickness` | `16` | qalinlik, butun mm |
| `MatCode` | material nomi | sheet `good@name` |
| `MatNo` | `1` | doimiy |
| `Grain` | `1` | doimiy (tola list uzunligi bo'ylab) |

`Program/Cut`:
| Atribut | Ma'no |
|---|---|
| `id` | 1..K tartib raqami |
| `Code` | `1`, `2`, `4`, `5`, `Z1`, `Z2`, `Z3`, `Z4` — NC300 dagi `COD` bilan bir xil (daraja/o'q qoidasi o'sha yerda) |
| `L` | sof detal/tasma o'lchami, mm, 2 xona |
| `Rep` | takrorlash (pastki daraxt bilan) |
| `Chk` | **faqat oxirgi `Cut` da**, butun son (3440…120972) — nazorat summasi, algoritmi topilmadi (savol 1) |

Kod statistikasi: `Z1` 508, `2` 352, `5` 257, `1` 130, `Z2` 141, `4` 98, `Z3` 9, `Z4` 2 (Z3/Z4 — `swMaxturns=6` bo'lgan 3167, 3181 da).

### 2.6 `Piece` (480 ta) — kesiladigan bo'lak turi
| Atribut/bola | Ma'no |
|---|---|
| `N` | 1..Q ketma-ket |
| `L`, `W` | bo'lakning listdagi o'lchami (X = list uzunligi bo'ylab, Y), 2 xona. Tolasiz bo'lak boshqa patternda 90° burilgan holda kesilishi mumkin (32 ta job), ya'ni `L/W` — kanonik yo'nalish; tolali bo'laklarda har doim `L = cl` (81/81) |
| `G="1"` | faqat tolali bo'laklarda (aks holda atribut yo'q) |
| `Q`, `qMin` | jami soni (= Σ `Pid` detallarning `qMin`) |
| `Pid id="P<n>"` | shu o'lchamdagi detallar (bir xil kesish o'lchamli bir nechta loyiha detali bitta `Piece` ga birlashadi; 749 `Pid` / 480 `Piece`) |
| `Sid id="<Job@Code>" qP<n>="k"` | qaysi jobda shu detaldan nechta (k = listdagi nusxa × `QBoards`); bitta `Sid` da bir nechta `qP*` bo'lishi mumkin |

---

## 3. Kesish rejasi qanday kodlangan

- **List:** `Job/Board` (o'lcham, material); `QBoards` — nechta list. Loyihadagi `cMaterialCount` = Σ`QBoards` (14/14).
- **Kesish daraxti:** `Program/Cut` — preorder ro'yxat, daraja kod bilan: `1`/`4` (1-daraja; X yoki Y bo'ylab), `2`/`5` (2-daraja), `Z1`, `Z2`, … (o'q navbatma-navbat). Ota-ona — oldingi bir daraja yuqori yozuv; barg = detal; `Rep` pastki daraxt bilan takror. Trim (5 mm) va arra (3 mm) faylda yo'q.
- **`Rep` birlashtirish qoidasi (NC300 dan farqi):** OSI ketma-ket bir xil bargni faqat **bir xil detal** bo'lsa birlashtiradi. Ketma-ket bir xil, lekin birlashtirilmagan 130 barg hammasi shu o'lchamda ≥2 xil detal bor joylarda (`01_008 bok` ning 2 ta loyiha qatori — `Z1:317, Z1:317`); NC300 esa `Z1:317 QTA=2` yozadi. Pastki daraxtli tugunlar ham ba'zan birlashtiriladi (19), ba'zan yo'q (26). Rep yoyilgandan keyin OSI = NC300 (64/64).
- **Detal ↔ kesish bog'lanishi:** to'g'ridan-to'g'ri yo'q; faqat o'lcham orqali: `Piece(L,W)` + `Sid@qP*`. Tekshiruv: har bir job uchun daraxtdan chiqqan bo'laklar (× `QBoards`) multiset'i = shu jobga tegishli `Sid` miqdorlari (o'lcham burilishini hisobga olganda) — **80/80**.
- **Qoldiq:** faqat `GibLabPart ID="D…"` (etiketka) sifatida.
- **Etiketka:** `GibLabPart@data`.

Hisob-kitob tekshiruvi:

| Buyurtma | Material | Job | ΣQBoards | loyiha cMaterialCount | Part | Σ qMin | daraxtdan bo'lak | loyiha cPartCount | Piece | Cut | GibLabPart |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 3167 | LDSP KASHMIR SHAGREN | 11 | 13 | 13 | 82 | 117 | 117 | 117 | 49 | 161 | 82 |
| 3168 | LDSP KASHMIR SHAGREN | 8 | 9 | 9 | 67 | 90 | 90 | 90 | 48 | 127 | 68 |
| 3169 | LDSP METALIK SHAGREN 5.03 kv | 4 | 4 | 4 | 82 | 104 | 104 | 104 | 44 | 147 | 82 |
| 3170 | LDSP KASHMIR SHAGREN | 2 | 2 | 2 | 32 | 40 | 40 | 40 | 29 | 65 | 32 |
| 3171 | LDSP DUB VATAN TEKSTURA | 2 | 4 | 4 | 6 | 28 | 28 | 28 | 6 | 17 | 6 |
| 3173 | LDSP KASHMIR SHAGREN | 9 | 10 | 10 | 53 | 77 | 77 | 83* | 36 | 111 | 54 |
| 3174 | LDSP KASHMIR SHAGREN | 10 | 11 | 11 | 70 | 112 | 112 | 112 | 45 | 155 | 70 |
| 3175 | LDSP KASHMIR SHAGREN | 3 | 4 | 4 | 14 | 32 | 32 | 32 | 8 | 27 | 15 |
| 3177 | LDSP KAPUCHINO | 4 | 4 | 4 | 74 | 87 | 87 | 87 | 44 | 137 | 75 |
| 3178 | LDSP LIZA BEJIVIY | 3 | 3 | 3 | 15 | 30 | 30 | 30 | 9 | 31 | 15 |
| 3179 | LMDF OQ GLYANETS | 6 | 6 | 6 | 84 | 104 | 104 | 104 | 49 | 155 | 85 |
| 3180 | LDSP DUB VATAN TEKSTURA | 5 | 5 | 5 | 51 | 69 | 69 | 69 | 40 | 122 | 51 |
| 3181 | LDSP UD (110197)_diffuseOriginal | 5 | 5 | 5 | 37 | 69 | 69 | 69 | 25 | 79 | 38 |
| 3182 | LDSP KASHMIR SHAGREN | 8 | 9 | 9 | 82 | 117 | 117 | 117 | 48 | 163 | 82 |

\* 3173 `.project` fayli eksportdan keyin tahrirlangan (5 detal qo'shilgan, nomlar siljigan); boshqa 13 buyurtmada 696 ta detalning **barcha** maydonlari loyiha bilan mos.

---

## 4. Loyiha → fayl xaritasi

| Loyiha | OSI |
|---|---|
| `project@name` + material nomi | fayl nomi, `WorkList@Code`, `Job@Code` prefiksi |
| `project@date` | `Order@Code` (sana), `WorkList@Due` |
| CS operatsiya sheet `good@name / l / w / t` (yoki qoldiq list) | `Part@Material`, `Board@MatCode/L/W/Thickness` |
| CS op `part` ro'yxatidagi tartib | `Part@Code/PartNo` |
| `part@id` | `Part@id = "P"+id`, `Pid`, `qP<id>` |
| `part@name / l / w / count / txt` | `IDesc / L / W / qMin / Grain` |
| `part@cl / cw` | `Cut@L` (barglar), `Piece@L/W` |
| `good(product)@name / product.order` | `Desc1 / IIDesc` |
| `el{t,b,l,r}` → EL `elSymbol`, band `name`, `t` | `TypEdge{Up,Lo,L,R}`, `MatEdge*`, `ThkEdge*` |
| XNC operatsiya `code` (`side=true` / `false`) | `DrillBarCode2` / `DrillBarCode3` (+`DrillCode3=false`) |
| Optimizator natijasi | `Job`, `Program`, `Piece`, `Sid` |

### Tekshirilgan misollar

**A. 3171, `01_001 oldi bok`** (loyiha: id 1, `l=1400 w=1750 count=2 txt=true`, 4 tomon `A`, band `1-19 dub votan` t=1):
`<Part Code="1" Desc1="01 parta" … Grain="1" IDesc="01_001 oldi bok" IIDesc="3171 mijoz" L="1400.0" MatEdgeL="1-19 dub votan" … ThkEdgeUp="1.0" TypEdgeUp="A" W="1750.0" id="P1" qMin="2"/>`;
`<Piece G="1" L="1400.00" N="4" Q="2" W="1750.00" qMin="2"><Pid id="P1"/><Sid id="…001" qP1="2"/></Piece>`; `Job …001 QBoards="2"`: `Cut Code="1" L="1400.00"` → `Cut Code="2" L="1750.00"` (1/list × 2 = 2 ✓).

**B. 3168, `01_012 polka`** (id 15, `852×287`, `count=8`, faqat `elb`): `Part Code="15" id="P15" Grain="0" ThkEdgeLo="1.0" TypEdgeLo="A" MatEdgeLo="1-19 kashmir" ThkEdgeUp/L/R="0.0" qMin="8"` (DrillBarCode2 yo'q — XNC yo'q).
`Piece L="287.00" W="852.00" Q="8"`, `Sid …003 qP15="4"`, `Sid …001 qP15="4"`. Job 001 (`QBoards=2`): `4:852 → 5:287 Rep=2` (2×2=4); Job 003: `4:1202 → 5:852 → Z1:287 Rep=4` (bo'lak 852×287 — burilgan) ✓.

**C. 3178, `01_008 Fasad`** (id 8, `2354×546`, `count=1`, `txt=true`, XNC `317801_01_008`): `Part Code="1" id="P8" DrillBarCode2="317801_01_008" Grain="1" L="2354.0" W="546.0"`. Bir xil o'lchamli `01_009`-dagi boshqa detal (P9) bilan bitta `Piece G="1" L="2354.00" W="546.00" Q="2"` ga birlashgan: `Pid P9, P8`; `Sid …002 qP9="1"`, `Sid …003 qP8="1"` ✓.

**D. 3167, ikki tomonlama XNC:** `01_018 bok` — loyihada `XNC code="316701_01_018" side="true"` va `code="316701_01_018_2" side="false"` → `DrillBarCode2="316701_01_018" DrillBarCode3="316701_01_018_2" DrillCode3="false"`.

---

## 5. Minimal qayta tiklangan namuna (anonim, 1 detal turi, 1 pattern)

(Haqiqiy faylda hammasi **bitta qatorda**; bu yerda o'qish uchun bo'lingan.)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Order Code="08.09.2026" Comment="00000000-0000-4000-8000-000000000001">
 <WorkList Code="9001_mijoz_LDSP_DUB_VATAN_TEKSTURA" Comment="" Due="2026-09-08 08:56:10" MaterialID="1" Released="2026-09-27 16:13:22">
  <Part Code="1" Desc1="01 parta" DrillCode2="true" DrillCode3="true" DrillCode4="true" DrillCode5="true" DrillCode6="true"
        DrillInfo2="true" DrillInfo3="true" DrillInfo4="true" DrillInfo5="true" DrillInfo6="true" EvDate="2026-09-27"
        Finish="S" Grain="1" IDesc="01_001 oldi bok" IIDesc="9001 mijoz" L="1400.0"
        MatEdgeL="1-19 dub votan" MatEdgeLo="1-19 dub votan" MatEdgeR="1-19 dub votan" MatEdgeUp="1-19 dub votan"
        Material="LDSP DUB VATAN TEKSTURA" PartNo="1" Prio="100" QMax="0"
        ThkEdgeL="1.0" ThkEdgeLo="1.0" ThkEdgeR="1.0" ThkEdgeUp="1.0"
        TypEdgeL="A" TypEdgeLo="A" TypEdgeR="A" TypEdgeUp="A" W="1750.0" id="P1" qMin="2"/>
  <GibLabPart ID="P1" data="eJyt…(base64 zlib xarita, NC300 hujjatidagi enc_map)…"/>
  <Job Code="9001_mijoz_LDSP_DUB_VATAN_TEKSTURA.001" Comment="00000000-0000-4000-8000-000000000001" ExeOrder="1" QBoards="2" ToWork="2" Type="PROGRAM" Worked="0">
   <TechnoParam ID="320" Value="0"/><TechnoParam ID="321" Value="500"/><TechnoParam ID="322" Value="500"/><TechnoParam ID="323" Value="500"/>
   <TechnoParam ID="324" Value="0"/><TechnoParam ID="325" Value="500"/><TechnoParam ID="326" Value="500"/><TechnoParam ID="327" Value="500"/>
   <TechnoParam ID="328" Value="0"/><TechnoParam ID="329" Value="500"/><TechnoParam ID="330" Value="500"/><TechnoParam ID="331" Value="500"/>
   <TechnoParam ID="332" Value="0"/><TechnoParam ID="333" Value="500"/><TechnoParam ID="334" Value="500"/><TechnoParam ID="335" Value="500"/>
   <Board Code="B11" Grain="1" L="2750" MatCode="LDSP DUB VATAN TEKSTURA" MatNo="1" Thickness="16" W="1830" id="1"/>
   <Program>
    <Cut Code="1" L="1400.00" Rep="1" id="1"/>
    <Cut Chk="?????" Code="2" L="1750.00" Rep="1" id="2"/>
   </Program>
  </Job>
  <Piece G="1" L="1400.00" N="1" Q="2" W="1750.00" qMin="2"><Pid id="P1"/><Sid id="9001_mijoz_LDSP_DUB_VATAN_TEKSTURA.001" qP1="2"/></Piece>
 </WorkList>
</Order>
```
`Chk` qiymatini hisoblash usuli noma'lum — mashina uni tekshiradimi, aniqlash kerak (savol 1).

Generator uchun serializatsiya qoidasi (14/14 faylda bayt-baayt tasdiqlangan): `'<?xml version="1.0" encoding="UTF-8"?>' + ser(root)`, bu yerda `ser(e) = "<tag" + Σ' k="esc(v)"' (k bo'yicha saralangan) + ("/>" agar bola yo'q, aks holda ">" + bolalar + "</tag>")`, `esc`: `& < > "`.

---

## 6. Noma'lum / noaniq joylar — savollar

1. **`Cut@Chk`** — oxirgi kesishdagi nazorat summasi qanday hisoblanadi? (Chiziqli yig'indilar, bayt yig'indilari, CRC16/32 sinab ko'rildi — mos kelmadi.) Selco OSI uni tekshiradimi yoki atributsiz/0 bilan qabul qiladimi? Iloji bo'lsa, Biesse hujjati yoki mashinada sinov.
2. **`TechnoParam` 320–335** — har birining ma'nosi (trim, kuch, …)? Har doim shu 16 qiymatmi yoki material/qalinlikka qarab o'zgaradimi?
3. **`Rep` birlashtirish** — mashina uchun farqi bormi? (Masalan har bir `Rep>1` etiketka chop etish tartibiga ta'sir qiladimi.) Har doim NC300 kabi to'liq birlashtirish yoki har doim `Rep=1` yozish mumkinmi?
4. **Vaqt zonasi:** `Due`/`Released` namunada mahalliy vaqtdan 3 soat orqada (UTC+2) — mahalliy vaqt yozilsa muammo bo'ladimi?
5. **`Order@Comment` UUID** — tasodifiy bo'lishi yetarlimi yoki loyiha `project.uuid` bo'lishi kerakmi?
6. **`GibLabPart@data`** — OSI uni ishlatadimi (etiketka printeri)? Majburiy bo'lmasa, element/atributni tashlab ketish mumkinmi? (Mashina tomonidagi etiketka shabloni nimani o'qiydi?)
7. **`Piece@N` va `Sid` tartibi** — qanday tartiblangan (namunada aniq qoida topilmadi)? Tolasiz bo'lakning kanonik `L/W` yo'nalishi qanday tanlanadi?
8. **Kirill harflari** — material/detal nomlarida kirill bo'lsa UTF-8 da to'g'ri ko'rsatiladimi (namunada faqat lotin)?
9. **`Board@Code`** — namunada `"B1" + id` (3167 da `B19`, `B110`, `B111` — tasdiqlangan). Bu `"B" + MatNo + id` emasmi (MatNo doim 1)? Bir faylda bir nechta material bo'lsa `MatNo`/`MaterialID` qanday raqamlanadi?
