# -*- coding: utf-8 -*-
"""2026-10-16 — QA tuzatishlari (kroy / EL / postprotsessor): EL o'lchami o'zgarganda kroy natijasi uchun tasdiq (#1),
stanok formati burilishlarni cheklasa qayta kroy tasdig'i (#3), «Раскроить все операции» band holati va «пропущено» (#6).
`a(kalit, ru, uz)` — i18n_src.py ichida (exec) chaqiriladi."""

# ── (EL) «Толщина» / «Ширина прифуговки»: shu kromkali detallarning kroy natijalari o'chadi — oldindan tasdiq ──
a("el.size_invalidate_text",
  "Изменение параметра «{{field}}» меняет размеры заготовок — результат раскроя будет удалён: {{ops}}. Продолжить? (Ctrl+Z вернёт)",
  "«{{field}}» parametri o'zgarsa zagotovka o'lchamlari o'zgaradi — kroy natijasi o'chiriladi: {{ops}}. Davom etilsinmi? (Ctrl+Z qaytaradi)")
a("el.size_invalidate_rem",
  "Изменение параметра «{{field}}» меняет размеры заготовок — раскрой будет удалён, а записанные на склад остатки возвращены (списаны со склада): {{ops}}. Продолжить? (Ctrl+Z вернёт раскрой)",
  "«{{field}}» parametri o'zgarsa zagotovka o'lchamlari o'zgaradi — kroy o'chiriladi, omborga yozilgan qoldiqlar esa qaytariladi (ombordan chiqariladi): {{ops}}. Davom etilsinmi? (Ctrl+Z kroyni qaytaradi)")
a("el.inv_manual", "изменён вручную", "qo'lda o'zgartirilgan")
a("el.inv_remnants", "остатки на складе", "qoldiqlar omborda")

# ── Postprotsessor: stanok formati burilishlarni cheklaydi — almashtirish / nusxadan eksport / bekor ──
a("pp.checking", "Проверка формата станка…", "Stanok formati tekshirilmoqda…")
a("pp.refit_q", "Раскрой не соответствует формату станка", "Kroy stanok formatiga mos emas")
a("pp.refit_text",
  "Формат станка «{{m}}» допускает не более {{n}} вращений, текущий раскрой выполнен с {{cur}}. Заменить раскрой в проекте новым (с ограничением {{n}}) или выгрузить файл из временной копии, не меняя раскрой?",
  "«{{m}}» stanok formati ko'pi bilan {{n}} burilishga ruxsat beradi, joriy kroy esa {{cur}} bilan bajarilgan. Loyihadagi kroy yangisi ({{n}} chegarasi bilan) bilan almashtirilsinmi yoki fayl kroyni o'zgartirmasdan vaqtinchalik nusxadan chiqarilsinmi?")
a("pp.refit_manual", "Текущий раскрой изменён вручную — при замене правки и комментарии карт будут потеряны (Ctrl+Z вернёт).",
  "Joriy kroy qo'lda o'zgartirilgan — almashtirilsa tahrirlar va karta izohlari yo'qoladi (Ctrl+Z qaytaradi).")
a("pp.refit_remnants", "Остатки текущего раскроя записаны на склад — заменить его нельзя, доступен только экспорт копии.",
  "Joriy kroy qoldiqlari omborga yozilgan — uni almashtirib bo'lmaydi, faqat nusxadan eksport mumkin.")
a("pp.refit_replace", "Заменить раскрой", "Kroyni almashtirish")
a("pp.refit_copy", "Экспорт копии", "Nusxadan eksport")
a("pp.refit_copied", "Файл сформирован из временного раскроя (не более {{n}} вращений); раскрой в проекте не изменён",
  "Fayl vaqtinchalik kroydan chiqarildi (ko'pi bilan {{n}} burilish); loyihadagi kroy o'zgarmadi")

# ── «Раскроить все операции»: band holati va natija (bo'sh operatsiyalar — «пропущено», xato emas) ──
a("common.cut_all_busy", "Раскрой всех операций…", "Barcha operatsiyalar kroy qilinmoqda…")
a("common.cut_all_done", "Раскроено операций: {{n}}, пропущено: {{s}}, с ошибкой: {{e}}",
  "Kroy qilingan operatsiyalar: {{n}}, o'tkazib yuborilgan: {{s}}, xato bilan: {{e}}")
