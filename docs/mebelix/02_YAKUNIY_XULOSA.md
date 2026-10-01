# Yakuniy xulosa — MebeliX Kroy v2 (GibLab'ni chuqur o'rganish natijasi)

Sana: 2026-09-30. Muallif: Claude (Cowork). Tayyorlandi: Diyorjon Shukriddinov uchun.

## 1. Nima o'rganildi

| Manba | Holat | Nima olindi |
|---|---|---|
| GibLab ichki yordami (Справка) — 24 bo'lim: operatsiyalar (O, CL, CS, EL, GR, XNC, LB), o'lcham rejimlari, pripusk, katalog, etiketkalar, **.project formati**, qoldiqlar hisobi (1C), importlar, yangilanishlar tarixi | ✅ to'liq o'qildi | parametrlar ma'nosi, formulalar, yorliqlar, fayl formati |
| Yordam rasmlari (torsovka, murakkab polosa, burilishlar, saralash, paket, qoldiq torsovkasi, detal tomonlari, o'lcham rejimlari) | ✅ ko'rildi | geometrik qoidalar |
| GibLab video-darsi (6 daq., dastur ichida) | ✅ 30+ kadr ko'rib chiqildi | xodim ish oqimi, «До кроить», detalni bosib ajratish, katalog oynasi |
| Xodimlar hisobi (ekran): barcha tablar, dialoglar, chop sozlamalari, mahsulot xossalari | ✅ | 13 ta yangi skrinshot, xodim odatlari |
| Internet: GibLab servis hujjati (stanoklar ro'yxati), InformDom maqolasi (2017), mebel-pro eksport hujjati | ✅ | qo'llab-quvvatlanadigan stanoklar va imkoniyatlar ko'lami |
| YouTube videolari («Початковий урок», «Оформлення замовлення», «Свердління та пазування», «Настройка кабинета») | ❌ o'qib bo'lmadi (veb vosita cheklovi) | — (nomlari ro'yxatda; kerak bo'lsa o'zingiz ko'rib, xulosani yozing) |
| promebelclub.ru forumi | ❌ 403 (sayt ruxsat bermadi) | — |

> Mualliflik huquqi: yordam matnlari **ko'chirilmadi**, faqat mazmuni o'z so'zlarimiz bilan va
> formulalar/parametrlar (funksional faktlar) sifatida yozildi. Paketda GibLab kodi, ikonkasi,
> yordam rasmlari yo'q. Skrinshotlar — sizning hisobingizdagi ekranlar (ichki ma'lumot uchun).

## 2. Eng muhim topilmalar

1. **v1 da xatolar bor edi** (endi tuzatildi):
   * «Торцовка по длине» — listning **yuqori** chetidan (enni kamaytiradi), «по ширине» — **chap** chetdan;
     qarama-qarshi tomonda minimal otstup; foydali = o'lcham − (torsovka+propil)×2.
   * Kromka: **ish = sof uzunlik**; **material = max(tomon, min) + 2×ortiqcha, × (1+chiqindi%)**.
     «Detskiy kravat» bo'yicha GibLab bilan **aynan** mos: 10.8 m / 10.4 m.
   * Taxminiy sarf = detallar maydoni × (2 − %/100); material miqdori = sarf − delovoy qoldiqlar.
   * «Расчет стоимости по листам» — narx maydoni ma'nosini o'zgartiradi (list ↔ m²).
2. **Optimizator** qayta yozildi: rekursiv gilyotina (2–6 daraja), min kesish qoidasi, polosa cheklovlari,
   saralash, bloklar, takrorlash/paketlar, oldindan ko'rish. Natija «Detskiy kravat»: **92.83 %** (GibLab 93.87 %).
3. **Xodimlar detallarni Bazis-Mebelshik'dan oladi** (`product.import = bm.1.86`, «GibLabExport» skripti).
   ⇒ MebeliX'ga **GibLab/Bazis XML importi** qo'shildi — eski loyihalarni ko'chirish ham shu bilan.
4. **Narxlar GibLab'da ishlatilmaydi** (hamma loyiha 0 UZS) — narx MES'da bo'ladi; MebeliX narxni
   katalogdan avtomatik oladi, lekin bu birinchi ustuvorlik emas.
5. **Katalog ishlamayapti** (Dropbox tokeni eskirgan) — material nomlari qo'lda. MES katalogi bu muammoni yechadi.
6. Kromka **rangi va nomi vizual belgi** sifatida ishlatiladi («!СмЧт» — to'q sariq).
7. Xodim tezligi **klaviaturaga** bog'liq: Space (tekstura/kromka), Shift+Space, Tab/Enter oqimi, Ctrl+V —
   bular aynan takrorlanishi shart (`E_HOTKEYS.md`).
8. **Savol:** kromka qalinligi GibLab'da 0 (PVC 1 mm uchun). Texnolog bilan aniqlang (`M_STAFF_HABITS.md`).

## 3. Paket tarkibi (bu zip)

```
00_README_UPDATE.md             — nima va qanday ishlatish
01_UPDATE_PROMPT_CLAUDE_CODE.md — Claude Code'ga beriladigan yangilanish prompti
02_YAKUNIY_XULOSA.md            — shu fayl
docs/A..O                       — lug'at, qoidalar, optimizator, UI v2, yorliqlar, model, import,
                                  hisobot/etiketka, MES, XNC, boshqa operatsiyalar, testlar,
                                  xodim odatlari, o'zgarishlar ro'yxati, ish oqimi
backend/                        — to'liq v2 backend (31 test yashil)
screens_v2/                     — 13 yangi skrinshot + MebeliX optimizator natijasi namunasi
```
Eski zip (v1) **o'zgartirilmadi**.

## 4. Tavsiyalar (keyingi qadamlar)

1. Claude Code'da avval **N1 tuzatishlarni** kiriting — xodimlar natijani GibLab bilan solishtiradi.
2. Xodimdan **haqiqiy `.project` fayl** oling (GibLab → Експортировать yoki Bazis eksporti) — import testiga.
3. Arra stanogi modelini va (bo'lsa) namunaviy dastur faylini bering — postprotsessor uchun.
4. 1–2 hafta **parallel ishlatish**: bir loyihani GibLab'da ham, MebeliX'da ham kroy qilib, listlar soni va
   kromka metrlarini solishtiring (farq > 1 % bo'lsa — menga/Claude'ga yozing).
5. Xodimlarning ustun nomlari profilini («детал номи», «Сони», …) standart qilib qo'ying.

## 5. Ochiq qolgan joylar (ma'lumot yetishmadi)

* Nesting (CN) — GibLab'da test holatida; birinchi bosqichga kiritilmadi.
* Postprotsessorlarning aniq formatlari (stanokka bog'liq).
* «Большой пакет» ning GibLab'dagi aniq algoritmi — biz takroriy kartalarni afzal ko'rish bilan modellashtirdik.
* YouTube darslari (o'qib bo'lmadi) — asosiy ma'lumot ichki yordam va video-darsdan to'liq olindi.

## 6. Eslatma: GibLab'dagi harakatlarim

Ko'rib chiqish paytida ikki tugma tasodifan ta'sir qildi: kroy kartasining **izoh** (F2) tugmasi va
operatsiyalar **saralash** oynasi (tur bo'yicha saralandi). Ikkalasi ham «Отменить» bilan qaytarildi —
operatsiyalar tartibi avvalgidek (CS, EL, EL, CS, XNC, XNC, XNC), izoh matni «da» o'zgarmagan.
Ko'rinishicha, hisobot ochilganda GibLab loyihani avtomatik saqlagan («Сохранить» tugmasi nofaol bo'lib qoldi). «Detskiy kravat» loyihasini bir ko'z yugurtirib
tekshirib qo'yishingizni tavsiya qilaman. Boshqa hech narsa o'zgartirilmadi, litsenziya/hisob sozlamalariga tegilmadi.
