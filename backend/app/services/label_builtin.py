"""O'rnatilgan namuna shablonlar (o'zimiz yozgan; foydalanuvchi ularni «nusxa» qilib o'zgartiradi).

 detail       — Деталь (QR): hozirgi qat'iy etiketkaning shablon ko'rinishi (standart; QR matni `MXK:…` o'zgarmagan — MES skaneri)
 detail_c128  — Деталь (Code128 + chizma): loyiha № + detal ID (4) + hisoblagich (4) — 1D shtrixkod
 waste        — Остаток: qoldiq etiketkasi (raqam, o'lcham, deloviy belgisi, karta QR)
 product      — Изделие: mahsulot etiketkasi (nom, kod, soni, mijoz, telefon, QR)

Koordinatalar mm; o'lcham `label.width` / `label.height` ga nisbatan hisoblanadi — shablon boshqa o'lchamga ham moslashadi.
"""
from __future__ import annotations

import copy
from typing import Optional

DEFAULT_KEY = "detail"

_LANG_MAP = "if(label.lang='uz','karta','карта')"

DETAIL = {
    "v": 1, "name": "Деталь (QR)", "size": {"w": 58, "h": 40},
    "params": [
        {"name": "qr", "type": "boolean", "default": True, "title": "QR"},
        {"name": "show_edges", "type": "boolean", "default": True, "title": "Схема кромок"},
        {"name": "show_product", "type": "boolean", "default": True, "title": "Изделие"},
        {"name": "show_map", "type": "boolean", "default": True, "title": "Номер карты"},
    ],
    "vars": [
        {"name": "k", "expr": "max(0.55, min(1, label.height/40, label.width/58))"},
        {"name": "pad", "expr": "1.6*k"},
        {"name": "qs", "expr": "max(11, 15*k)"},
        {"name": "ih", "expr": "max(20, 34*k)*0.2646"},
        {"name": "iw", "expr": "ih*1.6"},
        {"name": "has_edges", "expr": "show_edges and edge.count > 0"},
        {"name": "rw", "expr": "max(qs, if(has_edges, iw, 0))"},
        {"name": "lw", "expr": "label.width - 2*pad - rw - 1"},
        {"name": "y1", "expr": "5.4*k"},
        {"name": "y2", "expr": "y1 + 3.7*k"},
        {"name": "y3", "expr": "y2 + 5.4*k"},
        {"name": "has_prod", "expr": "show_product and len(product.name) > 0"},
        {"name": "y4", "expr": "y3 + 3.1*k"},
        {"name": "y5", "expr": "if(has_prod, y4 + 3.1*k, y4)"},
        {"name": "cw", "expr": "len(part.id)*1.6*k + 2*k"},
    ],
    "elements": [
        {"t": "text", "x": "pad", "y": "1.2*k", "size": "2.4*k", "maxw": "label.width - 2*pad",
         "text": "'№'+project.number+' '+left(project.name,28)"},
        {"t": "line", "x1": "pad", "y1": "4.5*k", "x2": "label.width - pad", "y2": "4.5*k", "stroke": {"w": 0.2, "color": "#999"}},
        # detal qatori (asosiy; hozirgi qat'iy etiketkaning ko'rinishi)
        {"t": "if", "cond": "label.kind = 'part'", "then": [
            {"t": "rect", "x": "pad", "y": "y1", "w": "cw", "h": "3.4*k", "fill": "#111"},
            {"t": "text", "x": "pad + k", "y": "y1 + 0.2*k", "size": "2.6*k", "bold": True, "color": "#fff", "text": "part.id"},
            {"t": "text", "x": "pad + cw + 0.8", "y": "y1 + 0.2*k", "size": "2.6*k", "bold": True, "maxw": "lw - cw - 0.8",
             "text": "left(part.title,40)"},
            {"t": "text", "x": "pad", "y": "y2", "size": "4.2*k", "bold": True, "maxw": "lw", "text": "part.dims"},
            {"t": "text", "x": "pad", "y": "y3", "size": "2.3*k", "maxw": "lw", "text": "left(material.name,40)"},
            {"t": "if", "cond": "has_prod", "then": [
                {"t": "text", "x": "pad", "y": "y4", "size": "2.3*k", "maxw": "lw", "text": "left(product.name,36)"}]},
            {"t": "text", "x": "pad", "y": "y5", "size": "2.3*k", "color": "#333", "maxw": "lw",
             "text": "part.copy+'/'+part.copies+if(show_map and map.index > 0, ' · '+" + _LANG_MAP + "+' '+map.index, '')"},
            {"t": "if", "cond": "has_edges", "then": [
                {"t": "edges", "x": "label.width - pad - iw", "y": "y1", "w": "iw", "h": "ih"}]}],
         "else": [
            {"t": "if", "cond": "label.kind = 'waste'", "then": [      # qoldiq qatori (print_wastes)
                {"t": "text", "x": "pad", "y": "y1", "size": "7*k", "bold": True, "maxw": "lw", "text": "'Д'+waste.number"},
                {"t": "text", "x": "pad", "y": "y1 + 8*k", "size": "3.6*k", "bold": True, "maxw": "lw",
                 "text": "format('0.##', waste.length)+' × '+format('0.##', waste.width)"},
                {"t": "text", "x": "pad", "y": "y1 + 13*k", "size": "2.3*k", "maxw": "lw", "text": "left(material.name,40)"},
                {"t": "text", "x": "pad", "y": "y1 + 16.1*k", "size": "2.3*k", "color": "#333", "maxw": "lw",
                 "text": "format('0.00', waste.area)+' '+if(label.lang='uz','m²','м²')+' · '+" + _LANG_MAP + "+' '+map.index"
                         "+if(waste.business, if(label.lang='uz',' · deloviy',' · деловой'), '')"}],
             "else": [                                                  # mahsulot qatori (source=products)
                {"t": "text", "x": "pad", "y": "y1", "size": "3.4*k", "bold": True, "wrap": True, "lines": 2, "maxw": "lw",
                 "text": "product.name"},
                {"t": "text", "x": "pad", "y": "y1 + 9*k", "size": "2.6*k", "maxw": "lw", "text": "product.code"},
                {"t": "text", "x": "pad", "y": "y1 + 12.6*k", "size": "2.6*k", "bold": True, "maxw": "lw",
                 "text": "part.copy+'/'+part.copies"},
                {"t": "text", "x": "pad", "y": "y1 + 16.2*k", "size": "2.3*k", "color": "#333", "maxw": "lw",
                 "text": "left(project.customer,30)"}]}]},
        {"t": "if", "cond": "qr and len(label.code) > 0", "then": [
            {"t": "barcode", "kind": "qr", "x": "label.width - pad - qs", "y": "y1 + if(has_edges, ih + 0.5, 0)",
             "size": "qs", "data": "label.code"}]},
    ],
}

DETAIL_C128 = {
    "v": 1, "name": "Деталь (Code128)", "size": {"w": 58, "h": 40},
    "params": [
        {"name": "caption", "type": "boolean", "default": True, "title": "Текст под штрихкодом"},
        {"name": "drawing", "type": "boolean", "default": True, "title": "Чертёж детали"},
        {"name": "margin", "type": "double", "default": 1.6, "title": "Поля, мм"},
    ],
    "vars": [
        {"name": "bh", "expr": "if(caption, 10.5, 8)"},
        {"name": "cw", "expr": "len(part.id)*1.6 + 2"},
        {"name": "lw", "expr": "label.width - 2*margin - if(drawing, 19, 0)"},
        {"name": "code", "expr": "''+project.number+rspace(right(part.id,4),4,'0')+rspace(part.counter,4,'0')"},
    ],
    "elements": [
        {"t": "text", "x": "margin", "y": "1.2", "size": 2.4, "maxw": "label.width - 2*margin",
         "text": "'№'+project.number+'  '+left(project.name,26)"},
        {"t": "line", "x1": "margin", "y1": 4.5, "x2": "label.width - margin", "y2": 4.5, "stroke": {"w": 0.2, "color": "#999"}},
        {"t": "rect", "x": "margin", "y": 5.4, "w": "cw", "h": 3.4, "fill": "#111"},
        {"t": "text", "x": "margin + 1", "y": 5.6, "size": 2.6, "bold": True, "color": "#fff", "text": "part.id"},
        {"t": "text", "x": "margin + cw + 0.8", "y": 5.6, "size": 2.6, "bold": True, "maxw": "lw - cw - 0.8",
         "text": "left(part.title,40)"},
        {"t": "text", "x": "margin", "y": 9.4, "size": 3.8, "bold": True, "maxw": "lw", "text": "part.dims"},
        {"t": "text", "x": "margin", "y": 14.2, "size": 2.3, "maxw": "lw", "text": "left(material.name,40)"},
        {"t": "text", "x": "margin", "y": 17.2, "size": 2.3, "maxw": "lw", "color": "#333", "text": "left(product.name,36)"},
        {"t": "if", "cond": "drawing", "then": [
            {"t": "part", "x": "label.width - margin - 18", "y": 5.4, "w": 18, "h": "label.height - margin - bh - 6.5"}]},
        {"t": "barcode", "kind": "code128", "x": "margin", "y": "label.height - margin - bh", "w": "label.width - 2*margin",
         "h": "bh", "data": "code", "caption": "caption"},
    ],
}

WASTE = {
    "v": 1, "name": "Остаток", "size": {"w": 58, "h": 40},
    "params": [{"name": "qr", "type": "boolean", "default": True, "title": "QR"}],
    "vars": [
        {"name": "pad", "expr": "1.6"},
        {"name": "qs", "expr": "min(15, label.height - 12)"},
        {"name": "lw", "expr": "label.width - 2*pad - if(qr, qs + 1, 0)"},
    ],
    "elements": [
        {"t": "text", "x": "pad", "y": 1.2, "size": 2.4, "maxw": "label.width - 2*pad",
         "text": "'№'+project.number+' '+left(project.name,28)"},
        {"t": "line", "x1": "pad", "y1": 4.5, "x2": "label.width - pad", "y2": 4.5, "stroke": {"w": 0.2, "color": "#999"}},
        {"t": "text", "x": "pad", "y": 5.4, "size": 8, "bold": True, "maxw": "lw", "text": "'Д'+waste.number"},
        {"t": "if", "cond": "waste.business", "then": [
            {"t": "text", "x": "pad", "y": 14.6, "size": 2.6, "bold": True, "maxw": "lw",
             "text": "if(label.lang='uz','DELOVOY QOLDIQ','ДЕЛОВОЙ ОСТАТОК')"}]},
        {"t": "text", "x": "pad", "y": 18.2, "size": 4.4, "bold": True, "maxw": "lw",
         "text": "format('0.##', waste.length)+' × '+format('0.##', waste.width)"},
        {"t": "text", "x": "pad", "y": 24, "size": 2.3, "maxw": "lw", "text": "left(material.name,40)"},
        {"t": "text", "x": "pad", "y": 27.2, "size": 2.3, "color": "#333", "maxw": "lw",
         "text": "format('0.00', waste.area)+' '+if(label.lang='uz','m²','м²')+' · '+" + _LANG_MAP + "+' '+map.index"},
        {"t": "if", "cond": "qr", "then": [
            {"t": "barcode", "kind": "qr", "x": "label.width - pad - qs", "y": 5.4, "size": "qs", "data": "label.code"}]},
    ],
}

PRODUCT = {
    "v": 1, "name": "Изделие", "size": {"w": 100, "h": 60},
    "params": [{"name": "qr", "type": "boolean", "default": True, "title": "QR"}],
    "vars": [
        {"name": "pad", "expr": "2"},
        {"name": "qs", "expr": "min(22, label.height - 14)"},
        {"name": "lw", "expr": "label.width - 2*pad - if(qr, qs + 2, 0)"},
    ],
    "elements": [
        {"t": "text", "x": "pad", "y": 1.5, "size": 2.8, "maxw": "label.width - 2*pad",
         "text": "'№'+project.number+' '+left(project.name,40)"},
        {"t": "line", "x1": "pad", "y1": 5.4, "x2": "label.width - pad", "y2": 5.4, "stroke": {"w": 0.25, "color": "#999"}},
        {"t": "text", "x": "pad", "y": 7, "size": 5.2, "bold": True, "wrap": True, "lines": 2, "maxw": "lw", "text": "product.name"},
        {"t": "text", "x": "pad", "y": 21, "size": 3.6, "maxw": "lw", "text": "product.code"},
        {"t": "text", "x": "pad", "y": 27, "size": 3.6, "bold": True, "maxw": "lw",
         "text": "if(label.lang='uz','Soni: ','Кол-во: ')+part.copy+' / '+part.copies"},
        {"t": "text", "x": "pad", "y": 33, "size": 3, "maxw": "lw", "text": "project.customer"},
        {"t": "text", "x": "pad", "y": 38, "size": 3, "maxw": "lw", "text": "product.phone1"},
        {"t": "text", "x": "pad", "y": 43, "size": 3, "color": "#333", "maxw": "lw", "text": "product.date"},
        {"t": "if", "cond": "qr", "then": [
            {"t": "barcode", "kind": "qr", "x": "label.width - pad - qs", "y": 7, "size": "qs", "data": "label.code"}]},
    ],
}

# kalit → (kind, rus nomi, o'zbek nomi, shablon)
BUILTIN: dict[str, tuple[str, str, str, dict]] = {
    "detail": ("part", "Деталь (QR) — стандартная", "Detal (QR) — standart", DETAIL),
    "detail_c128": ("part", "Деталь (Code128 + чертёж)", "Detal (Code128 + chizma)", DETAIL_C128),
    "waste": ("waste", "Остаток", "Qoldiq", WASTE),
    "product": ("product", "Изделие", "Mahsulot", PRODUCT),
}


def builtin_template(key: str, lang: str = "ru") -> Optional[dict]:
    """O'rnatilgan shablonning nusxasi (nomi tilga mos) yoki None."""
    item = BUILTIN.get(key)
    if item is None:
        return None
    tpl = copy.deepcopy(item[3])
    tpl["name"] = item[2] if lang == "uz" else item[1]
    return tpl


def builtin_list(lang: str = "ru") -> list[dict]:
    out = []
    for key, (kind, ru, uz, tpl) in BUILTIN.items():
        out.append({"id": f"builtin:{key}", "key": key, "name": uz if lang == "uz" else ru, "builtin": True, "kind": kind,
                    "size": tpl["size"], "params": [{k: v for k, v in p.items()} for p in tpl["params"]]})
    return out
