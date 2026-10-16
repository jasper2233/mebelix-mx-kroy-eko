# -*- coding: utf-8 -*-
# uz tarjimasini tozalash (2026-10-16, QA #9): o'zbek UI da qolgan ruscha matnlar. Fayl nomi `zz_uz` — eng oxirida yuklanadi,
# shuning uchun avvalgi skriptlardagi qiymatlarni almashtiradi. ru qiymatlari o'zgarmaydi (`T[key][0]` dan olinadi).
# Xodimlarning o'z atamalari (Сони, Ишлатилди, Колдик, ОВ/ОН/ОЛ/ОП, Ткт, Д-на/Ш-на, Д№) ikkala tilda ham saqlanadi — bu yerda tegilmaydi.
# Tekshiruv: `python scripts/i18n_check_uz.py` → 0 topilma.

def uz(key, text):
    """Faqat o'zbekchasini almashtirish (ru — avvalgi skriptdagidek)."""
    a(key, T[key][0], text)

def uz_fix(key, *pairs):
    """Uzun matnda ruscha parchalarni almashtirish (old, new, old, new, …); ru o'zgarmaydi."""
    s = T[key][1]
    for old, new in zip(pairs[::2], pairs[1::2]):
        if old not in s:
            raise SystemExit(f"i18n_zz_uz_1016: «{old}» {key} matnida topilmadi")
        s = s.replace(old, new)
    a(key, T[key][0], s)

# ── hisobot: (XNC) Обработка → Статистика ustunlarining qisqa nomlari ──
for _k, _n in [("side", "Tomon"), ("code", "Kod"), ("name", "Nomi"), ("qty", "Soni"),
               ("drills", "Tesh. soni"), ("drill_price", "Tesh. narxi"), ("drill_cost", "Tesh. qiym."),
               ("mill_len", "Frez. uz."), ("mill_price", "Frez. narxi"), ("mill_cost", "Frez. qiym."),
               ("saw_len", "Arra uz."), ("saw_price", "Arra narxi"), ("saw_cost", "Arra qiym."),
               ("extra_cost", "Qo'sh. qiym."), ("op_cost", "Op. qiym.")]:
    uz(f"print.xc.{_k}.n", _n)

# ── qisqa matnlar (to'liq o'zbekcha) ──
uz("project.no_op", "«Operatsiyalar» panelida operatsiya qo'shing (CS — listli kroy)")
uz("settings.min_part_note", "Qiymat yangi kroy operatsiyalariga qo'yiladi (umumiy standart). Tayyor operatsiyada uni «Parametrlar → Cheklovlar» da o'zgartirish mumkin.")
uz("sheets.col.cl_trim_hint", "Polosa torsovkasi — operatsiya parametridan («Torsovka»)")
uz("import.excel_hint", "Excel (.xlsx, .xls) yoki CSV faylni tanlang, so'ng ustunlarni belgilang: «Detallar» tabi — detallar, mahsulot va material bo'yicha guruhlash; «Mahsulotlar» tabi — mahsulotlar ro'yxati.")
uz("import.required_hint", "* — majburiy. «Uzunlik», «En» yoki «Soni» bo'sh yoki son bo'lmasa — qator o'tkazib yuboriladi va hisobotda ko'rsatiladi.")
uz("xi18.linear_hint", "«En» bo'sh bo'lsa, qator — pogonaj detal va CL operatsiyasiga tushadi («Material» ustuni bo'yicha)")
uz("xi18.simple_cols_hint", "Kod yoki nom shart. Soni — standart 1, Narx — 0; «Mahsulot» — operatsiya egasi.")
uz("xi18.simple_hint", "«Operatsiya» ustuni bo'lsa — har qiymat uchun alohida operatsiya yaratiladi; bo'lmasa bitta (yuqoridagi nom).")
uz("cs.p.stock_order_hint", "Ro'yxat bo'yicha — listlar «Listlar va qoldiqlar» ro'yxati tartibida qat'iy ishlatiladi (ombordagi qoldiqlar va soni cheklangan listlar — detal sig'sa, avval). Material tejash — dastur bir nechta tartibni sinab, material maydoni eng kam variantni oladi.")

# ── uzun matnlar: faqat ruscha parchalar almashtiriladi ──
uz_fix("phelp.stock_order", "«Листы и остатки»", "«Listlar va qoldiqlar»")
uz_fix("phelp.group_props", "«Объединение деталей»", "«Detallarni birlashtirish»")
uz_fix("phelp.merge", "«Группировка деталей по свойствам»", "«Detallarni xossalar bo'yicha guruhlash»")
uz_fix("help.text.cut", "«Группировка в блок»", "«Blokka guruhlash»")
uz_fix("pp_ed.context_doc", "«Данные для этикеток»", "«Etiketkalar uchun ma'lumotlar»")
uz_fix("ppm.ctx_doc", "«Данные для этикеток»", "«Etiketkalar uchun ma'lumotlar»")
uz_fix("whatsnew.v23.i01.d", "«Открыть»", "«Ochish»")
uz_fix("whatsnew.v23.i12.d", "«Простые операции»", "«Oddiy operatsiyalar»", "«Материалы»", "«Materiallar»")
