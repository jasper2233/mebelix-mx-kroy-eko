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
| **Стандарт** (standart) | **1185–1187 / 1212** (−25…−27 list, ≈ −2.2 %) | 15 | 380–382 | 0–2 | 0 | 12.5–17 s |
| Быстро | 1212 / 1212 | 11 | 363 | 23 | 0 | 1.9 s |

Listlar soni teng bo'lgan kroylarda («Стандарт», 382 ta):

| Ko'rsatkich | MebeliX | Avvalgi | Farq |
|---|---|---|---|
| Деловой qoldiq (≥ 1000×500, ≥ 0.5 m², korxona sozlamasi) | **751–753 m²** | 652 m² | **≈ +15 %** (≈ 125 kroyda ko'p, ≈ 75 da kam) |
| Kesish uzunligi (arra yo'li) | **22 026–22 153 m** | 22 287–22 457 m | ≈ −1.3 % |

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

## 5. Hali farq qolgan joylar

* «Быстро» rejimida 23 kroyda 1 list ko'p (standart rejimda — 0–2 chegaraviy kroy). Xodimlar uchun standart rejim.
* Chegaraviy kroylarni barqaror qilish g'oyalari: ko'p yadroli kompyuterda list tejash qidiruvlarini (bin completion va
  SVC) parallel jarayonlarda ishlatish; ichki qidiruvlarda vaqt o'rniga «ish hajmi» chegarasi (natija takrorlanuvchi).
* 74 kroyda деловой qoldiq avvalgisidan kam (jami 382 kroyda esa 101 m² ko'p): avvalgi dastur ba'zan bir nechta
  o'rta qoldiq qoldiradi; MebeliX bitta katta bo'lakni afzal ko'radi.
