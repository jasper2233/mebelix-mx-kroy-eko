# M. Xodimlar GibLab'dan qanday foydalanmoqda (kuzatuvlar)

Bu — korxonaning GibLab hisobini ko'rib chiqishdan olingan faktlar. Dizayn qarorlari shularga tayanadi.

## M1. Ish oqimi

1. Mebel **Bazis-Mebelshik** da loyihalanadi → «GibLabExport» skripti (v1.86) bilan eksport →
   GibLab'da «Импорт БМ» (mahsulot xossasida `product.import = bm.1.86`).
   Detal nomlari eksportdan: «№ Панель», «№ Панель1»; XNC operatsiyalari ham eksportdan keladi
   (kodlar `0000x005x0`, `0000x009x0`, `0000x010x0` — panellardagi frezalash).
2. GibLab'da: material nomi qo'lda yoziladi (masalan «LDSP BELI KARONA TEKSTURA», «XDF 2800x2070 mm 5.8 kv»),
   kod ko'pincha bo'sh. **Tovarlar katalogi ishlamaydi** (Dropbox tokeni eskirgan — xato chiqadi).
3. Kromka operatsiyalari: bir xil kod `KP-1/19-S`, nomlari «kromka PVC 1-19 Sasna» va
   «**!СмЧт** kromka PVC 1-19 Sasna». «!СмЧт» — maxsus belgi (ehtimol «смотри чертёж» — chizmaga qarang),
   jadvalda **to'q sariq rangda** ajralib turadi → xodimlar kromka nomi va rangini **vizual belgi** sifatida ishlatadi.
   MebeliX: EL rangi va nomi erkin, jadvalda rang bilan ko'rsatilsin.
4. Kroy → kartalarni ko'rish → **«KROYGA»** chop profili bilan PDF (10 sahifa: talabnoma, CS detallar/listlar,
   kartalar, kromka, XNC chizmalari) → sexga.
5. Narxlar **ishlatilmaydi**: barcha loyihalarda 0 UZS, holat «Не заказан». ⇒ Narx hisobi MES da bo'ladi;
   MebeliX'da narx maydonlari bor, lekin birinchi bosqichda ixtiyoriy (MES katalog narxlari bilan avtomatik).
6. Karta izohi (F2) ishlatiladi (masalan «da»).

## M2. Sozlamalar (xodimlar profili → MebeliX standartlari)

| Parametr | Qiymat |
|---|---|
| Valyuta | UZS |
| O'lcham rejimi | detal (с кромкой) |
| List | 2750×1830 (LDSP 16 mm), XDF 2800×2070 |
| Propil | **3 mm** |
| Torsovka | 2 / 2 mm, minimal otstup = torsovka |
| Yo'nalish | Любое |
| Tekstura hisobi | ✓ (lekin detallarda Ткт ko'pincha ☐) |
| Murakkab polosalar | ✓ |
| Aylanish | 6 |
| Paket balandligi | 40 mm (LDSP 16 → karralik 2) |
| Katta paket | ✓ |
| Polosalar saralash | По убыванию; polosa ichida — Не сортировать |
| Polosa eni min/max, uzunlik max | 0 / 0 / 10000 |
| Min kesish | 5 mm |
| Qoldiq | 1000 × 500, delovoy 0.5 m², «с учетом торцовки» ✓ |
| Min detal | 30 mm |
| Taxminiy to'ldirish | 90 % |
| Kromka (EL) | en 19, **qalinlik 0**, prifugovka 0, ortiqcha 20, min 100, yaxlitlash [0.0] |

> ⚠️ **Savol (texnolog bilan aniqlang):** kromka «PVC 1-19» (1 mm) qalinligi GibLab'da **0** kiritilgan —
> ya'ni detal o'lchamidan ayirilmaydi. Agar Bazis eksporti tayyor (kromkali) o'lcham bersa, kesilgan detal
> kromkadan keyin har tomonda +1 mm kattalashadi. MebeliX'da to'g'ri qiymat qo'yilsa o'lcham avtomatik
> to'g'rilanadi (B2). Hozirgi amaliyot bilan bir xil natija uchun — qalinlik 0 qoldiring.

## M3. Ustun nomlari (xodimlar o'zlari o'zgartirgan, «Uslugiya»/«Standart» profillari)

«детал номи» (Наименование), «Сони» (Кол), «Ишлатилди» (Исп.), «Колдик» (Остаток), «Изох» (Описание),
«Махсулот» (Изделие-наименование), «Арт» (Изделие-код), «Квадрати» (Площадь).
⇒ MebeliX standart profili shu nomlar bilan kelsin; ruscha/o'zbekcha to'liq tarjima — sozlamada.

## M4. Loyihalar tartibi

Papkalar: «Ozimizni ishlar», «Yanvar 2026», «Fevral 2026», arxiv «Я 2026 arxiv».
Loyiha nomlari: buyumlar yoki mijoz nomi («Detskiy kravat», «XONTAXTA», «2 ta tortmali tumba»,
«Alisher aka», «Abror aka so'qoq kuxniya»).
⇒ MebeliX: papkalar + qidiruv + MES buyurtmasiga bog'lash (mijoz nomi MES dan).

## M5. Namunaviy loyiha «Detskiy kravat» (test ma'lumoti sifatida ishlatilgan)

Operatsiyalar: CS LDSP (14 qator, 19 dona) · EL ×2 · CS XDF (1 list, kesish 6.3 m) · XNC ×3.
Natija GibLab'da: LDSP 2 list (93.87 % / 92.31 %), kesish 32.7 m, kromka 10.8 m (ish 10.4) va 3.1 m.
Kartada qoldiq Д1 = 2687 × 1820 (2-list).

## M6. Xulosa: nimalar muhim, nimalar yo'q

* **Muhim (har kuni)**: detal kiritish/import, kromka belgilash, kroy, kartalar, chop (KROYGA), izoh.
* **Ba'zan**: XNC ko'rish/chop, XDF kroy, Excel import.
* **Ishlatilmaydi**: narxlar, onlayn buyurtma moduli, Dropbox katalog, postprotsessorlar (kuzatilmadi).
