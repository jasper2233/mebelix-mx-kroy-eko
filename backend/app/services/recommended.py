"""«По умолчанию» (2026-10-26, foydalanuvchi qoidasi): MebeliX Kroy ning o'z tavsiya qilingan parametrlari — kroy sifati va aniqligi,
listga zich joylash, arra (pilniy markaz) uchun qulay va oson kesish. Foydalanuvchi sozlamani o'zgartirsa — uning tanlovi (eslab
qolinadi); «По умолчанию» tugmasi operatsiyani shu qiymatlarga qaytaradi (va ular keyingi loyihalar uchun ham standart bo'ladi).

Qiymatlar korxonaning onlayn tizimdagi import standartlari bilan bir xil (2026-10-26 jonli tekshirildi: «test uchun»), MX qoidalari
bilan: «Максимальное количество вращений» 4 (arra uchun qulay, zichlik deyarli bir xil), eng kam material birinchi.
Materialga / pulga / stanokka xos qiymatlar (qalinlik, list narxi, ish narxi, eni, belgi, rang, «Учет текстуры», EL prifugovkasi) o'zgartirilmaydi."""
from __future__ import annotations

from ..models import CSCutParams, CSMaterialParams, FirstCutDir, OpCostBase, SheetRounding, StripSort

CS_CUT = dict(kerf=3.0, kerf_group=None, trim_length=2.0, trim_width=2.0, end_offset_bottom=None, end_offset_right=None,
              trim_includes_kerf=False, first_cut=FirstCutDir.ANY, complex_strips=True, max_rotations=4, pack_height=40.0,
              fill_packet=90.0, quality="normal", max_part_types_per_map=0, prefer_big_pack=True, stock_order="list",
              strip_sort=StripSort.DESC, in_strip_sort=StripSort.NONE, min_strip_width=0.0, max_strip_width=0.0,
              max_strip_length=10000.0, min_trim_cut=5.0, merge_parts=False, save_drawings=False, machining_allowance=0.0)
CS_MATERIAL = dict(est_fill_percent=90.0, cost_by_sheets=True, sheet_rounding=SheetRounding.WHOLE, op_cost_base=OpCostBase.CUT_LENGTH,
                   remnant_min_side1=1000.0, remnant_min_side2=500.0, remnant_min_area=0.5, remnant_size_incl_trim=True,
                   min_part_size=30.0)
EL = dict(count_material=True, waste_percent=0.0, overhang=30.0, min_glue_length=100.0, marker_lines=1,
          min_perp_side=40.0, material_round=10, work_round=10)


def payload() -> dict:
    """JSON: {cs_cut, cs_material, el} — faqat tavsiya qilinadigan maydonlar (qolganlari tegilmaydi)."""
    cut = CSCutParams.model_validate(CS_CUT).model_dump(mode="json", include=set(CS_CUT))
    mat = CSMaterialParams.model_validate(CS_MATERIAL).model_dump(mode="json", include=set(CS_MATERIAL))
    from ..models import ELParams
    el = ELParams.model_validate(EL).model_dump(mode="json", include=set(EL))
    return dict(cs_cut=cut, cs_material=mat, el=el)
