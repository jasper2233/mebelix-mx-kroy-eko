# -*- coding: utf-8 -*-
"""W10 paketi matnlari: «Проект → Экспортировать» (.project), CS «Максимальное количество вращений» 1…6 yordami,
«Настройки → Общие» da «Минимальный размер детали». `a(kalit, ru, uz)` — i18n_src.py ichida (exec) chaqiriladi.
Interfeysda boshqa dasturlarning nomi yo'q; matnlar o'zimiz yozgan."""

# ── Eksport dialogi ──
a("export.title", "Экспорт проекта", "Loyihani eksport qilish")
a("export.project", "Файл .project (XML)", ".project fayli (XML)")
a("export.project_hint",
  "Открытый формат файла проекта: изделия, детали, материалы и листы, кромка, операции (CS, EL, GR, XNC, O, LB, SP). "
  "Результат раскроя (карты) не записывается — программа, открывающая файл, пересчитает раскрой. Перед скачиванием покажем, что не вошло в файл.",
  "Loyiha faylining ochiq formati: mahsulotlar, detallar, material va listlar, kromka, operatsiyalar (CS, EL, GR, XNC, O, LB, SP). "
  "Kroy natijasi (kartalar) yozilmaydi — faylni ochgan dastur kroyni qayta hisoblaydi. Yuklashdan oldin faylga nima kirmagani ko'rsatiladi.")
a("export.json", "Файл MebeliX (.mxk.json)", "MebeliX fayli (.mxk.json)")
a("export.json_hint", "Полная копия проекта вместе с результатом раскроя — для резервной копии и переноса между серверами MebeliX Kroy.",
  "Loyihaning kroy natijasi bilan to'liq nusxasi — zaxira nusxa va MebeliX Kroy serverlari orasida ko'chirish uchun.")
a("export.preparing", "Готовим файл…", "Fayl tayyorlanmoqda…")
a("export.file", "Файл", "Fayl")
a("export.size", "Размер", "Hajmi")
a("export.contents", "Состав", "Tarkibi")
a("export.counts", "изделий: {{products}}, строк деталей: {{parts}}", "mahsulotlar: {{products}}, detal qatorlari: {{parts}}")
a("export.warnings", "Не вошло в файл или записано иначе: {{n}}", "Faylga kirmadi yoki boshqacha yozildi: {{n}}")
a("export.notes", "Примечания", "Izohlar")
a("export.no_warnings", "Всё записано без потерь.", "Hammasi yo'qotishsiz yozildi.")
a("export.download", "Скачать .project", ".project ni yuklab olish")
a("export.back", "Назад", "Orqaga")
a("export.done", "Файл .project скачан", ".project fayli yuklab olindi")
a("export.selected", "Экспорт .project", ".project eksporti")

# ── CS: «Максимальное количество вращений» 1…6 ──
a("phelp.max_rot",
  "Максимальное число уровней резов (вращений листа на станке): от 1 до 6. 1 — только первый рез: каждая полоса — одна деталь без "
  "внутренних резов (размер детали должен точно совпасть с размером полосы, иначе она не поместится); 2 — полоса и деталь внутри неё; "
  "3 и больше — вложенные резы. Чем больше, тем лучше раскрой, но не все станки допускают больше 4.",
  "Kesim darajalari (stanokda list aylantirishlar) maksimal soni: 1 dan 6 gacha. 1 — faqat birinchi kesim: har polosa bitta detal, "
  "ichki kesimlarsiz (detal o'lchami polosa o'lchamiga aynan mos kelishi shart, aks holda joylashmaydi); 2 — polosa va uning ichidagi detal; "
  "3 va undan ko'p — ichma-ich kesimlar. Ko'p bo'lsa kroy yaxshiroq, lekin hamma stanok 4 dan ko'pini ruxsat etmaydi.")

# ── Настройки → Общие: «Минимальный размер детали» ──
a("settings.min_part", "Минимальный размер детали", "Detalning minimal o'lchami")
a("settings.min_part_hint",
  "Деталь, у которой меньшая сторона (пильный размер) меньше этого значения, в раскрой не попадает — будет предупреждение. "
  "Значение у каждого цеха своё (зависит от станка).",
  "Kichik tomoni (arra o'lchami) bu qiymatdan kichik detal kroyga kirmaydi — ogohlantirish chiqadi. "
  "Har sexda o'zining qiymati bor (stanokka bog'liq).")
a("settings.min_part_note",
  "Значение подставляется в новые операции раскроя (общий стандарт). В уже созданной операции его можно изменить в «Параметры → Ограничения».",
  "Qiymat yangi kroy operatsiyalariga qo'yiladi (umumiy standart). Tayyor operatsiyada uni «Параметры → Ограничения» da o'zgartirish mumkin.")
