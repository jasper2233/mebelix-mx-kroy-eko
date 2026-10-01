# L. Qabul testlari (raqamlar bilan)

Backend: `backend/tests/test_v2.py` — **31 test, hammasi yashil**. Quyidagi jadval — nima tekshirilishi
va kutilgan qiymat. Frontend e2e (Playwright) ssenariylari — L3.

## L1. Hisob-kitob qoidalari

| # | Holat | Kutilgan |
|---|---|---|
| 1 | List 1200×1000, torsovka по длине 20, propil 10 | foydali en **940** (yuqori 30 + past 30) |
| 2 | Xuddi shu, torsovka по ширине 20 | foydali uzunlik **1140** |
| 3 | Torsovka 0 | foydali = list; propil qo'shilmaydi |
| 4 | end_offset_bottom=0, end_offset_right=10, trim 2/2, propil 3 | en 1830−5 = 1825, uzunlik 2750−5−13 = 2732 |
| 5 | 300×300, kromka 2 mm + prifugovka 1 mm ОВ+ОН, rejim blank | detal 300×302, prifug. 300×298, zag. 300×300, pil. 300×300 |
| 6 | … rejim detail | 300×300 / 300×296 / 300×298 / 300×298 |
| 7 | … rejim jointed | 300×304 / 300×300 / 300×302 / 300×302 |
| 8 | «Detskiy kravat» kromka KP-1/19-S (ortiqcha 20, min 100) | material **10.8 m**, ish **10.4 m** (GibLab bilan bir xil) |
| 9 | Ikkinchi kromka !СмЧт | ish 3.0 m, material 3.1 m |
| 10 | Tomon 50 mm, min uzunlik 100, ortiqcha 20 | ish 0.05 m; material 0.14 m |
| 11 | Yaxlitlash kodlari | 10.8222 → [0.0] 10.8; ⌈0.0⌉ 10.9; ⌊0.00⌋ 10.8999→10.89; [0] 3.5→4 |
| 12 | Detallar 1 m², taxminiy 90 %, m² narxi 100 | sarf 1.1 m², material narxi 110 |
| 13 | CL polosa 1600, torsovka 20, propil 10 | foydali **1540** |
| 14 | Narx listlar bo'yicha 500 000 | = listlar × 500 000 |
| 15 | Narx m² bo'yicha 100 000 | = (material − delovoy) m² × 100 000 |
| 16 | Yaxlitlash «По длине 1/2» | oxirgi list 0.5 yoki 1; jami − 1 < n ≤ jami |
| 17 | МК=1, Сони=3, mahsulot 2 | kroyga 5 dona, ИК 5 |
| 18 | Qoldiq tasnifi (1000/500, 0.5 m²) | 2687×1820 → delovoy; 1000×500 → delovoy; 1200×400 → chiqindi; (300/300, 1 m²) 800×600 → qoldiq |

## L2. Optimizator

| # | Holat | Kutilgan |
|---|---|---|
| 19 | «Detskiy kravat» 19 detal, 2750×1830, propil 3, torsovka 2, min kesish 5 | 2 list, hech narsa qolmaydi, 1-list ≥ **92 %** (hozir 92.83; GibLab 93.87) |
| 20 | Barcha kartalar | detallar ustma-ust tushmaydi, foydali zona ichida |
| 21 | Tekstura ✓ (aylantirmaslik) | joylashuv o'lchami aynan 1000×300 |
| 22 | 995 mm detal 1000 mm polosada, min kesish 5 | joylanmaydi (5 mm tilim); min kesish 0 bo'lsa — joylanadi |
| 23 | max_rotations = 2 | buyruqlarda C/P daraja ≤ 2 |
| 24 | Polosa saralash «По убыванию», yo'nalish по длине | C1 balandliklari kamayish tartibida |
| 25 | first_cut = По ширине | barcha kartalar `first_cut == "width"`, buyruqlar `R0 90` bilan |
| 26 | max_strip_length 2000, list 2750×1830 | yo'nalish majburan en bo'yicha |
| 27 | 40 ta bir xil detal | karta takrorlanadi (C > 1), jami 40 |
| 28 | Qoldiq «с учетом торцовки» ☐ | qoldiq maydoni ✓ holatdagidan katta |
| 29 | Blok: 4 dona, uzunlik bo'yicha, min=max=2, blok propili 2 | 2 blok (2·400+2), kartada 4 joylashuv, oraliq 2 mm |
| 30 | «До кроить»: 1 list bilan kroy (qolganlar bor) → listlar 5 ga oshirib qolganini kroy | yangi kartalar qo'shildi, 1-karta o'zgarmadi, ИК jami 19 |

## L3. Import va API

| # | Holat | Kutilgan |
|---|---|---|
| 31 | Buferdan 2 qator (1-da «Ясень 1 мм» ОВ va ОЛ) | 2 detal; yangi EL «Ясень 1 мм» yaratildi, ОВ/ОЛ unga bog'langan; sarlavha qatori tashlab ketildi |
| 32 | GibLab XML (namuna) | rejim detail; CS nomi material dan; propil 4.4, aylanish 4; cTrimEL=−1 → None, cTrimEW=0 → 0; по длине предпочтительно; listlar bo'yicha narx, 1/2 по длине; taxminiy 90 %; listlar [sheet, business]; detal 720×280×2 tekstura, ОВ/ОН → EL; EL ortiqcha 20, min 50, qalinlik 1, en 22, chiqindi 10 % |
| 33 | XNC ifodalar | `dx/2 + origin.x` = 310; `allowanceT + 37` = 39; `dz > 10` = 1; «213» → R2 Q1 G3 |
| 34 | API: yangi loyiha | 1 mahsulot + 1 CS («Material1») |
| 35 | 2 ta EL qo'shish | belgilar A, B |
| 36 | Paste 19 detal → optimize → stock-table → izoh «da» → sarlavha → SVG → etiketka → hisobot → undo | hammasi 200; etiketkalar 19, shtrixkod raqamli |
| 37 | `PUT /api/settings/cs_cut/default {kerf 4.4}` → yangi loyiha | CS propil 4.4 |

## L4. Frontend e2e (Playwright) — Claude Code yozadi

1. **Tezkor kiritish**: Детали jadvalida `720 Tab 280 Tab 10 Tab Space Tab Space…` → qator yaratiladi,
   Ткт almashadi, ОВ ga A kromka tushadi, oxirgi katakda Enter → yangi qator.
2. **Bufer**: Excel matnini Ctrl+V → detallar + yangi EL.
3. **Kroy**: «Раскроить» → status qatori `№:1/2 S:2750/1830 …`, miniatyuralar, Таблица команд; Home/End bilan kartalar.
4. **Detalni bosish** → shu detalning hamma nusxalari ajraladi; ikki marta bosish → xossalar oynasi.
5. **До кроить**: detal qo'shish → faqat yangi karta qo'shiladi.
6. **Undo/Redo** Ctrl+Z/Ctrl+Y — jadval holati qaytadi; tugmalar faol/nofaol holati to'g'ri.
7. **Hisobot**: PDF 1-sahifada «Требование на склад», CS bo'limida kartalar va legenda.
8. **Import GibLab**: haqiqiy `.project` fayl → detallar soni va kromkalar mos.
9. **Yorliqlar**: `E_HOTKEYS.md` dagi har bir yorliq uchun kichik test.
