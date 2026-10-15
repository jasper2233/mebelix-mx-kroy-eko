# V. Onlayn GibLab bilan ekranma-ekran solishtirish (v2.5, 2026-10-03)

Foydalanuvchi talabi: «har bir ochilgan oynani onlayn GibLab bilan solishtir, farqlarni tuzat; tizim GibLab bilan bir xil
bo'lsin (xodimlar qiynalmasin), qo'shimcha qulayliklar va MES integratsiyasi bilan». Sertifikat/kalitga tegilmaydi.

## Usul
- Chrome kengaytmasi (Claude in Chrome) bu sessiyada **ulanmadi** → onlayn GibLab jonli ochilmadi. Ma'lumotnoma sifatida
  onlayn GibLab skrinlari ishlatildi: `screens/` (33 ta) va `docs/mebelix/screens_v2/` (13 ta).
- MX Kroy ekranlari Playwright bilan olindi (alohida baza, «5040 kravat.project» importi — CS×2, EL×2, XNC).

## Topilgan farqlar va holat
| № | Joy | Farq | Holat |
|---|---|---|---|
| 1 | Chap panel (akkordeon) | «Печать отчета» / «Настройки» / «Справка» ochilganda menyu pastda, o'rtada katta bo'sh joy qolardi. GibLab'da faol bo'lim yuqoriga ko'tariladi, menyu darhol uning ostida | ✅ `app/Layout.tsx` |
| 2 | Operatsiyalar jadvali | Pastki tab (Параметры, Раскрой, XNC) almashganda yuqori jadval 3–5 qatorga qisqarardi; GibLab'da balandlik o'zgarmaydi | ✅ `.top { flex: 0 0 auto }` |
| 3 | CS «Детали» | Kromka ustunlarida uzun nom kesilardi; GibLab'da qator balandlashib, nom to'liq ko'rinadi | ✅ `wrapText + autoHeight` |
| 4 | «Раскроить»dan keyin | Har kroydan keyin «Деловые остатки → склад» oynasi o'zi ochilardi (GibLab'da yo'q) | ✅ standart o'chiq (`remnant_confirm=False`); asboblar panelidagi tugma va «Настройки → Общие» katakchasi qoldi |
| 5 | Matnlar | Foydalanuvchiga ichki savol raqamlari ko'rinardi («вопрос Q-1/Q-2/Q-5/Q-15», «уточняется») | ✅ oddiy matnga almashtirildi (`i18n_cs_w2.py`) |
| 6 | XNC «Параметры» | Parametrlar yarim ekranni egallar, chizma kesilardi; yorliqlar «DX/DY/DZ», koordinata boshi «LT…» | ✅ tor chap ustun (330 px) + chizma qolgan joyda; «Длина (DX)», «Ширина (DY)», «Толщина (DZ)», «Левый верхний угол» … |
| 7 | «Режим ввода размеров» oynasi | Qisqa variantlar («заготовки») | ✅ sarlavha joriy rejim bilan, variantlar to'liq: «Режим ввода размеров заготовки» … |
| 8 | «Выберите тип операции» | «Отмена» tugmasi yo'q edi | ✅ |
| 9 | EL «Детали» | «Товар» ustunida operatsiya turi yo'q («(CS) LDSP…») | ✅ backend qatorga `op_type` qo'shildi |
| 10 | Loyihalar ro'yxati | Ctrl+A → Del: Del eski tanlov bilan ishlardi | 🟡 Del endi do'kondagi joriy tanlovni oladi; e2e `lists.spec.ts` (Ctrl+A dan keyin tanlov 1 ga qaytadi) hali yiqiladi — oldindan bor muammo, sababi AG Grid ichida, aniqlanmagan |

### 2-qism (2026-10-04, foydalanuvchi ko'rsatgan farqlar)
| № | Joy | Farq | Holat |
|---|---|---|---|
| 11 | Import / eksport belgilari | Ma'nosi teskari edi. Endi butun tizimda **import — pastga strelka** (kirish), **eksport — tepaga strelka** (chiqish): loyiha menyusi, loyihalar ro'yxati, Excel/katalog, zaxira, XNC shablonlari, etiketkalar, ZPL, OEE CSV, import profillari | ✅ |
| 12 | Postprotsessor belgisi | Hujjat belgisi edi → **mikrosxema** (`Cpu`): CS/CL/CN «Раскрой» asboblar paneli, XNC paneli, «Настройки → Постпроцессоры»; «Настройки» menyusidagi har bir bandga belgi qo'shildi | ✅ |
| 13 | Kroy kartasida kromka | Chiziq qalin edi → ingichka (ekran `fs/9`, chop `fs/6`); ko'rsatkichlar qatoriga **«Кромка» katakchasi** (yoqish/o'chirish; CS va CL) | ✅ |

### 3-qism (2026-10-04, jonli onlayn GibLab bilan — Chrome kengaytmasi ulandi)
Onlayn GibLab'da ko'rildi (faqat ko'rish; «test uchun/test» loyihasiga CL, SP, GR, O, LB operatsiyalari qo'shildi — foydalanuvchi ruxsati bilan).
Har ekranda tugmalar `title` lari (funksiyalar ro'yxati) o'qildi.
| № | Joy | Farq | Holat |
|---|---|---|---|
| 14 | Loyihalar ro'yxati | Sana «чт 16.07.2026», narx «0 UZS», holat — oddiy matn, tur belgisi ustuni, menyu ostida «двойной клик…» yordami; loyiha ochilmaganda «Печать отчета» yo'q | ✅ |
| 15 | Operatsiyalar paneli | Tezkor qo'shish: faqat CS, EL, GR, XNC (CN/CL/O — «+ Операция» orqali) | ✅ |
| 16 | CS «Детали» | «Д-на/Ш-на» — sarlavha rangli, qiymatlar qora | ✅ |
| 17 | «Печать отчета» | Sozlamalar oynalarda: «Поля страницы», «Настройки печати», «Изделия», «Настройки печати операций» → (CS) [Общие / Карты кроя / Заголовок карт кроя], (CL)…; hisobot to'liq kenglikda | ✅ |
| 18 | «Настройки» | «Режимы ввода деталей» — alohida oyna (4 variant); «Загрузить / выгрузить настройки»; menyu belgilari | ✅ |
| 19 | XNC «Стоимость» | Ikki ustun, GibLab yorliqlari (teshik/freza/arra narxi, soni/uzunligi, qiymati; qo'shimcha, bir dona, soni, operatsiya) | ✅ |
| 20 | EL «Детали» | Navigatsiya: Первая / Предыдущая / Следующая / Последняя; «Общие действия» — «Отмена» | ✅ |
| 21 | Kroy qilinmagan «Раскрой» | Katta tugma o'rniga «Раскроить» havolasi (GibLab'dagi kabi) | ✅ («Редактирование раскроя» noldan — yo'q) |
| 22 | CL | Tab «Полосы и остатки»; standart nom «Материал1» | ✅ |
| 23 | SP «Параметры» | Material Длина/Ширина/Толщина (2200×800×1), «Режим размеров» — radio, Описание chapda, o'ng ustun GibLab tartibida | ✅ (o'lchamlar hisobga ta'sir qilmaydi — savol) |
| 24 | GR «Параметры» | Ширина/Глубина/Отступ, «Толщина пилы» — Стоимость ostida, eskizda haqiqiy o'lchamlar, Описание chapda; nom «Пазование1» | ✅ |
| 25 | O | Bitta sahifa: parametrlar (Владелец, narxlar, Описание) + «Материалы» jadvali; nomsiz | ✅ |
| 26 | LB | Standart nom «Этикетки: Детали и остатки» | ✅ (bizda ko'proq: jonli ko'rish, ZPL, vizual redaktor) |
| 27 | Kroy qoldig'i | Qoldiq iloji boricha list bo'yi/eni bo'ylab butun polosa (burchak bo'lak ×0.75 baholanadi) | ✅ korpus: listlar o'zgarmadi (1191=1191), xato 0 |

Hali qilinmagan (keyingi qadam): bo'sh jadvallarda «Добавить / Вставить / Справка» havolalari; XNC asboblar paneli («Выбрать деталь», «Кодирование», «Отменить деталь»); sarlavhadagi sana «сб 26.09.2026» ko'rinishi.
(2026-10-15: «Листы и остатки» — «Сортировка» va «Удалить неиспользуемый материал» allaqachon bor — `CsSheets.tsx`; ko'p-kroyli loyihalar va onlayn solishtiruv — `X_1015_ONLAYN_AUDIT_MCP.md`.)

Mos kelganlari (o'zgartirilmadi): loyiha sarlavhasi, operatsiyalar ustunlari, CS tablari va ustunlari, «Листы и остатки», kroy
ko'rsatkichlari qatori (№/S/C/Ср/LT/F), «Таблица команд/карт», EL parametrlari, XNC «Шаблон» (palitra + «Программа»), «Изделия»,
«Общие действия», «Импорт из других программ», detal xossalari, ustun sozlamalari, postprotsessor stanoklari ro'yxati.
Ataylab farqli: hisobotni ochganda takror XNC kodlari haqidagi so'rov (GibLab Local xulqi), «Заказать»/MES bloklari, «Качество раскроя».

## Qolgan ish (jonli onlayn GibLab kerak)
Skrinlarda yo'q oynalar (CL/CN/SP/GR/LB/O ichki sahifalari, «Настройки» dialoglari: XNC Редактор, Модуль заказов, Dropbox va h.k.,
hisobot sozlamalari dialoglari) — kengaytma ulangach har birini ochib solishtirish.
