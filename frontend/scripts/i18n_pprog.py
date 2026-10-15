# -*- coding: utf-8 -*-
"""Mahsulot «Программа» (parametrik mahsulot) va «Пересчитать параметричность» — interfeys matnlari (W12).
i18n_src.py shu faylni o'zi yuklaydi (`a` — o'sha yerdan)."""

a("pprog.tab", "Программа", "Dastur")
a("pprog.program", "Программа изделия", "Mahsulot dasturi")
a("pprog.empty", "Программа пуста — добавьте команды слева (Par — параметр, Var — переменная, If — ограничение …)",
  "Dastur bo'sh — chapdan buyruq qo'shing (Par — parametr, Var — o'zgaruvchi, If — cheklov …)")
a("pprog.params", "Параметры", "Parametrlar")
a("pprog.par_hint", "Значения хранятся в изделии; программа не меняется", "Qiymatlar mahsulotda saqlanadi; dastur o'zgarmaydi")
a("pprog.vars", "Переменные изделия", "Mahsulot o'zgaruvchilari")
a("pprog.vars_none", "Переменных нет — добавьте Par или Var", "O'zgaruvchilar yo'q — Par yoki Var qo'shing")
a("pprog.vars_hint", "В выражениях XNC и этикеток доступны как product.<имя>", "XNC va etiketka ifodalarida product.<nom> sifatida ko'rinadi")
a("pprog.path", "Номер команды", "Buyruq raqami")
a("header.prog_warn", "Программа изделия: нарушений (Err) — {{e}}, предупреждений — {{w}}",
  "Mahsulot dasturi: cheklov buzilishi (Err) — {{e}}, ogohlantirishlar — {{w}}")

# ── «Общие действия» ──
a("common.recalc_parametric", "Пересчитать параметричность", "Parametrikni qayta hisoblash")
a("common.recalc_parametric_hint",
  "Заново вычисляются программы изделий и выражения XNC; переменные изделия (product.<имя>) обновляются в операциях XNC",
  "Mahsulot dasturlari va XNC ifodalari qayta hisoblanadi; mahsulot o'zgaruvchilari (product.<nom>) XNC operatsiyalarida yangilanadi")
a("common.recalc_parametric_done", "Пересчитано: программ изделий — {{p}}, операций XNC — {{x}}; замечаний — {{n}}",
  "Qayta hisoblandi: mahsulot dasturlari — {{p}}, XNC operatsiyalari — {{x}}; izohlar — {{n}}")
