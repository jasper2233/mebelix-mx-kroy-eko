# P. MebeliX Kroy ↔ avvalgi dastur (GibLab): taqqoslash natijalari

Sana: 2026-10-01. Manba: korxonaning 205 ta real `.project` fayli (`tools/bench/corpus.json`).
Har fayl ichida avvalgi dastur (litsenziyali GibLab, korxona kompyuterida) **saqlagan natija** bor: listlar soni,
деловой qoldiqlar, kesish uzunligi, kromka metri, CNC statistikasi. MebeliX har bir kroyni o'sha parametrlar
bilan (propil, torsovka, burilishlar soni, minimal obrezka, tekstura, birinchi kesish yo'nalishi, qoldiq qoidalari)
qayta yechdi va natijani `validate()` bilan tekshirdi. GibLab dasturi, kaliti va kodi ishlatilmagan —
faqat korxonaning o'z fayllaridagi raqamlar bilan solishtirilgan.

## 1. Listli kroy (CS) — 397 kroy, 12 581 detal

| Rejim | Listlar (MebeliX / avvalgi) | Kam | Teng | Ko'p | Tekshiruv xatosi | Eng uzoq kroy |
|---|---|---|---|---|---|---|
| **Стандарт** (standart) | **1186 / 1212** (−26 list, −2.1 %) | 15 | 381 | 1 | 0 | 17 s |
| Быстро | 1212 / 1212 | 11 | 363 | 23 | 0 | 1.9 s |

Listlar soni teng bo'lgan kroylarda («Стандарт», 381 ta):

| Ko'rsatkich | MebeliX | Avvalgi | Farq |
|---|---|---|---|
| Деловой qoldiq (≥ 1000×500, ≥ 0.5 m², korxona sozlamasi) | **751.2 m²** | 652.3 m² | **+15.2 %** (124 kroyda ko'p, 75 da kam) |
| Kesish uzunligi (arra yo'li) | **22 026 m** | 22 287 m | −1.2 % |

Bitta joylanmagan detal yo'q; 1 kroyda avvalgi natija to'liq emas (12 detaldan 10 tasi joylangan) — hisobga olinmagan.
Vaqt 2 yadroli serverda 2 ta kroy parallel ishlaganda o'lchangan; bitta kroy alohida — tezroq.

**Takroriy o'lchovlar haqida (halol):** optimizator vaqt byudjeti bilan ishlaydi, shuning uchun bir nechta chegaraviy
kroyda (1034 Sarvar op4 — 109 detal, 1096 Sarvar op8 — 184 detal, 1040 Izzat op16, 1076 Jahongir op6) natija
kompyuter yuklamasiga qarab ±1 list tebranadi: oxirgi sozlashlar davomidagi to'rt o'lchovda jami 1185–1189 list,
«ko'p» kroylar soni 0–3; yakuniy kod bilan — 1186 list (15 kroyda kam, 1 da ko'p: 1034 Sarvar op4). Bu kroylarda list tejash qidiruvi yechimga juda yaqin (ortiqcha 1.5–5 % list) — u holda qidiruv bir marta
uzaytiriladi (standart rejimda kroy jami ≤ 17 s).

«Detskiy kravat» (19 detal, 2750×1830): ikkala dastur ham 2 list; 1-list to'ldirish — MebeliX 92.83 %
(«Максимальное» rejimda 93.18 %), avvalgi 93.87 %. Oxirgi listdagi qoldiq — bitta 4.84 m² bo'lak.

## 2. Kromka (EL) va CNC (XNC)

| Tekshiruv | Natija |
|---|---|
| Kromka: ish metri va material metri (ortiqcha, minimal uzunlik, chiqindi %, yaxlitlash kodi) | 303 / 303 operatsiya aynan mos |
| CNC: teshiklar soni | 8 359 / 8 360 dastur mos |
| CNC: frezalash metri (yoylar, paz o'tishlari) | 8 360 / 8 360 mos |
| CNC: arra (paz) metri | 8 360 / 8 360 mos |

## 3. Bu bosqichda optimizatorga nima qo'shildi

1. **Qoldiqni yig'ish.** Oxirgi (to'liq bo'lmagan) listda detallar iloji boricha tor polosaga yoki burchakka zich
   joylanadi (ikkilik qidiruv + «burchak» variantlari), bo'sh joy bitta katta деловой qoldiq bo'ladi. Chiqindisi
   yetarli boshqa listlarda ham. Baholash — kartadagi bilan bir xil qoida (деловой qoldiqlar jami maydoni,
   «Размер остатка с учетом торцовки»), jami maydon hech qachon kamaymaydi; bir xil kartalar (paket) birga o'zgaradi;
   «По длине/ширине предпочтительно» da oxirgi list afzal yo'nalishda qoladi.
2. **Listni tejash qidiruvi** («bin completion» + qiymat tuzatish) uchun vaqt: «Стандарт» 7–9 s (faqat list kamayishi
   mumkin bo'lganda); yechimga juda yaqin bo'lsa bir marta uzaytiriladi (jami ≤ 17 s); juda zich bir listli holatda
   2 s bilan cheklanadi. Avval yomon bo'lgan kroylar (1040 op16, 1076 op6, 1096 op8) odatda avvalgi dastur darajasida.
3. **Qat'iy muddatlar.** Ko'p mayda detal (listda 100+ dona) bo'lganda ustunli qidiruv muddatga qaramay
   45–78 s gacha cho'zilardi — endi har qidiruv muddatda to'xtaydi (400 mayda detal «Быстро»: 48 s → 2.3 s).
4. **Xato tuzatildi:** «Мин. ширина полосы» qolgan joydan katta bo'lsa, eski 3 bosqichli algoritm polosani list
   tashqarisiga chiqarardi — endi bunday polosa ochilmaydi.
5. Mustaqil tekshiruv (alohida agent): kod ko'rib chiqildi va tasodifiy holatlar bilan sinaldi (propil 0–5,
   torsovka 0–15, burilishlar 2–6, guruhlar, qoldiq-listlar, tekstura aralash, ikki xil list). Topilgan 4 kamchilik
   (muddatlar, qoldiq bahosi, afzal yo'nalish, min. polosa eni) tuzatildi; tuzatishdan keyin 1 410 holat — tekshiruv
   xatosi 0, detal yo'qolmaydi/takrorlanmaydi, daraja chegarasi buzilmaydi, деловой qoldiq 534 holatda ko'paydi.

## 4. Qayta tekshirish

```bash
cd tools/bench && python3 compare.py normal      # ~8 daqiqa
cd backend && pytest -q                          # 91 test
```

## 4a. Ko'p-listli kroylar (qoldiq/qirqim + butun list) — 2026-10-01 (GibLab bilan jonli solishtirishdan)

Real GibLab ni (GibLabLocal) ochib solishtirilganda: **«Листы и остатки» ro'yxati — ustuvorlik tartibi**. Kroy ro'yxat
tartibida (1-qator birinchi) ketadi; GibLab ro'yxatni ochishda **soni bo'yicha o'sish** tartibida saralaydi (cheklangan
qoldiq/qirqim listlar birinchi, `10000` «cheksiz» list oxirida). Korxonaning 44 ta ko'p-listli kroyida tekshirildi:
soni bo'yicha o'sish 42/44 ga mos (2 ta istisno — hech bir detal sig'maydigan mayda list), yuza bo'yicha — 27/44.
Importer (`plugins/legacy_project.py`) endi shu tartibni qo'llaydi; avval fayl tartibi (cheksiz list birinchi) olinib,
qoldiqlar umuman ishlatilmasdi.

Optimizator (`services/optimizer.py`) o'zgarishlari: (1) `_job_key` — ishlatilgan **material maydoni (m²)** ham hisobga
olinadi (bir xil o'lchamli listlarda hech narsa o'zgarmaydi); (2) list tartibi variantlari (`_stock_orders`): ro'yxat
tartibi / cheklanganlar yuza bo'yicha kamayish va o'sish / faqat butun listlar; (3) `_refill_limited` — oxirgi butun
listdagi detallar ishlatilmagan qoldiq listga ko'chiriladi; (4) `_limited_first` — eng katta qoldiq listga bir nechta
muqobil detallar to'plami sinab ko'riladi. Natija (`tools/bench/compare_stock.py normal`, 44 kroy):

| | Ishlatilgan material | Kam | Teng | Ko'p |
|---|---|---|---|---|
| Avval (fayl tartibi) | MebeliX **608.2 m²** / avvalgi 581.9 m² | 1 | 36 | 7 |
| Hozir | MebeliX **574.0 m²** / avvalgi 581.9 m² | 6 | 36 | 2 |

Qolgan 2 kroyda (1014 so'qoq, 1071 Mirshoxid kuxniya) GibLab juda zich joylashuv topgan (detallar 8.8 % chiqindiga
sig'adi). `compare.py normal` (bitta list turi) o'zgarmadi: 1186 / 1212 list, xato 0. Tasodifiy sinov (`fuzz`: 100 ta
aralash-listli holat) — 0 xato.
Jonli tekshiruv («1230 Jamshid 04 shkaf»): 1-kroy — 2140×1140 qoldiq list, F 68.55 %, kesish 15.95 m (GibLab: aynan shu);
2-kroy — 1770×1830 (F 92.12 %) + 2750×1830, jami F 79.91 % (GibLab: aynan shu).

## 4b. Katta korpus — 1248 fayl (`giblab project` papkasi), 2026-10-02

`BENCH_PROJECTS=<papka> BENCH_DEDUP=1 BENCH_OUT=corpus_big.json python corpus_build.py` → 1877 kroy (52 takror olib tashlandi),
59 690 detal, avvalgi (GibLab) natijasi 5825 list; `BENCH_CORPUS=corpus_big.json python compare.py normal big` (16 yadro, 326 s,
tekshiruv xatosi **0**, eng sekin kroy 17 s). Korpus «birinchi list»ni oladi, shuning uchun zaxirasi cheklangan (qoldiq/qirqim birinchi
turgan) 51 kroy o'lchovga mos emas (ular uchun `compare_stock.py` ishlatiladi); asosiy natija — cheksiz listli kroylar:

| To'plam | Kroy | MebeliX list | GibLab list | Kam / teng / ko'p | деловой qoldiq | Kesish uzunligi |
|---|---|---|---|---|---|---|
| Cheksiz list (qty ≥ 100) | 1821 | **5584** | 5639 (**−55**, −1.0 %) | 45 (−88) / 1743 / 33 (+33) | **3622 m² vs 3188 (+13.6 %)** | 104 444 m vs 106 531 (−2.0 %) |
| Hammasi (artefaktlar bilan) | 1872 | 5774 | 5803 (−29) | 51 / 1778 / 43 | 3664 vs 3214 | 105 870 vs 108 026 |

Eng yirik «ko'p» holat — `1 Behzod` 109 detalli kroy: 7 list ↔ 6 (GibLab to'ldirishi 95.5 %). Xodimlar parametrlari: propil 3, burilish 4, min. obrezka 5.

## 5. Hali farq qolgan joylar

* «Быстро» rejimida 23 kroyda 1 list ko'p (standart rejimda — 0–2 chegaraviy kroy). Xodimlar uchun standart rejim.
* Chegaraviy kroylarni barqaror qilish g'oyalari: ko'p yadroli kompyuterda list tejash qidiruvlarini (bin completion va
  SVC) parallel jarayonlarda ishlatish; ichki qidiruvlarda vaqt o'rniga «ish hajmi» chegarasi (natija takrorlanuvchi).
* 74 kroyda деловой qoldiq avvalgisidan kam (jami 382 kroyda esa 101 m² ko'p): avvalgi dastur ba'zan bir nechta
  o'rta qoldiq qoldiradi; MebeliX bitta katta bo'lakni afzal ko'radi.

## 2026-10-04 (v2.7, postprotsessor ishlaridan keyin — optimizator o'zgarmagan, nazorat o'lchovi)
`compare.py normal`: 397 kroy | MebeliX 1191 list, avvalgi 1212 | kam 14, teng 378, ko'p 5 | tekshiruv xatosi 0 | joylashmagan 0.
`compare_stock.py normal`: 44 ko'p-listli kroy | 573.98 m² (avvalgi 581.90) | kam 6, teng 36, ko'p 2 | xato 0.

## 2026-11-10 (qoldiq + butun listlar: `_limited_prefix`)
`compare_stock.py normal`: 44 ko'p-listli kroy | 573.47 m² (avvalgi tizim 581.90; oldingi o'lchov 573.98) | kam 6, teng 37, ko'p 1 (1071) | tekshiruv xatosi 0 | joylashmagan 0.
