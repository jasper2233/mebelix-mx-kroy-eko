"""W9 · LB: tayyor shablon fayli (`<program>` XML) uchun SINTETIK fikstura — hamma matn va qiymat shu yerda o'ylab topilgan
(hech qanday korxona yoki dastur namunasi ko'chirilmagan; faqat fayl tuzilmasi — teg va atribut nomlari)."""
import base64
import struct
import zlib
from xml.sax.saxutils import quoteattr


def png(w: int = 2, h: int = 2) -> bytes:
    """Haqiqiy (kichik) PNG: kulrang w×h."""
    def chunk(tag: bytes, data: bytes) -> bytes:
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    raw = b"".join(b"\x00" + b"\x80" * w for _ in range(h))
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 0, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) \
        + chunk(b"IEND", b"")


def data_uri(raw: bytes, kind: str = "png") -> str:
    return f"data:image/{kind};base64," + base64.b64encode(raw).decode()


def el(tag: str, children=(), **attrs) -> str:
    """`<tag a="…">…</tag>`; `None` qiymatli atribut tushiriladi."""
    a = " ".join(f"{k}={quoteattr(str(v))}" for k, v in attrs.items() if v is not None)
    inner = "".join(children)
    return f"<{tag} {a}>{inner}</{tag}>" if inner else f"<{tag} {a}/>"


def program(children, **attrs) -> str:
    base = dict(columns="3", dx="70", dy="50", gap="2", margin="true", printMode="0", rows="5")
    base.update(attrs)
    return '<?xml version="1.0" encoding="UTF-8"?>' + el("program", children, **base)


def text(x, y, expr, **kw) -> str:
    a = dict(enable="true", x=x, y=y, text=expr, fillColor="#000000", fontName="Arial", fontSize="3", fontBold="false",
             fontItalic="false", rowHeight="3", ratio="true", align="left", valign="top", multiline="false", wordBreak="false")
    a.update(kw)
    return el("text", **a)


def sample_program(img: bytes | None = None) -> str:
    """Hamma element turlari: par (standart/foydalanuvchi), var, xy, if/else, text (turli), qrcode, rect/line, image, part."""
    pic = data_uri(img or png())
    inner = [
        el("if", [
            text("2", "3", "'Title'", w="30", fontBold="true"),
            text("0", "10", "ns(part.code)", w="inner", align="center", fontName="Courier New", fontSize="2.5",
                 fillColor="#FF0000", fontItalic="true", comment="centered"),
            text("10", "14", "format('0.#',part.id)", w="20", align="right"),
            text("2", "20", "name", w="30", h="9", multiline="true", wordBreak="true", rowHeight="3"),
            el("qrcode", enable="true", x="45", y="2", sz="18", text="'ID-'+part.id", fillColor="#000000"),
            el("rect", enable="true", x="2", y="30", w="30", h="0", strokeColor="rgb(255,0,0)", strokeWidth="0.3", strokeDash="0",
               fillColor="", fillHatch="1"),
            el("rect", enable="true", x="2", y="32", w="20", h="8", strokeColor="#000000", strokeWidth="0.25", strokeDash="2",
               fillColor="#EEEEEE", fillHatch="3"),
            el("image", enable="true", x="50", y="30", w="8", h="8", imgdata=pic, ratio="true", expr=""),
            el("part", enable="true", x="40", y="22", w="18", h="24", optimalTurn="true", size="true", edgeband="true"),
            el("if", [text("2", "42", "'LOGO'")], condition="show_logo", expand="true"),
            el("else", [text("2", "42", "'NOLOGO'")], expand="true"),
        ], condition="not waste", expand="true"),
        el("else", [text("0", "20", "'WASTE '+indexInOperation", w="la2", align="center", fontSize="5")], expand="true"),
    ]
    children = [
        el("par", name="part.code", type="string", expr="TEST-1"),
        el("par", name="part.id", type="integer", expr="7"),
        el("par", name="waste", type="boolean", expr="false"),
        el("par", name="etn", type="string", expr="X"),
        el("par", name="gap2", type="double", expr="2.5", comment="Ichki oraliq"),
        el("par", name="show_logo", type="boolean", expr="true", comment="Logo"),
        el("par", name="tag", type="string", expr="HELLO"),
        el("par", name="copies_n", type="integer", expr="3"),
        el("par", name="calc_par", type="double", expr="dx/2"),
        el("var", name="inner", type="double", expr="dx-gap2*2", comment="Ichki eni"),
        el("var", name="la2", type="double", expr="dx-4"),
        el("var", name="prefix", type="string", expr="'P-'"),
        el("xy", enable="true", x="1", y="2"),
        *inner,
    ]
    return program(children)

