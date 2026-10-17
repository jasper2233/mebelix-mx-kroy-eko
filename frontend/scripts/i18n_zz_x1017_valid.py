# -*- coding: utf-8 -*-
"""2026-10-17 · xabarlar auditi (frontend): son maydonlari chegarasi (jim qisqartirish o'rniga sabab), detal o'lchami,
XNC ifoda xatosi, kroyni o'chirish tasdig'i, qoldiqlar taklifi, xato sarlavhasi (i18n_src.py yuklaydi; «zz» — oldingi kalitlardan keyin)."""

# ── son maydoni (shared/ui.tsx Num): «<Yorliq>: <sabab>» ──
a("num.range", "допустимо {{min}} – {{max}}{{u}}", "ruxsat etilgan: {{min}} – {{max}}{{u}}")
a("num.min", "допустимо не меньше {{min}}{{u}}", "kamida {{min}}{{u}} bo'lishi kerak")
a("num.max", "допустимо не больше {{max}}{{u}}", "ko'pi bilan {{max}}{{u}} bo'lishi kerak")
a("num.nan", "введите число", "son kiriting")
a("num.empty", "значение не может быть пустым", "qiymat bo'sh bo'lishi mumkin emas")
a("num.thick_pack", "толщина материала не может быть больше высоты пакета ({{h}} мм)",
  "material qalinligi paket balandligidan ({{h}} mm) katta bo'lishi mumkin emas")
a("num.pack_thick", "высота пакета не может быть меньше толщины материала ({{th}} мм)",
  "paket balandligi material qalinligidan ({{th}} mm) kichik bo'lishi mumkin emas")

# ── detal o'lchami (Детали jadvali, xossalar oynasi) ──
a("parts.size_pos", "размер детали должен быть больше 0", "detal o'lchami 0 dan katta bo'lishi kerak")
a("parts.size_zero", "{{what}}: размер детали должен быть больше 0 — деталь не попадёт в раскрой",
  "{{what}}: detal o'lchami 0 dan katta bo'lishi kerak — detal kroyga kirmaydi")
a("parts.size_small", "{{what}} {{v}} мм меньше ограничения «Минимальный размер детали» = {{mm}} мм",
  "{{what}} {{v}} mm «Detalning minimal o'lchami» = {{mm}} mm cheklovidan kichik")
a("parts.qty_zero", "Количество 0 — деталь не попадёт в раскрой", "Soni 0 — detal kroyga kirmaydi")
a("parts.left_tip", "Не вошло в раскрой: {{n}} шт", "Kroyga kirmadi: {{n}} dona")

# ── XNC ──
a("xnc.expr_err", "Ошибка", "Xato")
a("xnc.pl.text", "Сообщение", "Xabar")
a("xnc.p.text", "Текст сообщения (строка в кавычках или выражение)", "Xabar matni (qo'shtirnoqdagi satr yoki ifoda)")
a("xnc.state_n", "Ошибок / предупреждений: {{n}}", "Xato / ogohlantirishlar: {{n}}")

# ── kroy: o'chirish tasdig'i, qoldiqlar taklifi ──
a("cut.delete_text", "Карты раскроя этой операции будут удалены; детали и листы останутся. Отменить можно через «Отменить» (Ctrl+Z).",
  "Bu operatsiyaning kroy kartalari o'chiriladi; detallar va listlar qoladi. «Bekor qilish» (Ctrl+Z) bilan qaytarish mumkin.")
a("rem.offer", "Деловые остатки: {{n}} — не записаны на склад", "Deloviy qoldiqlar: {{n}} — omborga yozilmagan")
a("rem.offer_btn", "Записать на склад…", "Omborga yozish…")
a("settings.remnant_confirm", "После раскроя предлагать записать деловые остатки на склад (уведомление с кнопкой)",
  "Kroydan keyin deloviy qoldiqlarni omborga yozishni taklif qilish (tugmali xabar)")

# ── xato xabari sarlavhasi ──
a("app.error_title", "Ошибка", "Xato")
