# -*- coding: utf-8 -*-
"""2026-10-18 · joylashuv mosligi auditi (loyihalar ro'yxati, loyiha sarlavhasi, chap «Проект» menyusi, pastki akkordeon,
«Операции» asboblari va menyusi, «Объединить» / «Выбрать элементы для печати» oynalari, «Товары», ixcham «Импорт из других программ»).
i18n_src.py yuklaydi (alifbo tartibida — oldingi qiymatlarni almashtiradi)."""

# ── loyihalar ro'yxati ──
a("menu.select_all", "Выделить все…", "Hammasini tanlash…")
a("ctx.select_all", "Выделить все…", "Hammasini belgilash…")
a("projects.up", "Перейти в верхнюю папку", "Yuqori papkaga o'tish")
a("projects.home", "Домой", "Bosh papka")

# ── pastki akkordeon ──
a("menu.logout", "Выйти", "Chiqish")
a("menu.logout_done", "Сеанс завершён", "Seans tugadi")
a("menu.logout_local", "Вход в систему не требуется: программа работает без учётной записи", "Tizimga kirish talab qilinmaydi: dastur hisob yozuvisiz ishlaydi")

# ── loyiha sarlavhasi va chap «Проект» menyusi ──
a("header.save_currency", "Сохранить текущие параметры для использования по умолчанию",
  "Joriy parametrlarni standart sifatida saqlash")
a("menu.export_more", "Экспорт: другие форматы…", "Eksport: boshqa formatlar…")

# ── «Импорт из других программ» (ixcham oyna) ──
for k, ru, uz in [("pro100", "Импорт PRO100", "PRO100 import"), ("imos", "Imos (fxm)", "Imos (fxm)"),
                  ("bazis", "Импорт БМ(xml,obl)", "BM import (xml,obl)"), ("bcad", "Импорт BCAD(xml)", "BCAD import (xml)"),
                  ("woody2", "Woody2 (xml,wes)", "Woody2 (xml,wes)"), ("woodwop", "WoodWop (mpr)", "WoodWop (mpr)"),
                  ("ilenia", "iLENIA (pd4)", "iLENIA (pd4)"), ("project", "Файл проекта (XML)", "Loyiha fayli (XML)")]:
    a(f"importx.q.{k}", ru, uz)
a("importx.q_more", "Параметры и профили импорта…", "Import parametrlari va profillari…")

# ── «Товары» (Каталог товаров) ──
a("catalog.goods", "Товары", "Tovarlar")
a("catalog.materials", "Материалы", "Materiallar")
a("catalog.unit", "Ед.И", "Birlik")

# ── «Операции»: menyu, «Объединить», «Выбрать элементы для печати» ──
a("ops.settings", "Настройки", "Sozlamalar")
a("ops.copy", "Копировать", "Nusxa olish")
a("ops.copied", "Строка операции скопирована в буфер обмена", "Operatsiya qatori buferga nusxalandi")
a("ops.copy_failed", "Не удалось скопировать в буфер обмена", "Buferga nusxalab bo'lmadi")
a("ops.convert_cn", "Конвертировать в «Нестинговый раскрой»", "«Nesting kroy» ga aylantirish")
a("ops.convert_q", "Конвертировать «{{name}}» в «Нестинговый раскрой»?", "«{{name}}» «Nesting kroy» ga aylantirilsinmi?")
a("ops.convert_text", "Результат раскроя будет удалён (Ctrl+Z вернёт).", "Kroy natijasi o'chiriladi (Ctrl+Z qaytaradi).")
a("ops.convert_ok", "Конвертировать", "Aylantirish")
a("ops.print_select", "Выбрать элементы для печати", "Chop etish uchun elementlarni tanlash")
a("ops.print_select_head", "Операции для печати", "Chop etiladigan operatsiyalar")
a("ops.col.sel", "Выб", "Tanl.")
a("ops.pick_all", "Выбрать все", "Hammasini tanlash")
a("ops.pick_none", "Снять выделение со всех", "Hammasidan belgini olish")
a("ops.merge_off", "Объединение доступно для операций CS, CL, CN и EL", "Birlashtirish CS, CL, CN va EL operatsiyalari uchun")
a("ops.merge_none", "Других операций этого типа нет", "Bu turdagi boshqa operatsiyalar yo'q")
a("ops.merged", "Объединено операций: {{n}}", "Birlashtirilgan operatsiyalar: {{n}}")
