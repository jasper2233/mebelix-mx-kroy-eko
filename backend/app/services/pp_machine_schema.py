"""Postprotsessor stanoklarining sozlamalar sxemasi (W7): har stanok uchun guruhlangan parametrlar va «etiketka maydonlari»
(«Данные для этикеток»: nom → ifoda) jadvalining standart qatorlari.

Bu modul faqat **ma'lumot va tekshiruv** (DB yo'q): sxema (kalit, tur, standart, ru/uz yorliq), qiymatlarni tekshirish
(`validate_params`) va etiketka maydonlarini tekshirish (`validate_label_fields`; ifoda sintaksisi — `expr.compile_check`).
Saqlash va postprotsessor konteksti — `pp_machine_ctx.py`.

Turlar: bool | int | mm | float | string | path | choice.
  mm/float — chekli son; int — butun; path — **faqat satr** (server fayl tizimiga hech narsa yozmaydi/o'qimaydi);
  choice — variantlardan biri (`custom=True` bo'lsa — ro'yxat to'liq emas, boshqa matn ham mumkin).
Stanok formatining o'zi (fayl mazmuni) bu yerda yo'q — uni korxona dasturchilari shablonda yozadi; shablon `machine.params` va
`maps[].placements[].label` dan foydalanadi.

Parametr nomlari (kalitlar) — bizniki; rus yorliqlari xodimlar odatlangan nomlar, o'zbekchasi to'liq tarjima.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any

from ..i18n import _
from . import expr

# ───────────────────────── Chegaralar ─────────────────────────
MAX_STR = 300                 # matn / yo'l parametri, belgi
MAX_PATH = 260
MAX_CHOICE = 100              # `custom` variant uzunligi
MAX_LABEL_ROWS = 100          # etiketka maydonlari jadvali qatorlari
MAX_LABEL_NAME = 80
MAX_NUM = 1_000_000.0         # mm/float uchun standart chegara (moduli)
_CTRL = re.compile(r"[\x00-\x1f\x7f]")
_PATH_BAD = re.compile(r'[<>"|?*\x00-\x1f\x7f]')

TYPES = ("bool", "int", "mm", "float", "string", "path", "choice", "template")
# `template` (W18): etiketka shabloni havolasi — "" (stanokning standarti) | `builtin:<kalit>` | `profile:<id>` (W4 kutubxonasi,
# `GET /label-templates`). Faqat havola: server shablonni o'qimaydi/yozmaydi; ko'rinish va tanlov — frontend (LabelTemplateField).
_TPL_REF = re.compile(r"(builtin:[A-Za-z0-9_.-]{1,60}|profile:\d{1,9})")

# parametr guruhlari: kalit → (ru, uz); chiqish tartibi — stanok parametrlari bo'yicha
GROUPS: dict[str, tuple[str, str]] = {
    "general": ("Общие", "Umumiy"),
    "labels": ("Печать этикеток", "Etiketkalarni chop etish"),
    "label_files": ("Этикетки", "Etiketkalar"),
    "special": ("Специализированные", "Stanokka xos"),
    "trim": ("Торцовка", "Torsovka"),
    "limits": ("Ограничения", "Cheklovlar"),
}


@dataclass(frozen=True)
class Opt:
    value: str
    ru: str
    uz: str


@dataclass(frozen=True)
class Param:
    key: str
    group: str
    type: str
    default: Any
    ru: str
    uz: str
    min: float | None = None
    max: float | None = None
    options: tuple[Opt, ...] = ()
    custom: bool = False                  # choice: ro'yxat to'liq emas — boshqa matn ham mumkin
    enabled_if: str | None = None         # shu bool parametr yoqilgandagina faol (UI da xira)
    note_ru: str = ""
    note_uz: str = ""


@dataclass(frozen=True)
class LabelTable:
    title_ru: str
    title_uz: str
    rows: tuple[tuple[str, str], ...]     # standart qatorlar: (nom, ifoda)
    kind: str = "labels"                  # labels | udi (PARTS_UDI — foydalanuvchi yozuvlari)


@dataclass(frozen=True)
class MachineSchema:
    key: str
    params: tuple[Param, ...] = ()
    label_table: LabelTable | None = None
    info_ru: str = ""
    info_uz: str = ""


# ───────────────────────── Qisqa konstruktorlar ─────────────────────────
def _B(key, group, default, ru, uz, **kw):
    return Param(key, group, "bool", bool(default), ru, uz, **kw)


def _I(key, group, default, ru, uz, lo=0, hi=1_000_000, **kw):
    return Param(key, group, "int", int(default), ru, uz, min=lo, max=hi, **kw)


def _MM(key, group, default, ru, uz, lo=0.0, hi=100_000.0, **kw):
    return Param(key, group, "mm", float(default), ru, uz, min=lo, max=hi, **kw)


def _F(key, group, default, ru, uz, lo=0.0, hi=1000.0, **kw):
    return Param(key, group, "float", float(default), ru, uz, min=lo, max=hi, **kw)


def _S(key, group, default, ru, uz, **kw):
    return Param(key, group, "string", default, ru, uz, **kw)


def _P(key, group, default, ru, uz, **kw):
    return Param(key, group, "path", default, ru, uz, **kw)


def _C(key, group, default, ru, uz, options, custom=False, **kw):
    return Param(key, group, "choice", default, ru, uz, options=tuple(Opt(*o) for o in options), custom=custom, **kw)


def _T(key, group, ru, uz, **kw):
    """Etiketka shabloni havolasi (`template` turi): standart "" — stanokning o'z standart shabloni."""
    return Param(key, group, "template", "", ru, uz, **kw)


# ───────────────────────── Umumiy variantlar ─────────────────────────
_LABEL_MODE = (("normal", "Обычный (x,x,x,x)(x,x,x,x)", "Oddiy (x,x,x,x)(x,x,x,x)"),)
_ORIENT_HV = (("horizontal", "Горизонтально", "Gorizontal"), ("vertical", "Вертикально", "Vertikal"))


def _pre_cuts() -> tuple[Param, ...]:
    return (
        _MM("pre_cut_head", "trim", 0, "Размер предварительного реза при головном резе", "Bosh kesimda oldindan kesim o'lchami"),
        _MM("pre_cut_front", "trim", 0, "Размер предварительного реза спереди для докроя",
            "Dokroy uchun oldindan kesim o'lchami (old tomondan)"),
        _MM("pre_cut_rear", "trim", 0, "Размер предварительного реза сзади для докроя",
            "Dokroy uchun oldindan kesim o'lchami (orqa tomondan)"),
    )


def _label_dx_dy(group: str, dy: float) -> tuple[Param, ...]:
    return (_MM("label_dx", group, 58, "Длина DX", "DX uzunligi", lo=1, hi=1000),
            _MM("label_dy", group, dy, "Ширина DY", "DY eni", lo=1, hi=1000))


# ───────────────────────── Etiketka maydonlari: standart jadvallar ─────────────────────────
def _edge_name(s: str, n: str) -> str:
    return f"if(empty({s}),'','('+{s}+') '+{n})"


_EDGE_TOP, _EDGE_BOTTOM = _edge_name("ets", "etn"), _edge_name("ebs", "ebn")
_EDGE_LEFT, _EDGE_RIGHT = _edge_name("els", "eln"), _edge_name("ers", "ern")
_SPACE_SYM = tuple(f"if(empty({s}),' ',{s})" for s in ("ets", "ebs", "els", "ers"))

_WINCUT_ROWS = tuple((f"Campo{n}", "") for n in range(10, 15))

_MAESTRO_ROWS = (
    ("Codice", "project.name"), ("Lunghezza", "format('0.00',length)"), ("Larghezza", "format('0.00',width)"),
    ("Richiesti", "if(waste,count,usedCount)"),
    ("CodiceBordo1", _SPACE_SYM[0]), ("CodiceBordo2", _SPACE_SYM[1]), ("CodiceBordo3", _SPACE_SYM[2]),
    ("CodiceBordo4", _SPACE_SYM[3]), ("Job", "project.name"),
)

_CADMATIC4_ROWS = (
    ("PartFinishedLength", "detail.length"), ("PartFinishedWidth", "detail.width"), ("PartInformation", "description"),
    ("Edge.MaterialBack", _EDGE_TOP), ("Edge.MaterialFront", _EDGE_BOTTOM),
    ("Edge.MaterialLeft", _EDGE_LEFT), ("Edge.MaterialRight", _EDGE_RIGHT),
)

_OSI_ROWS = (
    ("Код", "'P' + part.id"), ("Коорд min", "usedCount"), ("Коорд max", "0"), ("Приоритет", "100"),
    ("Длина", "length"), ("Ширина", "width"), ("Текстура", "if(txt,1,0)"),
    ("Окончательная обработка / Finish", "'S'"), ("Данные отхода", "now('yyyy-MM-dd')"),
    ("Код подформата / PartNo", "indexInOperation"), ("Comment", "description"), ("Job", ""), ("Name", ""),
    ("Описание I", "name"), ("Описание II", "project.name"),
)

# FELDER Format4 PC6: Part.text0 — kromka qalinligi belgisi (1 yoki 2) har tomon uchun
_PC6_TEXT0 = "+".join(f"if(empty({s}),' ',if({t}>1,2,1)+' ')" for s, t in
                      (("ets", "ett"), ("ebs", "ebt"), ("els", "elt"), ("ers", "ert")))
_PC6_ROWS = (
    ("Part description (16)", "name"), ("Headdata.text(30)", "project.name"),
    ("Material.headline1(30)", "material.name"), ("Material.headline2(30)", "material.code"),
    ("Material.headline3(30)", "'#N('+now('yyMMddHHmmss')+rspace(crc16(project.name+material.name),5,'0')+')'"),
    ("Part.text0(12)", _PC6_TEXT0),
    ("Part.text1(30)", _EDGE_TOP), ("Part.text2(30)", _EDGE_BOTTOM), ("Part.text3(30)", _EDGE_LEFT),
    ("Part.text4(30)", _EDGE_RIGHT), ("Part.text5(30)", "description"),
    ("Part.text6(30)", "grtn"), ("Part.text7(30)", "grbn"), ("Part.text8(30)", "grln"), ("Part.text9(30)", "grrn"),
    ("Part.text10(30)", "XNC1"), ("Part.text11(30)", "'#P('+part.id+')'"),
)

_PC7_ROWS = (
    ("Part description", "name"), ("Headdata.text", "project.name"),
    ("Edge top", _EDGE_TOP), ("Edge bottom", _EDGE_BOTTOM), ("Edge left", _EDGE_LEFT), ("Edge right", _EDGE_RIGHT),
    ("Part.text1", "indexInOperation"), ("Part.text2", "material.name"), ("Part.text3", "material.code"),
    ("Part.text4", "product.name"), ("Part.text5", "description"), ("Part.text6", "XNC1"), ("Part.text7", "XNC2"),
    ("Part.text8", "mill"), ("Part.text9", "drill"), ("Part.text10", "groove"), ("Part.text11", "'#P('+part.id+')'"),
)

_CUTSAWFG_ROWS = tuple((f"Field{i}", e) for i, e in enumerate((
    "project.name", "material.name", "name", "description", "indexInOperation", "format('0.00',length)",
    "format('0.00',width)", "usedCount", "waste", _EDGE_TOP, _EDGE_BOTTOM, _EDGE_LEFT, _EDGE_RIGHT,
    "groove", "mill", "drill", "XNC1", "XNC2", "material.code", "product.name"), 1))

_NXCUTSAW_ROWS = tuple((f"F{i}", e) for i, e in enumerate((
    "name", "description", "usedCount", "format('0.00',detail.length)", "format('0.00',detail.width)", "XNC1", "XNC2",
    _EDGE_TOP, _EDGE_BOTTOM, _EDGE_LEFT, _EDGE_RIGHT, "mill", "drill", "", "", "", "", "", "", ""), 1))

_T_EXTRA = ("Дополнительные данные для этикеток", "Etiketkalar uchun qo'shimcha ma'lumotlar")
_T_DATA = ("Данные для этикеток", "Etiketkalar uchun ma'lumotlar")
_T_UDI = ("User defined part info records (PARTS_UDI)", "Detal bo'yicha foydalanuvchi yozuvlari (PARTS_UDI)")


def _tbl(title, rows, kind="labels") -> LabelTable:
    return LabelTable(title[0], title[1], tuple(rows), kind)


# ───────────────────────── Stanoklar sxemasi (19 ta pil markazi) ─────────────────────────
_SCM_LIST = "create_list_file"
_WINCUT = MachineSchema("scm_wincut", (
    _B("translit_filenames", "general", False, "Транслитерация имен файлов (Латинские буквы)",
       "Fayl nomlarini transliteratsiya qilish (lotin harflari)"),
    _B("print_labels", "labels", True, "Печать этикеток", "Etiketkalarni chop etish"),
    _C("label_mode", "labels", "normal", "Режим печати этикеток (Зависит от версии WinCut)",
       "Etiketka chop etish rejimi (WinCut versiyasiga bog'liq)", _LABEL_MODE, custom=True),
    _B(_SCM_LIST, "special", False, "Создавать файл списка для станков SCM", "SCM stanoklari uchun ro'yxat faylini yaratish"),
    _B("list_with_stack_height", "special", False, "Список с количеством плит и максимальной высотой пакета",
       "Plitalar soni va paketning maksimal balandligi bilan ro'yxat", enabled_if=_SCM_LIST),
    _B("list_sheet_size_in_name", "special", False, "Список с размерами листов в наименовании",
       "Nomida list o'lchamlari bor ro'yxat", enabled_if=_SCM_LIST),
    _B("list_maps_in_lst", "special", True, "Список и карты кроя помещать в папку списков (lst)",
       "Ro'yxat va kroy kartalarini ro'yxatlar papkasiga (lst) joylash", enabled_if=_SCM_LIST),
    _P("list_dir", "special", "C:\\wincut\\lst\\", "Путь к папке списков", "Ro'yxatlar papkasi yo'li", enabled_if=_SCM_LIST),
    _P("maps_dir", "special", "C:\\wincut\\prg\\", "Путь к папке карт кроя", "Kroy kartalari papkasi yo'li", enabled_if=_SCM_LIST),
    _B("mirror_cuts", "special", True, "Отзеркаливание всех резов", "Barcha kesimlarni akslantirish"),
    _B("spread_by_multiplicity", "special", False, "Разложить по одной полосе с учетом кратности",
       "Karraliligini hisobga olib bitta polosaga yoyish"),
    _MM("trim_uv", "special", 0, "Торцовка на U и V резах", "U va V kesimlarda torsovka"),
    _B("trim_with_kerf", "special", True, "Торцовка с учетом толщины пилы", "Torsovkada arra qalinligini hisobga olish"),
    _B("use_p_cuts", "special", False, "Использовать P-резы (5 уровня вращения)", "P-kesimlardan foydalanish (5-burilish darajasi)"),
    _I("vel_rotaz", "special", 3000, "VelRotaz", "VelRotaz"),
    _I("vel_avanz", "special", 30, "VelAvanz", "VelAvanz"),
), _tbl(_T_EXTRA, _WINCUT_ROWS))

_MAESTRO = MachineSchema("scm_maestrocut", (
    _B("print_labels", "labels", True, "Печать этикеток", "Etiketkalarni chop etish"),
    _C("label_mode", "labels", "normal", "Режим печати этикеток (Зависит от версии WinCut)",
       "Etiketka chop etish rejimi (WinCut versiyasiga bog'liq)", _LABEL_MODE, custom=True),
    _I("label_field_no", "labels", 64, "Номер поля для данных этикетки", "Etiketka ma'lumotlari maydonining raqami", 0, 9999),
    _B(_SCM_LIST, "special", True, "Создавать файл списка для станков SCM", "SCM stanoklari uchun ro'yxat faylini yaratish"),
    _B("list_sheet_size_in_name", "special", False, "Список с размерами листов в наименовании",
       "Nomida list o'lchamlari bor ro'yxat", enabled_if=_SCM_LIST),
    _P("list_dir", "special", "C:\\MaestroCut\\Client\\xMix\\", "Путь к папке списков", "Ro'yxatlar papkasi yo'li",
       enabled_if=_SCM_LIST),
    _B("mirror_cuts", "special", True, "Отзеркаливание всех резов", "Barcha kesimlarni akslantirish"),
    _B("spread_by_multiplicity", "special", False, "Разложить по одной полосе с учетом кратности",
       "Karraliligini hisobga olib bitta polosaga yoyish"),
    _MM("trim_uv", "special", 0, "Торцовка на U и V резах", "U va V kesimlarda torsovka"),
    _B("use_p_cuts", "special", False, "Использовать P-резы (5 уровня вращения)", "P-kesimlardan foydalanish (5-burilish darajasi)"),
), _tbl(_T_EXTRA, _MAESTRO_ROWS))

_PTX = MachineSchema("holzma_ptx", (
    _P("opt_params_file", "special", "", "Файл параметров оптимизации (*.prm)", "Optimallashtirish parametrlari fayli (*.prm)"),
    _P("saw_params_file", "special", "", "Файл параметров пилы (*.spm)", "Arra parametrlari fayli (*.spm)"),
    *_pre_cuts(),
    _B("label_data_at", "labels", False, "Печать этикеток: @Данные для этикеток", "Etiketka chop etish: @Etiketka ma'lumotlari"),
), _tbl(_T_UDI, (), "udi"))

_CADMATIC4 = MachineSchema("holzma_cadmatic4", (
    _C("orientation", "special", "first_cuts_vertical", "Ориентация", "Yo'nalish", (
        ("first_cuts_vertical", "Первые резы по вертикали", "Birinchi kesimlar vertikal"),
        ("first_cuts_horizontal", "Первые резы по горизонтали", "Birinchi kesimlar gorizontal")), custom=True),
    _C("cut_order", "special", "as_cadmatic", "Порядок резов", "Kesimlar tartibi", (
        ("as_cadmatic", "Как в настройках CadMatic", "CadMatic sozlamasidagidek"),
        ("from_trim", "От торцовки", "Torsovkadan boshlab"),
        ("from_remnant", "От остатка", "Qoldiqdan boshlab"))),
    _C("part_name", "special", "number", "Подпись детали (PartName)", "Detal yozuvi (PartName)",
       (("number", "Номер", "Raqam"),), custom=True),
    *_pre_cuts(),
    _C("label_target", "labels", "PartMaterial", "Добавить информацию для модуля печати этикеток в:",
       "Etiketka chop etish moduli uchun axborotni qo'shish joyi:", (("PartMaterial", "PartMaterial", "PartMaterial"),), custom=True),
), _tbl(_T_EXTRA, _CADMATIC4_ROWS))

_CADMATIC3 = MachineSchema("holzma_cadmatic3", (
    _C("orientation", "special", "first_cut", "Ориентация", "Yo'nalish", (
        ("first_cut", "По первому резу", "Birinchi kesim bo'yicha"),
        ("horizontal", "Горизонтально", "Gorizontal"), ("vertical", "Вертикально", "Vertikal")), custom=True),
    _B("generate_label_files", "labels", False, "Генерировать файлы для этикеток", "Etiketka fayllarini yaratish"),
))

_OSI = MachineSchema("biesse_osi", (
    _S("program_version", "labels", "", "Версия программы", "Dastur versiyasi"),
    _C("orientation", "special", "horizontal", "Ориентация", "Yo'nalish", _ORIENT_HV),
    _C("order_name", "special", "order_date", "Заказ - Наименование", "Buyurtma — nomi",
       (("order_date", "Дата заказа", "Buyurtma sanasi"),), custom=True),
), _tbl(_T_DATA, _OSI_ROWS))

_NC300 = MachineSchema("biesse_nc300", (
    _C("orientation", "special", "horizontal", "Ориентация", "Yo'nalish", _ORIENT_HV),
    _S("rdiv", "special", "", "RDIV", "RDIV"),
    _S("magp", "special", "", "MAGP", "MAGP"),
))

_PC6 = MachineSchema("felder_format4_pc6", (
    _B("remnants_on_maps", "labels", False, "Помещать остатки на карты кроя", "Qoldiqlarni kroy kartalariga joylash"),
    _B("label_by_part_number", "labels", False, "Распечатывать этикетку в соответствии с номером детали (не для всех версий)",
       "Etiketkani detal raqamiga mos chop etish (hamma versiyalarda emas)"),
), _tbl(_T_DATA, _PC6_ROWS))

_PC7 = MachineSchema("felder_format4_pc7", (), _tbl(_T_DATA, _PC7_ROWS))

_F4CLASSIC = MachineSchema("felder_f4classic", (
    _B("generate_label_files", "label_files", True, "Генерировать файлы для этикеток", "Etiketka fayllarini yaratish"),
    *_label_dx_dy("label_files", 60.5),
    _S("zpl_header", "label_files", "", "ZPL Header", "ZPL sarlavhasi"),
    _T("label_template", "label_files", "Шаблон этикетки (библиотека)", "Etiketka shabloni (kutubxona)",
       note_ru="файл этикетки станка", note_uz="stanokning etiketka fayli"),
))

_HOMAG = MachineSchema("homag_chf", (
    _MM("trim_zw", "trim", 0, "Торцовка на Z и W резах", "Z va W kesimlarda torsovka"),
    _B("latin_letters", "special", False, "Использовать латинские буквы", "Lotin harflaridan foydalanish"),
    _C("orientation", "special", "first_cut_5", "Ориентация", "Yo'nalish",
       (("first_cut_5", "По первому резу (5 уровня вращения)", "Birinchi kesim bo'yicha (5-burilish darajasi)"),), custom=True),
))

_KDT_QK = MachineSchema("kdt_presize_qk", (
    _B("trim_with_kerf", "trim", True, "Включать толщину пилы в торцовку", "Arra qalinligini torsovkaga kiritish"),
    _MM("trim_from_third_rotation", "trim", 0, "Торцовка начиная с третьего вращения", "Uchinchi burilishdan boshlab torsovka"),
    _B("generate_label_files", "labels", True, "Генерировать файлы для этикеток", "Etiketka fayllarini yaratish"),
    _B("distribute_maps_to_packs", "special", True, "Распределять количество карт кроя по пакетам",
       "Kroy kartalari sonini paketlarga taqsimlash"),
))

_KDT_XML = MachineSchema("kdt_presize_xml", (
    _B("generate_label_files", "label_files", True, "Генерировать файлы для этикеток", "Etiketka fayllarini yaratish"),
    *_label_dx_dy("label_files", 60.5),
    _T("label_template", "label_files", "Шаблон этикетки (библиотека)", "Etiketka shabloni (kutubxona)",
       note_ru="файл этикетки станка", note_uz="stanokning etiketka fayli"),
))

_SCHEER = MachineSchema("scheer", (
    *_label_dx_dy("labels", 40),
    _B("barcode", "labels", False, "Штрихкод", "Shtrixkod"),
))

_CUTSAWFG = MachineSchema("nanxing_cutsawfg", (), _tbl(_T_DATA, _CUTSAWFG_ROWS))
_NXCUTSAW = MachineSchema("nanxing_nxcutsaw", (), _tbl(_T_DATA, _NXCUTSAW_ROWS))

_SHELLING = MachineSchema("shelling_mcs", (
    _MM("trim_from_third_rotation", "trim", 0, "Торцовка начиная с третьего вращения", "Uchinchi burilishdan boshlab torsovka"),
), _tbl(_T_UDI, (), "udi"))

_ELMO3 = MachineSchema("elmo3", (
    _B("trim", "trim", False, "Торцовка", "Torsovka"),
    _MM("saw_blade_height", "special", 49, "Высота пильного диска", "Arra diski balandligi"),
    _F("height_width_ratio", "special", 4, "Соотношение высота-ширина детали", "Detal balandligi va eni nisbati"),
    _MM("fence_long_min", "limits", 2, "Продольный упор (Min)", "Bo'ylama tirgak (min)"),
    _MM("fence_long_max", "limits", 1600, "Продольный упор (Max)", "Bo'ylama tirgak (maks)"),
    _MM("fence_cross_min", "limits", 146, "Поперечный упор (Min)", "Ko'ndalang tirgak (min)"),
    _MM("fence_cross_max", "limits", 3200, "Поперечный упор (Max)", "Ko'ndalang tirgak (maks)"),
), info_ru="Разъём USB: программы должны быть на флешке, разархивированные в папку «SAW»",
    info_uz="USB: dasturlar flesh-xotirada «SAW» papkasiga arxivdan chiqarilgan holda bo'lishi kerak")

_GLASS = MachineSchema("glass_gcode", (
    _C("version", "special", "ncstudio_v7", "Версия", "Versiya", (("ncstudio_v7", "NCStudio v7", "NCStudio v7"),), custom=True),
))

_FASTPANEL = MachineSchema("fastpanel", (
    _C("version", "special", "2.1.5", "Версия программы FastPanel", "FastPanel dasturi versiyasi",
       (("2.1.5", "2.1.5", "2.1.5"), ("2.1.4", "2.1.4", "2.1.4"))),
), info_ru="Версия 2.1.5 — не более 3 вращений, 2.1.4 — не более 2 (раскрой при необходимости выполняется заново)",
    info_uz="2.1.5 versiya — ko'pi bilan 3 burilish, 2.1.4 — ko'pi bilan 2 (kerak bo'lsa kroy qayta bajariladi)")

_ALL = (_FASTPANEL, _WINCUT, _MAESTRO, _PTX, _CADMATIC4, _CADMATIC3, _OSI, _NC300, _PC6, _PC7, _F4CLASSIC, _HOMAG, _KDT_QK, _KDT_XML,
        _SCHEER, _CUTSAWFG, _NXCUTSAW, _SHELLING, _ELMO3, _GLASS)
SCHEMAS: dict[str, MachineSchema] = {s.key: s for s in _ALL}


def schema_of(key: str) -> MachineSchema:
    """Stanok sxemasi; ishlov markazlari (cnc) uchun — bo'sh sxema (parametrsiz, jadvalsiz)."""
    return SCHEMAS.get(key) or MachineSchema(key)


def defaults(key: str) -> dict[str, Any]:
    return {p.key: p.default for p in schema_of(key).params}


# ───────────────────────── Qiymatlarni tekshirish ─────────────────────────
def _num(v: Any) -> float:
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise ValueError(_("val_number"))
    if not math.isfinite(v):
        raise ValueError(_("val_finite"))
    return float(v)


def _in_range(p: Param, x: float) -> None:
    if p.min is not None and x < p.min:
        raise ValueError(_("val_ge", v=f"{p.min:g}"))
    if p.max is not None and x > p.max:
        raise ValueError(_("val_le", v=f"{p.max:g}"))


def coerce(p: Param, v: Any) -> Any:
    """Qiymatni parametr turiga keltiradi (qat'iy: «true» matni bool emas). Xato — ValueError (foydalanuvchi tilida)."""
    t = p.type
    if t == "bool":
        if not isinstance(v, bool):
            raise ValueError(_("val_bool"))
        return v
    if t == "int":
        x = _num(v)
        if x != int(x):
            raise ValueError(_("val_int"))
        _in_range(p, x)
        return int(x)
    if t in ("mm", "float"):
        x = _num(v)
        if abs(x) > MAX_NUM:
            raise ValueError(_("val_le", v=f"{MAX_NUM:g}"))
        _in_range(p, x)
        return x
    if not isinstance(v, str):
        raise ValueError(_("val_str"))
    if t == "string":
        if len(v) > MAX_STR:
            raise ValueError(_("val_str_long", v=MAX_STR))
        if _CTRL.search(v):
            raise ValueError(_("pp_ctrl_chars"))
        return v
    if t == "path":                                       # faqat satr: server fayl tizimiga tegmaydi
        if len(v) > MAX_PATH:
            raise ValueError(_("val_str_long", v=MAX_PATH))
        if _PATH_BAD.search(v):
            raise ValueError(_("pp_path_chars"))
        return v
    if t == "template":
        if v == "" or _TPL_REF.fullmatch(v):
            return v
        raise ValueError(_("pp_tpl_ref"))
    if t == "choice":
        if any(o.value == v for o in p.options):
            return v
        if p.custom and 0 < len(v) <= MAX_CHOICE and not _CTRL.search(v):
            return v
        raise ValueError(_("val_choice"))
    raise ValueError(_("val_generic"))


def validate_params(key: str, raw: Any) -> tuple[dict[str, Any], list[dict]]:
    """`{param: qiymat}` → (tozalangan qiymatlar, xatolar [{key, message}]). Noma'lum kalit — xato."""
    by_key = {p.key: p for p in schema_of(key).params}
    out: dict[str, Any] = {}
    errors: list[dict] = []
    if not isinstance(raw, dict):
        return out, [dict(key="", message=_("val_dict"))]
    for k, v in raw.items():
        p = by_key.get(k)
        if p is None:
            errors.append(dict(key=str(k)[:80], message=_("pp_param_unknown", k=str(k)[:80])))
            continue
        try:
            out[k] = coerce(p, v)
        except ValueError as e:
            errors.append(dict(key=k, message=str(e)))
    return out, errors


def resolve_params(key: str, saved: dict[str, Any] | None) -> dict[str, Any]:
    """Standart qiymatlar ustiga saqlanganlari (eski/noma'lum yoki yaroqsiz saqlangan qiymat — e'tiborga olinmaydi)."""
    out = defaults(key)
    for p in schema_of(key).params:
        if saved and p.key in saved:
            try:
                out[p.key] = coerce(p, saved[p.key])
            except ValueError:
                pass
    return out


# ───────────────────────── Etiketka maydonlarini tekshirish ─────────────────────────
def validate_label_fields(key: str, raw: Any) -> tuple[list[dict], list[dict]]:
    """`[{name, expr}]` → (tozalangan qatorlar, xatolar [{index, field, name, message}]).
    Nomlar bo'sh bo'lmasin va takrorlanmasin; ifoda bo'sh bo'lishi mumkin (qiymat «»), aks holda sintaksis `expr.compile_check`."""
    out: list[dict] = []
    errors: list[dict] = []
    if schema_of(key).label_table is None:
        return out, [dict(index=-1, field="", name="", message=_("pp_no_label_table"))]
    if not isinstance(raw, list):
        return out, [dict(index=-1, field="", name="", message=_("val_list"))]
    if len(raw) > MAX_LABEL_ROWS:
        return out, [dict(index=-1, field="", name="", message=_("pp_label_rows_limit", n=MAX_LABEL_ROWS))]
    seen: set[str] = set()
    for i, row in enumerate(raw):
        if not isinstance(row, dict):
            errors.append(dict(index=i, field="", name="", message=_("val_dict")))
            continue
        name, src = row.get("name", ""), row.get("expr", "")
        if not isinstance(name, str):
            errors.append(dict(index=i, field="name", name="", message=_("val_str")))
            continue
        name = name.strip()
        e_name = check_name(name, seen)
        if e_name:
            errors.append(dict(index=i, field="name", name=name, message=e_name))
        seen.add(name)
        if not isinstance(src, str):
            errors.append(dict(index=i, field="expr", name=name, message=_("val_str")))
            continue
        e_expr = check_expr_syntax(src)
        if e_expr:
            errors.append(dict(index=i, field="expr", name=name, message=e_expr))
        out.append(dict(name=name, expr=src.strip()))
    return out, errors


def check_name(name: str, seen: set[str]) -> str | None:
    """Maydon nomi xatosi matni yoki None: bo'sh emas, ≤ 80 belgi, boshqaruv belgisiz, takrorlanmagan (`seen`)."""
    if not name:
        return _("pp_label_name_empty")
    if len(name) > MAX_LABEL_NAME:
        return _("val_str_long", v=MAX_LABEL_NAME)
    if _CTRL.search(name):
        return _("pp_ctrl_chars")
    if name in seen:
        return _("pp_label_name_dup", n=name)
    return None


def check_expr_syntax(src: str) -> str | None:
    """Ifoda sintaksisi (bo'sh ifoda — to'g'ri: qiymat «»). Xato matni yoki None. Ifoda faqat `services/expr.py` da tekshiriladi."""
    s = src.strip()
    if not s:
        return None
    try:
        expr.compile_check(s)
    except ValueError as e:
        return str(e)
    except Exception:  # noqa: BLE001 — dvigatel kutilmagan xato bersa ham API 500 qaytarmasin
        return _("xnc.e_syntax")
    return None


def default_label_rows(key: str) -> list[dict]:
    t = schema_of(key).label_table
    return [dict(name=n, expr=e) for n, e in t.rows] if t else []
