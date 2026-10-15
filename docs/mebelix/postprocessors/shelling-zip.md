# Shelling (Schelling) — `.l.zip` (NCL/NCP formati)

Manba namunalar: `post prtsessorlar/PILNIY APPARAT/Shelling/` — 14 ta zip (buyurtmalar 3167–3182; 3172, 3176 yo'q).
Solishtirilgan loyihalar: `giblab project/3 Eldor/<NNNN> <mijoz>/<NNNN>_<mijoz>.project`.

**Tushunish darajasi: to'liq (kesish rejasi va detal ma'lumotlari uchun).** 14 namunaning hammasida
detal soni, kesish daraxti geometriyasi va qoldiqlar (ostatok) tekshirildi — xatosiz yopiladi.
Ochiq qolganlar — doimiy (o'zgarmagan) maydonlar ma'nosi va `GibLabData.*.xml` (yorliq ma'lumoti) kerakligi (pastda §6).

---

## 1. Chiqadigan fayllar

| Xususiyat | Qiymat |
|---|---|
| Fayl nomi | `<loyiha nomi>_<list materiali nomi>.l.zip`, masalan `3171_mijoz_LDSP_DUB_VATAN_TEKSTURA.l.zip`. Material nomidagi bo'sh joylar `_` ga almashtiriladi (`LDSP UD (110197)_diffuseOriginal` → `LDSP_UD_110197__diffuseOriginal` — qavslar tozalanadi, aniq qoida savol ostida). |
| Soni | **Bitta buyurtma × bitta list materiali = bitta zip.** Bir zip ichida faqat bitta material (bir xil qalinlik) bo'ladi, lekin bir nechta list o'lchami (yangi list + qoldiq listlar) bo'lishi mumkin. |
| Zip ichidagi papkalar | Yo'q — hamma fayllar ildizda. |
| Zip ichidagi fayllar | `0000.ncl` — ish (job) fayli: listlar ro'yxati + detallar ro'yxati. `0001.ncp … NNNN.ncp` — har bir kesish kartasi (pattern) uchun alohida fayl, 4 xonali raqam, 1 dan boshlab ketma-ket. `GibLabData.<GibLabID>.xml` — yorliq (etiketka) ma'lumotlari (§2.5). |
| Kodlash | `.ncl`/`.ncp` — sof ASCII (namunalarda 0x7F dan katta bayt yo'q). Kirill/lotin bo'lmagan belgilar uchun kodlash noma'lum (savol). `GibLabData` — UTF-8 XML. |
| Qator oxiri | `CRLF` (`\r\n`), oxirgi qatordan keyin ham `CRLF` bor. |
| O'nlik ajratgich | Ishlatilmaydi: barcha uzunliklar **mikron (mm × 1000) butun son**, nol bilan to'ldirilgan, 8 xona (`00584000` = 584,000 mm). Namunalarda hamma qiymat butun mm edi. |
| Format turi | Qat'iy **qat'iy kenglikdagi ustunlar** (fixed-width); maydonlar bitta bo'sh joy bilan ajratilgan, matnli maydonlar o'ngdan bo'sh joy bilan to'ldiriladi. |
| Zip vaqti | Zip yozuvlari vaqti = eksport vaqti (mahalliy soat). |
| Hajm | Zipning 90–95 % ini `GibLabData.xml` egallaydi (har bir detal uchun zlib+base64 blob + SVG chizma). `.ncl` 3–44 KB, `.ncp` 0,3–1,5 KB. |

### GibLabID
`S 01` qatorida, har bir `F 01` da va `GibLabData.<ID>.xml` nomida bir xil 20 belgili hex ID:
`891c 0000 01a0e33b80ab` → oxirgi 12 hex = eksport vaqti Unix-millisekundda (`0x01a0e33b80ab` = 2026-09-27 19:18:42.731),
birinchi 4 hex — tasodifiy/xesh, o'rtadagi `0000` doimiy. MebeliX o'zining noyob ID sini shu shaklda yasashi mumkin.

---

## 2. Tuzilma

Qatorning birinchi 4 belgisi yozuv turini bildiradi. Ustun raqamlari **1 dan** sanaladi.
`N8` = 8 xonali mikron qiymat; `Tn` = n belgili matn (o'ngdan bo'sh joy bilan to'ldirilgan, uzunroq bo'lsa kesiladi).

### 2.1 `0000.ncl` — yozuvlar tartibi

```
S 01 ...            (1 ta)  ish sarlavhasi
S 46 ...            (1 ta)  ishning to'liq nomi
B 01 ...            (1..n)  list (board) turlari
{ F 01 / P 09 / F 80 }  (har bir detal uchun 3 qator)
F 01 ... (kind=1)   (0..1)  qoldiq (Ostatok) — faqat qoldiq hosil bo'lsa, oxirida
S$                  tugash belgisi (literal "S$")
```

Statistika (14 namuna): `S 01`/`S 46`/`S$` — 14 tadan; `B 01` — 21; `F 01` — 755 (749 detal + 6 qoldiq);
`P 09` va `F 80` — 749 tadan (faqat detallarda, qoldiqda yo'q).

#### `S 01` — 67 belgi
| Ustun | Qiymat | Ma'nosi |
|---|---|---|
| 1–4 | `S 01` | yozuv turi |
| 6–8 | `001` | doimiy (savol: ish/kanal raqami?) |
| 10–12 | `001` | doimiy |
| 14–33 | T20 | zip nomining (`.l.zip` siz) birinchi 20 belgisi |
| 35–44 | `2026-09-27` | eksport sanasi `YYYY-MM-DD` |
| 46 | `0` | doimiy |
| 48–67 | T20 | GibLabID |

#### `S 46` — 75 belgi
`S 46 ` + T70 — ishning to'liq nomi (zip nomi `.l.zip` siz), 70 gacha to'ldirilgan.

#### `B 01` — list turi, 99 belgi
| Ustun | Misol | Ma'nosi |
|---|---|---|
| 1–4 | `B 01` | |
| 6–9 | `0001` | list indeksi (1..n), `P 01` shu raqamga murojaat qiladi |
| 11 | `0` | doimiy (barcha 21 yozuvda 0, hatto qoldiq-listlarda ham) |
| 13–32 | T20 | material nomi (list `good@name` ning birinchi 20 belgisi) |
| 34–41 | N8 | qalinlik (`00016000` = 16 mm) |
| 43–50 | N8 | list uzunligi L (tola/teksturaga parallel tomoni, odatda 2750) |
| 52–59 | N8 | list kengligi W |
| 61 | `0` | doimiy |
| 63–82 | T20 | material nomi takrori |
| 84, 86 | `0 0` | doimiy |
| 88–97 | `0000000001` | doimiy (savol: ombordagi soni? — loyihada 4 list ishlatilganda ham 1) |
| 99 | `0` | doimiy |

Bir nechta `B 01` bo'lishi mumkin: masalan 3181 da 5 xil list (2750×1830 yangi list va 2750×650, 600×530, 2440×750, 1810×534 qoldiq-listlar);
3174 da 2750×450 + 2750×1830. Ular `.project` dagi `good typeId="sheet"` ichidagi `<part l= w=>` (list variantlari) ga mos.
`B` yozuvlari tartibi loyihadagi tartibga to'liq mos emas — muhim emas, chunki bog'lanish indeks orqali.

#### `F 01` — detal, 312 belgi
| Ustun | Misol | Ma'nosi | Loyihadan manba |
|---|---|---|---|
| 1–4 | `F 01` | | |
| 6–9 | `0001` | detal indeksi (1..N, ketma-ket). `.ncp` dagi `C` yozuvlari shunga murojaat qiladi | CS operatsiyasidagi `<part id>` tartibi |
| 11–14 | `0001` | indeks takrori (namunalarda doim = 6–9) | |
| 16 | `0` | tur: `0` = detal, `1` = qoldiq (Ostatok) | |
| 18–23 | `000002` | kerakli soni | `part@count` |
| 25–30 | `000002` | soni takrori (doim teng) | `part@count` |
| 32–51 | T20 | material nomi (20 belgi) | list `good@name` |
| 53–60 | N8 | qalinlik | `sheet@t` |
| 62–69 | N8 | detal uzunligi L | `part@l` (=`cl`=`dl` namunalarda) |
| 71–78 | N8 | detal kengligi W | `part@w` |
| 80–87 | N8 | L takrori | `part@l` |
| 89–96 | N8 | W takrori | `part@w` |
| 98–117 | T20 | detal nomi (20 belgigacha kesiladi: `01_007 utalshonka pl #` → `01_007 utalshonka pl`) | `part@name` |
| 119 | `0`/`1` | **aylantirish ruxsati**: `0` = aylantirib bo'lmaydi (tekstura), `1` = mumkin | `part@txt="true"` → `0`, `false` → `1` |
| 121–150 | `9 9 0 00 000000 000 000000 000` | doimiy | — |
| 152 | `1` | doimiy `1` (qoldiqda `0`) — ehtimol "yorliq chop etilsin" | — |
| 154 | `0` | doimiy | — |
| 156–175 | T20 | 1-chi XNC (присадка) dastur nomi, bo'sh bo'lishi mumkin | `operation typeId="XNC" side="true"` ning `code` i (`<product code>_<part code>`, masalan `318101_01_002`) |
| 177–196 | T20 | 2-chi XNC dastur nomi (orqa tomon) | `side="false"` operatsiya `code` i (`318101_01_008_2`) |
| 197–237 | bo'sh | zaxira (namunalarda doim bo'sh) | — |
| 239, 241 | `1 0` | doimiy | — |
| 243–262 | T20 | GibLabID | — |
| 264–283 | T20 | buyum (product) nomi | `good typeId="product" @name` (masalan `01 shkaf`) |
| 285–293 | `000000001` | yorliq raqami = **loyihadagi `part@id`** (9 xona) | `part@id` |
| 295–304 | `2026.09.08` | loyiha sanasi `YYYY.MM.DD` | `project@date` (Unix ms) |
| 306, 308 | `0 0` | doimiy | — |
| 310–312 | `000` | doimiy | — |

Qoldiq (`kind=1`) `F 01` qatori **154 belgi** — 154-ustundan keyin hech narsa yo'q:
```
F 01 0001 0001 1 000001 000001 LDSP UD (110197)_dif 00016000 02333000 00740000 00000000 00000000 Ostatok              0 9 9 0 00 000000 000 000000 000 0 0
```
Qoldiq indekslari detallardan alohida, 1 dan sanaladi; L/W takrori `00000000`; nomi doim `Ostatok`; 119-ustun `0`; 152-ustun `0`.
Undan keyin `P 09`/`F 80` kelmaydi.

#### `P 09` — 45 belgi (har detaldan keyin)
`P 09 00000000 00000000 00000000 00000000 XXXX` — barcha 749 ta yozuvda bir xil (savol: ehtimol kesish qo'yimlari/allowance yoki chizma maydonlari).

#### `F 80` — kromka (edge) ma'lumoti, 159 belgi
| Ustun | Ma'nosi |
|---|---|
| 1–45 | `F 80 00000000 00000000 00000000 00000000 0000` — doimiy |
| 47–67 | 1-tomon (T21) = **`elb`** (pastki uzun tomon) |
| 68–88 | 2-tomon (T21) = **`elt`** (yuqori uzun tomon) |
| 89–109 | 3-tomon (T21) = **`ell`** (chap qisqa tomon) |
| 110–130 | 4-tomon (T21) = **`elr`** (o'ng qisqa tomon) |
| 131–159 | `00 00 00 00 00000000 00000000` — doimiy |

Har bir tomon matni: `(<elSymbol>) <t>` yoki bo'sh. `elSymbol` — kromka operatsiyasining (`operation typeId="EL" @elSymbol`, `A`,`B`,`C`,`D`,`E`) belgisi,
`<t>` — lenta qalinligi (`good typeId="band" @t`; barcha loyihalarda `t="1"`, shuning uchun bu "1" qalinlik ekanini to'liq tasdiqlab bo'lmadi — savol).
Tartib `elb, elt, ell, elr` 13 namunadagi 744 detalda xatosiz tasdiqlandi.

### 2.2 `NNNN.ncp` — kesish kartasi (pattern)

```
P 01 <pattern#4> <board#4> <runs6> 0 0 0000 0          (32 belgi)
P 02 01 0001 <runs4> 00000000 001                       (30 belgi)
P 03 00 0 00 00000000 <D1> <D2> <D1> <D2>                (57 belgi)
P 98 0 0 0                                               (10 belgi)
C ...   (kesish daraxti, 1..n qator)
P$                                                       (tugash belgisi)
```

| Maydon | Ma'nosi |
|---|---|
| `P 01` 6–9 | kesish kartasi raqami (= fayl raqami) |
| `P 01` 11–14 | `B 01` list indeksi |
| `P 01` 16–21 | **shu karta bo'yicha kesiladigan listlar soni** (runs). Namunalarda 1 yoki 2 |
| `P 02` 14–17 | runs takrori (4 xona). Namunalarda doim `P 01` runs ga teng. Ehtimol "paket (kitob) balandligi — bir paketdagi list soni" (`swPackageHeight=40` / 16 mm → maks 2). Savol. |
| `P 03` | `D1 D2` — list o'lchamlari, **birinchi kesish darajasi qaysi o'q bo'ylab ketishiga qarab tartiblangan**: `D1` — 1-daraja polosalari o'lchanadigan o'q. Ikkinchi juftlik namunalarda doim birinchisiga teng (savol: xom list va kesilgan list?) |
| `P 98 0 0 0` | doimiy, sarlavha tugashi |

#### `C` — kesish daraxti qatori (22 yoki 29 belgi)
```
C <ota3> <bola3> <o'lcham N8> <soni3>[ 0 <detal#4>]
  2-4     6-8      10-17        19-21     23  25-28
```
- **ota** — joriy bo'lak belgisi. Ildiz: `K01` yoki `L01`.
  - `K01` — `D1` = listning uzun tomoni (L): birinchi kesishlar listning kalta tomoniga parallel (ko'ndalang, "Kopfschnitt"/head-cut). 46 kartada `D1 > D2`.
  - `L01` — `D1` = listning qisqa tomoni (W): birinchi kesishlar uzunasiga (rip). 34 kartada `D1 < D2`.
  - Hamma 80 kartada: `K` ⇔ `P 03` da `D1 > D2`, `L` ⇔ `D1 < D2` (2750×450 list ham `L`).
- **bola** maydoni:
  - `T  ` — **torets/trim (kromka chetini kesish)**: `o'lcham` = trim kengligi (namunalarda doim `00005000` = 5 mm = `cTrimL/cTrimW` 2 mm + arra qalinligi `swSawthick` 3 mm). Faqat ildizda (`K01`/`L01`) va 1-darajadagi har polosada (`Xnn`) bitta-bittadan, birinchi qator sifatida.
  - `Xnn` — 1-daraja polosa (strip); `ann` — 2-daraja; `bnn` — 3-daraja; `cnn`, `dnn` — 4,5-daraja (namunalarda `d` gacha). Darajalar navbatma-navbat o'qni almashtiradi (D1 → D2 → D1 ...). Raqam (`nn`) shu ota ichida 01 dan sanaladi; **bir xil nom turli otalarda qayta ishlatiladi** (`X01` ichida `a01` va `X02` ichida yana `a01`), shuning uchun daraxt tartib bo'yicha quriladi: `C a01 ...` qatori eng oxirgi e'lon qilingan `a01` ga tegishli.
  - bo'sh (`   `) — **tayyor detal**; qator oxirida `0 <detal#>` (`F 01` indeksi). `0` — doimiy (barcha 853 detal qatorida 0; savol: aylantirish belgisi bo'lishi mumkin).
  - `R  ` — **qoldiq (Ostatok)**: `C K01 R   00000000 000 0 0001` — o'lcham 0, soni 0, oxirida qoldiq indeksi (`F 01 kind=1`). Faqat ildiz darajasida, karta oxirida, 6 kartada uchradi.
- **o'lcham** — bola bo'lakning ota o'qi bo'ylab o'lchami (mikron).
- **soni** — shu o'lchamdagi bo'lak ketma-ket necha marta takrorlanadi (har birining ichki tuzilmasi bir xil).

**Arra qalinligi (kerf) faylda yozilmaydi** — 3 mm (`swSawthick="3"`) deb hisoblanadi: har bir bo'lak (`T` dan tashqari) `o'lcham + 3` joy egallaydi.
Barcha 80 kartada: `T + Σ(o'lcham+3)×soni ≤ ota o'lchami` — xatosiz.
Detal qatorida detalning ikkinchi o'lchami doim ota bo'lak o'lchamiga aniq teng (qo'shimcha kesish yo'q).

### 2.3 Detal orientatsiyasi (tekstura)
Detal barg (leaf) holatidan uning list L o'qi bo'ylab o'lchami hisoblanadi (`K` da D1 = list L; `L` da D2 = list L):
- `rot=0` (tekstura) detallar — 97 ta joylashuvning hammasida detal L list L ga parallel.
- `rot=1` detallar — 455 ta to'g'ri, 301 ta 90° burilgan.
Demak `F 01` dagi L/W loyiha `l/w` (L = tekstura yo'nalishi) bilan beriladi, burilish faqat `.ncp` dagi geometriyadan kelib chiqadi.

### 2.4 Qoldiq (business waste) hisoblash
Ildiz darajasida ishlatilgan joy `U = T + Σ(o'lcham+3)×soni`, qolgan `D1 − U`. Qoldiq `F 01`:
- list-L o'qi bo'ylab va list-W o'qi bo'ylab tartibda yoziladi;
- D1 bo'ylab: `D1 − U − 5` (yana bir trim); D2 bo'ylab: `D2 − 10` (ikki tomondan trim).
Misollar (6/6 mos): 3181: list 2440×750, U=102 → qoldiq 2333×740; 3168 (`L01`, 1830×2750): U=1263 → 2740×562; 3175: 1816×1820.
Bu loyihadagi `<part waste="true" business="true" l= w= rl= rw=>` ga to'liq mos (`rl/rw` — xom, `l/w` — trimdan keyin).
Qoldiq faqat `cMinDimRegWaste` shartidan o'tganda yoziladi (GibLab hisobi; MebeliX o'z qoldiq qoidasini qo'llaydi).

### 2.5 `GibLabData.<GibLabID>.xml`
```xml
<?xml version="1.0" encoding="UTF-8"?><GibLab><GibLabLabel GibLabID="..."><part data="eJy..." id="11"/>...</GibLabLabel></GibLab>
```
- Bitta `<part>` har bir `F 01` uchun (qoldiq ham), `id = F-indeks × 10 + 1` (11, 21, 31, …).
- `data` = base64(zlib(Java-serializatsiya qilingan kalit/qiymat lug'ati)) — yorliq printeri uchun maydonlar:
  `project.name`, `project.date`, `project.uuid`, `material.name`, `product.name/code`, `part.id/code/name`, `length/width`,
  `detail.*`, `afterPreMilling.*`, `cutting.*`, kromka maydonlari (`etc/etn/ets/ett/etw/etj`, `eb*`, `el*`, `er*`), paz (`gr*`), `XNC1..5`, SVG chizma va h.k.
  Satrlar "overlong UTF-8" (`C1 xx`) bilan kodlangan.
- Bu stanok kesish rejasi uchun emas, **GibLab yorliq/etiketka moduli** uchun. Stanok uni talab qiladimi — noma'lum (savol). Agar talab qilinmasa, MebeliX uni yozmasligi mumkin.

---

## 3. Kesish rejasi qanday kodlangan (xulosa)

1. Har bir noyob kesish kartasi — alohida `.ncp`; `P 01` dagi runs — necha list shu karta bilan kesiladi (bir paket/kitob ichida bir vaqtda kesiladi deb taxmin qilinadi; namunalarda maks 2).
2. Karta — daraxt: ildiz (list) → `T` trim → 1-daraja polosalar (`Xnn`) → har polosada `T` trim → 2-daraja (`ann`) → … → detallar.
3. Kesish ketma-ketligi = qatorlar tartibi (chuqurlik bo'yicha birinchi — depth-first): polosa e'lon qilinadi, keyin uning ichi, keyin keyingi polosa.
4. Oxirgi bo'lakdan keyingi ortiqcha joy — chiqindi, yozilmaydi; yirik qoldiq bo'lsa `R` + `F 01 kind=1`.
5. Detal sonlari: `Σ (runs × yo'l bo'ylab barcha soni ko'paytmasi)` = `F 01` soni. 14 namunada hammasi teng
   (masalan 3167: 82 detal, jami 117 dona, 11 karta, 13 list; 3181: 37 detal, 69 dona, 5 karta, 5 list).

---

## 4. Loyiha → fayl moslashuvi (tekshirilgan)

To'g'ri loyiha fayli — **`NNNN_<mijoz>.project`** (pastki chiziqli, UTF-8, `project.uuid` va CS natijalari bor).
`NNNN <mijoz>.project` (bo'sh joyli, windows-1251, `importBMV`) — Bazis Mebelshchik dan import, kesish natijasi yo'q.

Avtomatik solishtirish (`F 01` yorliq raqami = `part@id` orqali):
| Buyurtma | F detal | Mos keldi | Tafovut |
|---|---|---|---|
| 3167, 3168, 3169, 3170, 3171, 3174, 3175, 3177, 3178, 3179, 3180, 3181, 3182 | 6…84 | 100 % | nom, L/W, soni, `rot`, 4 kromka (+ belgi), XNC nomlari, product nomi, sana, GibLabID — hammasi mos |
| 3173 | 53 | 49 ta id topildi, ko'p maydon farq qiladi | loyiha 2026-10-01 da (eksportdan keyin) qayta tahrirlangan — namuna eskirgan |

`F 01` tartibi = CS operatsiyasidagi `<part id>` tartibi (tekshirilgan 10 namunada aynan).

### Aniq misollar
**3171 (mijoz), `01_001 oldi bok`** — loyiha: `id=1 l=1400 w=1750 count=2 txt=true elt elb ell elr = @operation#1` (EL `elSymbol="A"`, band `t=1`).
```
F 01 0001 0001 0 000002 000002 LDSP DUB VATAN TEKST 00016000 01400000 01750000 01400000 01750000 01_001 oldi bok      0 9 9 0 ... 000000001 2026.09.08 ...
F 80 ... 0000 (A) 1                (A) 1                (A) 1                (A) 1                00 00 ...
```
`txt=true` → `0`; yorliq `000000001` = `part@id=1`. `0001.ncp` (runs 2): `C X01 01750000 001 0 0001` → 2 list × 1 = 2 = `count` ✓.
`01_002 tom` (`elt` faqat) → F 80 da faqat 2-tomon `(A) 1` ✓.

**3181 (mijoz)** — `01_003 bok`: `elb ell elr` → `F 80` 1,3,4-tomonlar; `01_001 TV #` kromkasi `@operation#5` (`elSymbol="E"`, `1-35 qora`) → `(E) 1`.
`01_008 bok` uchun XNC operatsiyalari `318101_01_008` (side=true) va `318101_01_008_2` (side=false) → 156 va 177-ustunlar.
`01_006 tr pol` `txt=false` → `1`. 5 ta list turi `B 01 0001..0005`; `0005.ncp` (list 2440×750) → `R` + `Ostatok 2333×740` = loyiha `l=2333 w=740 rl=2338 rw=750` ✓.

**3168 (mijoz)** — `L01` karta (`0002.ncp`, `P 03 … 01830000 02750000`): `X01` = 597 polosa (W o'qi bo'ylab), ichida `02180000 001 0 0001` → `01_001 bok` `l=2180 w=597 txt=false`.
Qoldiq: `L01 R` → `F 01 … 1 … 02740000 00562000 Ostatok` = loyiha `l=2740 w=562 rl=2750 rw=567` ✓.

---

## 5. Minimal qayta tuzilgan misol (anonim)

Bitta list 2750×1830×16, 2 detal: `01_001 bok` 720×560 ×2 (tekstura, `elb`+`ell` kromka A), `01_002 polka` 564×300 ×3 (aylantirsa bo'ladi), qoldiq 1714×1820.
Bu misol yuqoridagi tahlil skripti bilan tekshirildi (sonlar 2/3, geometriya va qoldiq formulasi mos). Qator oxiri `CRLF`.

`0000.ncl`:
```
S 01 001 001 9999_mijoz_LDSP_OQ   2026-10-04 0 1a2b000001a0e33b80ab
S 46 9999_mijoz_LDSP_OQ                                                    
B 01 0001 0 LDSP OQ              00016000 02750000 01830000 0 LDSP OQ              0 0 0000000001 0
F 01 0001 0001 0 000002 000002 LDSP OQ              00016000 00720000 00560000 00720000 00560000 01_001 bok           0 9 9 0 00 000000 000 000000 000 1 0 999901_01_001                                                                      1 0 1a2b000001a0e33b80ab 01 shkaf             000000001 2026.10.01 0 0 000
P 09 00000000 00000000 00000000 00000000 XXXX
F 80 00000000 00000000 00000000 00000000 0000 (A) 1                                     (A) 1                                     00 00 00 00 00000000 00000000
F 01 0002 0002 0 000003 000003 LDSP OQ              00016000 00564000 00300000 00564000 00300000 01_002 polka         1 9 9 0 00 000000 000 000000 000 1 0                                                                                    1 0 1a2b000001a0e33b80ab 01 shkaf             000000002 2026.10.01 0 0 000
P 09 00000000 00000000 00000000 00000000 XXXX
F 80 00000000 00000000 00000000 00000000 0000                                                                                     00 00 00 00 00000000 00000000
F 01 0001 0001 1 000001 000001 LDSP OQ              00016000 01714000 01820000 00000000 00000000 Ostatok              0 9 9 0 00 000000 000 000000 000 0 0
S$
```
(Eslatma: `S 46` qatori 75 belgigacha bo'sh joy bilan to'ldiriladi.)

`0001.ncp`:
```
P 01 0001 0001 000001 0 0 0000 0
P 02 01 0001 0001 00000000 001
P 03 00 0 00 00000000 02750000 01830000 02750000 01830000
P 98 0 0 0
C K01 T   00005000 001
C K01 X01 00720000 001
C X01 T   00005000 001
C X01     00560000 002 0 0001
C X01 a01 00300000 001
C a01     00564000 001 0 0002
C K01 X02 00300000 001
C X02 T   00005000 001
C X02     00564000 002 0 0002
C K01 R   00000000 000 0 0001
P$
```
Tushuntirish: `K01` — 2750 bo'ylab: trim 5, polosa 720 (+3), polosa 300 (+3) → U=1031, qolgan 1719 → qoldiq 1719−5=1714 × 1830−10=1820.
`X01` (720×1830) ichida 1830 bo'ylab: trim 5, 2×560 (`01_001`, L=720 list L ga parallel — tekstura saqlangan), `a01` 300 polosa ichida 564 (`01_002`).
`X02` (300×1830) ichida 2×564 — `01_002` 90° burilgan (rot=1 bo'lgani uchun ruxsat).
Zip: `9999_mijoz_LDSP_OQ.l.zip` = `0000.ncl` + `0001.ncp` (+ ixtiyoriy `GibLabData.1a2b000001a0e33b80ab.xml`).

### Generator uchun qoidalar (qisqa)
- Uzunlik → `'%08d' % round(mm*1000)`; son → `'%06d'`/`'%03d'`; indeks → `'%04d'`.
- Matn maydonlari: kesish + `ljust` (material 20, nom 20, product 20, XNC 20, `S 46` 70, kromka 21).
- `F 01` (detal) aniq 312 belgi, qoldiq 154, `F 80` 159, `B 01` 99, `S 01` 67, `P 01` 32, `P 02` 30, `P 03` 57, `P 09` 45, `C` 22/29.
- Trim `T` = `cTrim + kerf` (5 mm); kerf yozilmaydi, lekin joylashuvda hisobga olinadi.

---

## 6. Noaniq maydonlar — foydalanuvchiga savollar

1. **`GibLabData.*.xml` kerakmi?** Stanok (yoki uning yorliq printeri) bu faylni o'qiydimi, yoki faqat `.ncl/.ncp` yetarlimi? Agar kerak bo'lsa, ichidagi serializatsiya formati GibLab-ga xos — uni qayta yaratish murakkab.
2. **`P 02` 14–17 ustun** (namunada doim = runs): bu "paketdagi listlar soni" (kitob balandligi) mi? runs > 2 bo'lgan (masalan 5 ta bir xil list) namunasi bormi? Ular 2+2+1 ga bo'linadimi yoki bitta karta runs=5 bo'ladimi?
3. **`P 03` ikkinchi juftlik** (doim birinchisiga teng) — xom list va trimdan keyingi list o'lchamimi? Qoldiq-list (ostatok) bilan kesilgan namunalarda ham teng edi.
4. **`F 80` dagi `(A) 1`** — "1" lenta qalinligimi (band `t`)? Hamma loyihalarda `t=1`. 2 mm (yoki 0,4) kromkali namuna bo'lsa yuboring.
5. **`F 01` L/W** — `l/w`, `cl/cw` (kesish o'lchami) yoki `dl/dw` (tayyor o'lcham)? Namunalarda uchalasi teng. Kromka uchun qo'yim (pre-joint) qo'llansa qaysi yoziladi? Ikkinchi L/W juftligi (80–96) nimani bildiradi?
6. **`C` detal qatoridagi `0`** (23-ustun) — burilish belgisimi? 853 qatorda hammasi `0`, hatto 301 ta burilgan detalda ham.
7. **Doimiy maydonlar**: `S 01` dagi `001 001`; `B 01` dagi `0000000001`; `F 01` dagi `9 9 0 00 000000 000 000000 000 1 0`, `P 09` dagi `XXXX`; `F 80` boshidagi va oxiridagi nollar. Stanok sozlamasidan (masalan, Schelling NCL versiyasi, yorliq turi) kelib chiqadimi? Ularni o'zgartirish kerak bo'lgan holatlar bormi?
8. **Kirillcha nomlar** (detal/material) qaysi kodlashda yozilishi kerak (cp1251/cp866)? Namunalarda faqat lotin bor.
9. **Trim** har doim 5 mm (= 2 + 3) bo'ladimi, yoki `cTrimL`≠`cTrimW` bo'lganda ildiz va polosa trimlari farq qiladimi? Polosaning ikkinchi tomoni (oxiri) trim qilinmaydi — to'g'rimi?
10. **3173 namunasi** loyihasi eksportdan keyin o'zgartirilgan — u bilan solishtirish to'liq emas (boshqa 13 tasi 100 % mos).
11. Zip nomidagi material nomini tozalash qoidasi (qavslar, nuqta, `#`): stanok uchun zip nomi muhimmi, yoki ixtiyoriy?
