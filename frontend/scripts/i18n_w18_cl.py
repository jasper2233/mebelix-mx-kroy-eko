# -*- coding: utf-8 -*-
"""W18 · (CL) W11 bo'shliqlari — interfeys matnlari: detal «Свойства», «Варианты», «До кроить», «Групповые действия» (SP / ko'chirish),
etiketka manbai. i18n_src.py shu faylni o'zi yuklaydi (`a` — o'sha yerdan)."""

# ── CL detal «Свойства» (Ctrl+Space) ──
a("cl.pp.num_in_strips", "№ в раскрое (полосы)", "Kroyda (polosalar) №")
a("cl.pp.sketch_hint", "Ширина детали = ширина полосы ({{w}} мм); ОВ / ОН — продольные кромки, ОЛ / ОП — торцы",
  "Detal eni = polosa eni ({{w}} mm); ОВ / ОН — bo'ylama kromkalar, ОЛ / ОП — uchlar")
a("cl.pp.strip_width", "Ширина полосы", "Polosa eni")
a("cl.pp.delta_hint", "◁ ▷ — изменение длины от торцевых кромок: после прифуговки — минус толщина кромки, заготовка — плюс ширина прифуговки; "
  "в строке «пильный» вводится припуск по торцам.",
  "◁ ▷ — uch kromkalaridan uzunlik o'zgarishi: prifugovkadan keyin — kromka qalinligi ayriladi, zagotovka — prifugovka eni qo'shiladi; "
  "«arra o'lchami» qatorida uchlar bo'yicha pripusk kiritiladi.")

# ── «Групповые действия»: SP va перенос ──
a("ga.move_h", "Перенос в другую операцию", "Boshqa operatsiyaga ko'chirish")

# ── CL «Варианты» ──
a("cl.variants.busy", "Расчёт вариантов раскроя…", "Kroy variantlari hisoblanmoqda…")
a("cl.variants.hint", "Варианты строятся по разным целям; результат можно применить как есть — он проходит ту же проверку, что и ручное редактирование. "
  "Одинаковые результаты помечены.",
  "Variantlar turli maqsadlar bo'yicha quriladi; natijani to'g'ridan-to'g'ri qo'llash mumkin — u qo'lda tahrirlash bilan bir xil tekshiruvdan o'tadi. "
  "Bir xil natijalar belgilanadi.")
a("cl.variants.material", "Минимум материала", "Eng kam material")
a("cl.variants.consumption", "Минимум расхода", "Eng kam sarf")
a("cl.variants.cuts", "Минимум резов", "Eng kam kesim")
a("cl.variants.max", "Максимальное качество", "Maksimal sifat")
a("cl.variants.material_hint", "Меньше суммарная длина полос → больше делового остатка → меньше разных карт → меньше резов",
  "Polosalar umumiy uzunligi kam → deloviy qoldiq ko'p → xil kartalar kam → kesimlar kam")
a("cl.variants.consumption_hint", "Расход = материал − деловые остатки (они уходят на склад), затем меньше полос",
  "Sarf = material − deloviy qoldiqlar (omborga ketadi), so'ng polosalar kam")
a("cl.variants.cuts_hint", "Меньше резов (длина реза LT), затем меньше материала", "Kesimlar kam (kesim uzunligi LT), so'ng material kam")
a("cl.variants.max_hint", "Цель «минимум материала», но режим качества «Максимальное» (дольше)",
  "Maqsad «eng kam material», lekin sifat rejimi «Maksimal» (uzoqroq)")
a("cl.variants.same_as", "= как «{{name}}»", "= «{{name}}» bilan bir xil")
a("cl.variants.strips", "Полос", "Polosalar")
a("cl.variants.maps", "карт: {{n}}", "kartalar: {{n}}")
a("cl.variants.row_material", "Материал", "Material")
a("cl.variants.row_consumption", "Расход (без дел. остатка)", "Sarf (deloviy qoldiqsiz)")

# ── etiketka manbai: CS yoki CL ──
a("lb.cs_op", "Материал (операция CS / CL)", "Material (CS / CL operatsiyasi)")
