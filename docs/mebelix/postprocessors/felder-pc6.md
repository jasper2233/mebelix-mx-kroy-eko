# Felder PC6 — `.may` formati (GibLab post-protsessor chiqishi)

> Manba: `post prtsessorlar/PILNIY APPARAT/Felder PC6/*.may` (7 ta fayl, buyurtmalar 3151, 3153, 3155, 3156, 3157, 3159, 3161) va mos `giblab project/3 Eldor/<NNNN> <mijoz>/<NNNN>_<mijoz>.project`.
> Tekshirish: 7 fayl, 30 ta karta (MA200), 192 ta detal yozuvi (MA010), 64+41 ta polosa (MA400/MA300), 289 ta barg (detal) yozuvi (MA3k0/MA4k0).
> Bir xil buyurtmalar uchun **Felder PC7** (`felder-pc7.md`) va **SCM MaestroCut** fayllari ham bor — uchalasining raskroyi aynan bir xil (pastda isbot).
> Ishonch darajasi: **yuqori** (kesish sxemasi, detallar, kromka, o'lchamlar 100% tekshirildi); bir nechta doimiy maydonlarning ma'nosi ochiq savol.

---

## 1. Fayllar

| Xususiyat | Qiymat |
|---|---|
| Kengaytma | `.may` |
| Nomlash | `<loyiha nomi>_<material nomi>.may`, material nomidagi bo'sh joy(lar) → bitta `_` (masalan `LDSP  PIKARD` → `LDSP_PIKARD`). Masalan `3161_mijoz_LDSP_PIKARD.may` |
| Soni | **bitta material (bitta CS operatsiyasi) = bitta fayl**. Bir buyurtmada bir nechta material bo'lsa — har biriga alohida fayl (namunalarda har buyurtmadan bittadan fayl berilgan) |
| Arxiv | yo'q, oddiy matn fayl |
| Kodlash | ASCII (namunalarda 127 dan katta bayt yo'q). Kirill/UTF-8 nomlar qanday yozilishi noma'lum → savol |
| Qator oxiri | CRLF (`\r\n`), oxirgi qator ham CRLF bilan tugaydi |
| Ajratkich | `/` (har bir maydondan keyin `/`, ya'ni qator `/` bilan tugaydi) |
| Maydonlar | **qat'iy uzunlikdagi** (fixed width): matn — chapga tekislanib bo'sh joy bilan to'ldiriladi (uzunrog'i kesiladi), son — chapdan `0` bilan to'ldiriladi |
| O'nlik ajratkich | nuqta `.`; o'lchamlar 1 kasr xona (`001900.0`), `MA050` dagi bitta maydon 2 xona (`0000.00`) |
| Birlik | mm |

Fayl tuzilishi (tartib qat'iy):

```
MA000                     sarlavha (buyurtma)
MA005                     material sarlavhasi
{ MA010 ; MA015 } × N     har bir detal uchun 2 qator (N = CS dagi detal pozitsiyalari soni)
MA050                     list (zagotovka) ta'rifi
{ MA200 ; { MA300|MA400 ; { MA3k0|MA4k0 }* }* }*   kartalar (raskroy)
MA999/                    tugash
### GibLab label data ###
#<partId>=<base64>        har bir detal uchun etiketka ma'lumoti (N qator)
```

---

## 2. Yozuvlar va maydonlar

Quyida `#` — `/` bilan bo'lingandagi indeks (0 = yozuv turi), `W` — maydon kengligi (belgi).

### MA000 — sarlavha (1 ta)

| # | W | Misol | Ma'nosi |
|---|---|---|---|
| 1 | 6 | `260926` | Eksport sanasi. `26.09.2026` → `260926`; DDMMYY yoki YYMMDD ekanini aniqlab bo'lmadi (namunada ikkalasi ham bir xil) — **savol** |
| 2 | 1 | `A` | doimiy (ma'nosi noma'lum) |
| 3 | 0 | `` | bo'sh |
| 4 | 8 | `GibLab  ` | dastur nomi (doimiy) |
| 5 | 1 | `M` | doimiy, ehtimol "metric/mm" |
| 6 | 3 | `UZS` | loyiha valyutasi (`project@currency`) |
| 7 | 30 | `3161 mijoz` | buyurtma nomi = `good[typeId=product]@product.order` (yoki loyiha nomi bo'sh joy bilan) |

### MA005 — material sarlavhasi (1 ta)

| # | W | Misol | Ma'nosi |
|---|---|---|---|
| 1 | 10 | `110052` yoki `3` | **material kodi** (`good[typeId=sheet]@code`); kod bo'sh bo'lsa — sheet `good@id` (3151/3155/3156/3157: `3`, 3153: `5`, 3159: `4`) |
| 2 | 6 | `000002` | CS operatsiyasi `@id` (6 xona) |
| 3 | 5 | `016.0` | qalinlik `t` |
| 4 | 30 | `LDSP  PIKARD` | material nomi (`sheet@name`, ikki bo'sh joy saqlanadi) |
| 5 | 30 | `110052` / bo'sh | material kodi (faqat kod bor bo'lsa) |
| 6 | 30 | `#N(26092617461861705)` | "partiya/etiketka" ID: `YYMMDDHHMMSS` (eksport vaqti, 26.09.26 17:46:18) + 5 raqam (buyurtmaga xos, PC7 da ham bir xil; kelib chiqishi noma'lum) |

### MA010 — detal (har pozitsiya uchun 1 ta)

| # | W | Misol | Ma'nosi / manba |
|---|---|---|---|
| 1 | 10 | `110052` | material kodi (MA005#1 bilan bir xil) |
| 2 | 6 | `000002` | CS op id |
| 3 | 5 | `016.0` | qalinlik |
| 4 | 16 | `01_022 nostandar` | `part@name` — **16 belgida kesiladi** |
| 5 | 8 | `001900.0` | uzunlik `part@l` (= `cl`, namunalarda farq yo'q) |
| 6 | 8 | `000347.0` | eni `part@w` (= `cw`) |
| 7 | 5 | `00001` | soni `part@count` |
| 8 | 1 | `J`/`N` | **J = burish mumkin** (`txt=false`), **N = tekstura bor, burish mumkin emas** (`txt=true`). 191/192 mos; 1 istisno (3161 `01_009 sokl`) — eksport paytida `txt=true` bo'lgan (etiketka blokida `txt=1`), `.project` keyin o'zgargan |
| 9 | 2 | `  ` | doim bo'sh |
| 10 | 12 | `  1 1 1     ` | kromka bayroqlari: pozitsiya 0=yuqori(T), 2=pastki(B), 4=chap(L), 6=o'ng(R); `1` = kromka bor, ` ` = yo'q; oxirgi 4 belgi doim bo'sh. (`1` — bayroqmi yoki kromka qalinligi (barcha namunalarda t=1)mi — savol) |
| 11 | 8 | `001900.0` | uzunlik (takror; `cl` deb taxmin) |
| 12 | 8 | `000347.0` | eni (takror; `cw`) |
| 13 | 8 | `001898.0` | **`jl`** = l − t(ell) − t(elr) (kromkasiz, "afterPreMilling" uzunlik) |
| 14 | 8 | `000346.0` | **`jw`** = w − t(elt) − t(elb) |
| 15 | 30 | `(A) 1-19 Sasna` | yuqori kromka (`elt`): `(<EL.elSymbol>) <band@name>`; yo'q bo'lsa bo'sh |
| 16 | 30 | | pastki kromka (`elb`) |
| 17 | 30 | | chap kromka (`ell`) |
| 18 | 30 | | o'ng kromka (`elr`) |
| 19 | 5 | `00001` | soni (takror) |
| 20 | 5 | `00001` | soni (takror; ehtimol "kesish kerak bo'lgan soni") |

### MA015 — detal qo'shimcha (har MA010 dan keyin)

| # | W | Ma'nosi |
|---|---|---|
| 1–7 | | MA010#1–7 bilan bir xil (kod, op id, qalinlik, nom16, l, w, soni) |
| 8–12 | 5×30 | doim bo'sh (ehtimol foydalanuvchi maydonlari/qo'shimcha matn) |
| 13 | 30 | XNC dastur kodi (1-tomon): `operation[typeId=XNC][side=true]@code`, masalan `316101_01_001`; XNC yo'q bo'lsa bo'sh. 2-tomon kodi (`..._2`) PC6 ga **yozilmaydi** |
| 14 | 30 | `#P(<part@id>)` — etiketka ma'lumotiga havola (`#<id>=` qatoriga) |

### MA050 — list (zagotovka) ta'rifi (1 ta)

| # | W | Misol | Ma'nosi |
|---|---|---|---|
| 1–3 | | | material kodi, CS id, qalinlik |
| 4 | 6 | `GibLab` | doimiy |
| 5 | 8 | `002750.0` | list uzunligi (`sheet@l`, X o'qi) |
| 6 | 8 | `001830.0` | list eni (`sheet@w`, Y o'qi) |
| 7 | 4 | `0015` | doimiy — **savol** |
| 8 | 4 | `J   ` | doimiy; ehtimol "listda tekstura yo'nalishi bor" — **savol** |
| 9 | 7 | `0000.00` | doimiy (narx? `sheet@cost=0`) — **savol** |
| 10 | 8 | `000105.0` | = 100 + chekka kesim (trim). 3159 da trim=8 → `000108.0`. Ma'nosi — **savol** |
| 11–14 | 4 | `05.0` | 4 tomondan chekka kesim (trim). **= `cTrimL` + `swSawthick`** (2+3=5; 3159: 2+6=8). Tartib (old/orqa/chap/o'ng?) — namunalarda hammasi teng |
| 15 | 4 | `03.0` | arra qalinligi (kerf) = `tool.cutting@swSawthick` |
| 16 | 30 | | material nomi |
| 17 | 30 | | material kodi (bo'lsa) |
| 18 | 1 | ` ` | doim bo'sh |

### MA200 — karta (raskroy sxemasi), har biri bitta list turi uchun

| # | W | Misol | Ma'nosi |
|---|---|---|---|
| 1–3 | | | material kodi, CS id, qalinlik |
| 4 | 6 | `GibLab` | doimiy |
| 5, 6 | 8 | `002750.0`/`001830.0` | list L × W |
| 7, 8, 9 | 4 | `0001`/`0002` | **shu karta bo'yicha kesiladigan listlar soni**. Uchala maydon doim bir xil. Σ(#7) = ishlatilgan listlar soni (`cMaterialCount`; 3156: 2+6×1=8 ✓, 3157: 2+2+3=7 ✓). Uchalasining farqi (soni / takrorlar / paket balandligi?) — **savol** |
| 10–13 | 4 | `05.0` | trim (MA050 dagi kabi) |
| 14 | 4 | `03.0` | kerf |

### MA300 / MA400 — 1-darajali polosa

| # | W | Ma'nosi |
|---|---|---|
| 1 | 8 | polosa o'lchami (1-daraja kesim qadami) |
| 2 | 5 | doim bo'sh (`     `) — **savol** (polosa takrori?) |

* `MA300` — birinchi kesimlar **list uzunligi bo'ylab** (polosa eni Y o'qida, polosa uzunligi = butun list uzunligi).
* `MA400` — birinchi kesimlar **ko'ndalang** (polosa uzunligi X o'qida, eni = butun list eni).
* Bitta kartada faqat bitta yo'nalish uchradi (18 karta MA4xx, 12 karta MA3xx).

### MA3k0 / MA4k0 (k = 1..5) — detal (barg)

| # | W | Misol | Ma'nosi |
|---|---|---|---|
| 1 | 16 | `7` | detalning **MA010 tartib raqami** (1 dan, fayldagi MA010 qatorlari tartibi) |
| 2 | 8 | `000498.0` | detalning **list X o'qi** (uzunlik, 2750 yo'nalishi) bo'yicha o'lchami |
| 3 | 8 | `000420.0` | detalning **list Y o'qi** bo'yicha o'lchami |
| 4 | 2 | `01` | doim `01` (bitta listda 1 dona) |
| 5 | 5 | `     ` | doim bo'sh |

X/Y listga nisbatan berilgani uchun burilish shu yerdan aniqlanadi: `X==l && Y==w` → oddiy, `X==w && Y==l` → 90° burilgan. `N` (tekstura) detallari hech qachon burilmagan (142/142); `J` detallarda 44 ta burilish bor.

k raqamining ma'nosi — 3-bo'limga qarang.

### MA999 — tugash: `MA999/`

### Etiketka bloki (`### GibLab label data ###` dan keyin)

* Har detal pozitsiyasi uchun bitta qator: `#<part@id>=<base64>`, kalit — loyiha `part@id` (MA015#14 dagi `#P(id)` bilan mos), tartib — MA010 tartibi.
* Qiymat: `base64(zlib(...))` (`eJ` bilan boshlanadi). Ichida GibLab'ning etiketka o'zgaruvchilari: ketma-ket `[tur 1 bayt][1 bayt][uzunlik u32 BE][kalit][bor 1 bayt][qiymat]`; tur: 0=satr (u32 uzunlik + baytlar), 1=int32, 2=double BE, 3=bool. Kalit va satrlardagi kichik lotin harflari "overlong UTF-8" (`C1 xx`) bilan yashirilgan.
* Kalitlar (to'liq ro'yxat emas): `project.name/date/currency/uuid/crc16/crc32`, `material.name/code`, `product.name/code/count`, `operation.code/name/parts.count`, `part.id/code`, `name`, `length/width`, `detail.*`, `afterPreMilling.*`, `cutting.*`, `allowanceT/B/L/R`, `thick`, `txt`, `count/usedCount`, kromka (`et*`, `eb*`, `el*`, `er*`: c=kod, n=nom, s=belgi, t=qalinlik, w=eni, j=prejoint), paz (`grt*`...), `drill/mill/groove`, `XNC1..5`, `part.position`, `product.order`.
* Bu blok faqat etiketka chop etish uchun (Felder dasturi GibLab etiketka shablonini ishlatsa). **Biz uchun ixtiyoriy** deb hisoblaymiz — kerakligini mijoz tasdiqlashi kerak (savol).

---

## 3. Kesish rejasi qanday kodlangan

Daraxt (guillotine) ko'rinishi, DFS tartibida, faqat **barglar (detallar)** yoziladi; oraliq bo'laklar yashirin.

**Darajalar va o'qlar.** 1-daraja = polosa (`MA300`/`MA400` qatoridagi o'lcham). Keyingi darajalar o'qni almashtirib boradi:

| Daraja | `MA3…` kartada o'q | `MA4…` kartada o'q |
|---|---|---|
| 1 (polosa) | Y | X |
| 2 | X | Y |
| 3 | Y | X |
| 4 | X | Y |
| 5 | Y | X |

**k raqami (MA3**k**0) ma'nosi** — detalni ozod qiluvchi oxirgi kesim darajasi `L` va u "yangi ochilgan ota bo'lakdagi birinchi kesim"mi:

| k | Oxirgi kesim darajasi L | Ota bo'lak | Talqin |
|---|---|---|---|
| 1 | 2 | polosa | polosadan L2 kesim bilan detal (detalning polosa o'qidagi o'lchami = polosa o'lchami) |
| 2 | 3 | **yangi** L2 bo'lak | yangi L2 bo'lak (o'lchami = detalning L2-o'qi o'lchami) ochiladi, keyin L3 kesim bilan detal |
| 3 | 3 | mavjud L2 bo'lak | joriy L2 bo'lakdan navbatdagi L3 kesim, detal tayyor |
| 4 | 4 | **yangi** L3 bo'lak | joriy L2 bo'lakda yangi L3 bo'lak (o'lchami = detal o'lchami), keyin L4 kesim |
| 5 | 4 | mavjud L3 bo'lak | joriy L3 bo'lakdan navbatdagi L4 kesim |
| 6* | 5 | yangi L4 bo'lak | (namunada yo'q, qoida bo'yicha) |
| 7* | 5 | mavjud L4 bo'lak | (namunada yo'q) |

Formula: `k = 2L−3`, agar detal ota bo'lakdagi birinchi kesim bo'lsa va `L≥3` → `k = 2L−4`.

Qoidalar:
* Juft k (2, 4) kelganda yangi ota bo'lak ochiladi va uning o'lchami = detalning shu o'qdagi o'lchami. Agar undan yuqoridagi ota (masalan k=4 uchun L2 bo'lak) joriy holatda yo'q bo'lsa (polosa endi boshlangan yoki oldingi yozuv k=1 bo'lsa), u **yashirin** ochiladi va o'lchami ichidagilarning maksimal chetidan aniqlanadi (3151, 1-karta: `MA440 D62 244×995` polosaning birinchi yozuvi; MaestroCut'da bu L2 bo'lak 1000 mm, Felder uchun 995 yetarli — farq faqat chiqindi).
* Toq k (1, 3, 5) — mavjud ota bo'lakka qo'shni kesim; detalning boshqa o'qdagi o'lchami ota bo'lak o'lchamiga teng bo'lishi shart (tekshirildi, xatosiz).
* Kesim orasida har doim kerf qo'shiladi; bo'lak oxiridagi qoldiq — chiqindi (yozilmaydi).
* Polosalar 1-o'q bo'ylab trim'dan boshlab ketma-ket: `pos = trim; har polosa: pos += size + kerf`.
* Takror (book/paket): bitta listdan bir nechta bir xil detal — yozuv takrorlanadi (masalan `MA420/9 …` ×3). Bir karta bir nechta listga — MA200#7 (`0002`) orqali, yozuvlar 1 marta.
* Qoldiq (delovoy ostatok) **PC6 ga yozilmaydi** (PC7 da bor).
* Trim'lar yozilmaydi (MA050/MA200 dagi qiymat bilan mashina o'zi kesadi).

**Misol (3155, 2-karta, MaestroCut daraxti bilan solishtirish):**

```
MA300/000887.0/        polosa Y=887
MA320/6  400×778   → X400 (yangi L2) → U778 (L3)            [Maestro: X400 U778]
MA320/7  400×778   → X400 → U778
MA320/8  810×303   → X810 (yangi L2) → U303
MA330/9  810×303   →        U303 (shu X810 ichida)
MA340/13 777×270   →        U270 (yangi L3) → V777 (L4)
MA320/11 794×303   → X794 → U303
MA340/12 778×300   →        U300 → V778
MA340/13 777×270   →        U270 → V777
```

**Tekshiruv natijalari (7 fayl, 30 karta):**
* Har bir kartani yuqoridagi qoida bo'yicha geometrik qayta tikladim: barcha detallar list ichida (trim hisobga olingan), bir-birini kesib o'tmaydi, toq-k o'lcham mosligi buzilmagan — **0 xato**.
* Σ(detal yozuvlari × MA200#7) har bir pozitsiya bo'yicha = `part@count`; jami = CS `cPartCount` (61, 70, 33, 73, 36, 20, 18) — **7/7 mos**.
* SCM MaestroCut (`.XPrg`, aniq Y/X/U/V daraxti) dan k-kodlarni avtomatik hisoblab, Felder ketma-ketligi bilan solishtirdim: **30/30 karta, barcha polosa o'lchamlari, detal ID va k-kodlari bir xil**.
* PC6 va PC7 kesish qismi bir xil (qoldiqdan tashqari) — 7/7.

---

## 4. Loyiha (.project) → fayl moslik jadvali

| Loyiha manbasi | PC6 maydoni |
|---|---|
| `good[typeId=product]@product.order` | MA000#7 |
| `sheet@code` (yo'q bo'lsa `sheet@id`) | MA005#1, MA010#1, MA015#1, MA050#1, MA200#1 |
| `operation[typeId=CS]@id` | #2 (6 xona) |
| `sheet@t` | #3 |
| `sheet@name` | MA005#4, MA050#16 |
| `sheet@l`, `sheet@w` | MA050#5,6; MA200#5,6 |
| `cTrimL + swSawthick` | MA050#11–14, MA200#10–13 |
| `tool.cutting@swSawthick` | MA050#15, MA200#14 |
| CS ichidagi `<part id>` tartibi | MA010/MA015 tartibi (qoldiq/list stok qismlarisiz) |
| `part@name` (16 belgi) | MA010#4, MA015#4 |
| `part@l`, `part@w` (`cl`,`cw` bilan teng) | MA010#5,6,11,12 |
| `part@jl`, `part@jw` | MA010#13,14 |
| `part@count` | MA010#7,19,20, MA015#7 |
| `part@txt` | MA010#8 (`true`→`N`, `false`→`J`) |
| `part@elt/elb/ell/elr` + `EL@elSymbol` + `elXMat` | MA010#10 (bayroq), #15–18 (matn) |
| `operation[XNC][side=true]@code` | MA015#13 |
| `part@id` | MA015#14 `#P(id)`, etiketka `#id=` |
| raskroy natijasi (optimizator) | MA200 / MA300/MA400 / MA3k0/MA4k0 |

Konkret tekshiruvlar (mijoz nomlari olib tashlangan):

1. **3161 (LDSP PIKARD, kod 110052, CS id 2):** `01_001 bok` l=1900 w=347, kromka B/L/R (A, 1 mm) → `MA010/110052/000002/016.0/01_001 bok/001900.0/000347.0/00001/J/  /  1 1 1     /001900.0/000347.0/001898.0/000346.0/ /(A) 1-19 Sasna/(A)…/(A)…/00001/00001/`; jl=1900−1−1=1898, jw=347−1=346 ✓. `01_006 Fasad` txt=true → `N` ✓. Karta: 1 list, polosa `MA400` 2254 + 352 + 100; 18 dona detal = `cPartCount=18` ✓.
2. **3155 (LMDF DUB VATAN, kod yo'q → `3` = sheet id, CS id 3):** `01_022 nostandar` (nom 16 belgiga kesilgan), kromka B=(A) votan, L=(B) kashmir → bayroq `  1 1       `, jl=2400−1=2399 ✓. 3 karta × 1 list = 3 list = `cMaterialCount=3` ✓; 33 detal ✓.
3. **3157 (LDSP KASHMIR SHAGREN):** 1- va 2-karta `0002/0002/0002` (2 listdan), qolgan 3 ta 1 dan → 7 list = `cMaterialCount=7` ✓; 25 detal yozuvi × list soni = 36 = `cPartCount` ✓.
4. **3159 (LMDF BELI KARONA TEKSTURA):** arra 6 mm (`swSawthick=6`) → kerf `06.0`, trim `08.0` (=2+6), MA050#10 `000108.0` ✓.

---

## 5. Minimal qayta tiklangan misol (anonim)

Buyurtma `9001 mijoz`, material `LDSP OQ` (kod yo'q → sheet id `3`), CS id 2, list 2750×1830×16, trim 5, kerf 3. Detallar: 1) `01_001 bok` 720×560 ×2 (kromka T,B); 2) `01_002 polka` 564×300 ×2 (T); 3) `01_003 fasad` 716×396 ×1, tekstura, 4 tomon kromka. Raskroy: polosa Y=560 [720, 720, 564→300, 564→300], polosa Y=396 [716].

```text
MA000/041026/A//GibLab  /M/UZS/9001 mijoz                    /
MA005/3         /000002/016.0/LDSP OQ                       /                              /#N(26100412000012345)         /
MA010/3         /000002/016.0/01_001 bok      /000720.0/000560.0/00002/J/  /1 1         /000720.0/000560.0/000720.0/000558.0/(A) 1-19 oq                   /(A) 1-19 oq                   /                              /                              /00002/00002/
MA015/3         /000002/016.0/01_001 bok      /000720.0/000560.0/00002/                              /                              /                              /                              /                              /900101_01_001                 /#P(1)                         /
MA010/3         /000002/016.0/01_002 polka    /000564.0/000300.0/00002/J/  /1           /000564.0/000300.0/000564.0/000299.0/(A) 1-19 oq                   /                              /                              /                              /00002/00002/
MA015/3         /000002/016.0/01_002 polka    /000564.0/000300.0/00002/                              /                              /                              /                              /                              /                              /#P(2)                         /
MA010/3         /000002/016.0/01_003 fasad    /000716.0/000396.0/00001/N/  /1 1 1 1     /000716.0/000396.0/000714.0/000394.0/(A) 1-19 oq                   /(A) 1-19 oq                   /(A) 1-19 oq                   /(A) 1-19 oq                   /00001/00001/
MA015/3         /000002/016.0/01_003 fasad    /000716.0/000396.0/00001/                              /                              /                              /                              /                              /900101_01_003                 /#P(3)                         /
MA050/3         /000002/016.0/GibLab/002750.0/001830.0/0015/J   /0000.00/000105.0/05.0/05.0/05.0/05.0/03.0/LDSP OQ                       /                              / /
MA200/3         /000002/016.0/GibLab/002750.0/001830.0/0001/0001/0001/05.0/05.0/05.0/05.0/03.0/
MA300/000560.0/     /
MA310/1               /000720.0/000560.0/01/     /
MA310/1               /000720.0/000560.0/01/     /
MA320/2               /000564.0/000300.0/01/     /
MA320/2               /000564.0/000300.0/01/     /
MA300/000396.0/     /
MA310/3               /000716.0/000396.0/01/     /
MA999/
### GibLab label data ###
```

(Etiketka qatorlari `#1=…`, `#2=…`, `#3=…` — ixtiyoriy, 2-bo'limga qarang. Har qator CRLF bilan tugaydi.)

**Generatsiya algoritmi (MebeliX uchun):**
1. Optimizator daraxtini normallashtiring: har bo'lak o'lchami = ichidagilarning maksimal cheti; bo'lak ichida, agar biror detal bo'lakni to'liq egallasa (o'lchami bo'lak o'lchamiga teng), uni birinchi qo'ying.
2. Karta: `MA200`; har polosa: `MA300` (Y bo'yicha polosa) yoki `MA400` (X bo'yicha).
3. DFS: L darajadagi tayyor detal uchun `k = 2L−3`; agar u ota bo'lakdagi birinchi kesim va L≥3 bo'lsa `k = 2L−4`. Oraliq (detal bo'lmagan) bo'laklar yozilmaydi.
4. Detal raqami — MA010 tartib raqami; X/Y — listga nisbatan.
5. Bir xil kartalar → bitta MA200, soni #7–9 ga.

---

## 6. Ochiq savollar

1. `MA000#1` sana formati DDMMYY yoki YYMMDD? (`260926` — ikkalasiga ham mos). `MA000#2 = A`, `#5 = M` nimani bildiradi?
2. `#N(YYMMDDHHMMSS+5 raqam)` dagi oxirgi 5 raqam qanday hosil qilinadi (3161→61705, 3155→16128)? Mashina buni tekshiradimi yoki ixtiyoriy noyob ID yetarlimi?
3. `MA050#7 = 0015`, `#8 = J`, `#9 = 0000.00`, `#10 = 100+trim` — ma'nolari? Felder dasturida qaysi parametrlar (min. qoldiq, paket balandligi, narx...)?
4. `MA200#7/#8/#9` — uchtasi doim teng; farqi nima (listlar soni, paket balandligi, takror)? Paket balandligi (`swPackageHeight=40`) bilan cheklash kerakmi (masalan 3 list → 2+1)?
5. Trim 4 qiymati qaysi tomonlarga mos (old/orqa/chap/o'ng)? Har doim `cTrimL + kerf` mi?
6. MA010#10 dagi `1` — kromka bor bayrog'imi yoki kromka qalinligi (mm)? 2 mm kromkada `2` yoziladimi?
7. MA010#11–12: `l/w` mi yoki `cl/cw` (kesish o'lchami)? Namunalarda farq yo'q; `cSizeMode`/pripusk bo'lganda qaysi biri yoziladi? Kesish sxemasidagi X/Y ham `cl/cw` deb taxmin qilinmoqda.
8. Kirill yoki 16 belgidan uzun nomlar: kodlash (cp1251? cp866?) va qisqartirish qoidasi tasdig'i.
9. Etiketka bloki (`### GibLab label data ###`) mashina uchun majburiymi? Agar yo'q bo'lsa, faylni `MA999/` bilan tugatish yetarlimi?
10. MA015#8–12 (5 ta bo'sh 30-belgilik maydon) va MA300/MA400#2, MA3k0#5 (5 belgilik bo'sh) — nimalar uchun?
11. Qoldiq (delovoy ostatok) PC6 ga umuman yozilmaydimi yoki mashina sozlamasiga bog'liqmi?
12. k=6/7 (5-daraja) va undan chuqur kodlar mashinada qo'llab-quvvatlanadimi (`swMaxturns=6` loyihalarda bor, lekin namunada max k=5)?
