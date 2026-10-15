"""Ifoda tili hujjatlari: har funksiya uchun ru/uz tavsif va misol (muharrir yordamchisi va «Справка → Выражения» uchun).

Matnlar shu loyiha uchun noldan yozilgan. Misol natijalari `services/expr.py` dvigatelida **jonli hisoblanadi** (hujjat eskirmaydi);
tasodifiy / vaqtga bog'liq funksiyalar (`random`, `uuid`, `now`) uchun natija tavsifiy matn (`DYNAMIC`).
Ro'yxat tarkibi `expr.FUNCTION_GROUPS` bilan mos bo'lishi shart (test: `tests/test_expr_api_w6.py`).
"""
from __future__ import annotations

import datetime as _dt
import random as _random
from functools import lru_cache

from . import expr as E

# guruh kaliti → (ru, uz); tartib — ro'yxatdagi tartib
GROUP_TITLES: dict[str, tuple[str, str]] = {
    "math": ("Математические", "Matematik"),
    "text": ("Строковые", "Matn"),
    "convert": ("Преобразование чисел", "Sonlarni o'zgartirish"),
    "misc": ("Прочие", "Boshqa"),
}
GROUP_ORDER = ["math", "text", "convert", "misc"]

# funksiya nomi (kichik harf) → (ru tavsif, uz tavsif, misol)
DOCS: dict[str, tuple[str, str, str]] = {
    # ── matematik ──
    "abs": ("Модуль числа: значение без знака.", "Sonning moduli: ishorasiz qiymat.", "abs(-7)"),
    "acos": ("Арккосинус: угол, косинус которого равен x (x от −1 до 1). Результат в радианах (в режиме градусов — в градусах).",
             "Arkkosinus: kosinusi x ga teng burchak (x −1 dan 1 gacha). Natija radianda (gradus rejimida — gradusda).", "acos(-1)"),
    "acot": ("Арккотангенс: угол, котангенс которого равен x.", "Arkkotangens: kotangensi x ga teng burchak.", "acot(1)"),
    "asec": ("Арксеканс: угол, секанс которого равен x (|x| ≥ 1).", "Arksekans: sekansi x ga teng burchak (|x| ≥ 1).", "asec(2)"),
    "asin": ("Арксинус: угол, синус которого равен x (x от −1 до 1).", "Arksinus: sinusi x ga teng burchak (x −1 dan 1 gacha).", "asin(1)"),
    "atan": ("Арктангенс: угол, тангенс которого равен x.", "Arktangens: tangensi x ga teng burchak.", "atan(1)"),
    "ceil": ("Округление вверх до целого; результат дробного типа (double).",
             "Butun songa yuqoriga yaxlitlash; natija double turida.", "ceil(1.2)"),
    "cos": ("Косинус угла x (по умолчанию x в радианах).", "x burchakning kosinusi (standart holda x radianda).", "cos(0)"),
    "cosh": ("Гиперболический косинус.", "Giperbolik kosinus.", "cosh(0)"),
    "cot": ("Котангенс угла x.", "x burchakning kotangensi.", "cot(1)"),
    "coth": ("Гиперболический котангенс (x ≠ 0).", "Giperbolik kotangens (x ≠ 0).", "coth(1)"),
    "exp": ("Экспонента: число e в степени x.", "Eksponenta: e sonining x darajasi.", "exp(1)"),
    "floor": ("Округление вниз до целого; результат дробного типа (double).",
              "Butun songa pastga yaxlitlash; natija double turida.", "floor(-1.5)"),
    "ln": ("Натуральный логарифм (x > 0).", "Natural logarifm (x > 0).", "ln(e)"),
    "log": ("Десятичный логарифм (x > 0).", "O'nli logarifm (x > 0).", "log(1000)"),
    "log2": ("Двоичный логарифм (x > 0).", "Ikkilik logarifm (x > 0).", "log2(8)"),
    "logx": ("Логарифм x по заданному основанию: logx(x, основание).", "x ning berilgan asos bo'yicha logarifmi: logx(x, asos).", "logx(9, 3)"),
    "max": ("Наибольшее из значений (1–50 аргументов). Если среди них есть дробное — результат дробный.",
            "Qiymatlarning eng kattasi (1–50 ta argument). Ichida kasr bo'lsa — natija kasr.", "max(2, 9, 4)"),
    "min": ("Наименьшее из значений (1–50 аргументов). Если среди них есть дробное — результат дробный.",
            "Qiymatlarning eng kichigi (1–50 ta argument). Ichida kasr bo'lsa — natija kasr.", "min(2, 9, 4)"),
    "random": ("Случайное число от 0 (включительно) до 1 (не включая); при каждом вычислении новое.",
               "0 dan (shu jumladan) 1 gacha (shu jumladan emas) tasodifiy son; har hisoblashda yangi.", "random()"),
    "round": ("Округление до ближайшего целого, половина — вверх (round(2.5) = 3, round(−1.5) = −1). Второй аргумент (необязательный) — число знаков после запятой.",
              "Eng yaqin butunga yaxlitlash, yarim — yuqoriga (round(2.5) = 3, round(−1.5) = −1). Ikkinchi argument (ixtiyoriy) — kasr xonalari soni.",
              "round(2.567, 2)"),
    "sec": ("Секанс угла x (1 / cos x).", "x burchakning sekansi (1 / cos x).", "sec(0)"),
    "sign": ("Знак числа: 1.0, −1.0 или 0.0.", "Son ishorasi: 1.0, −1.0 yoki 0.0.", "sign(-12)"),
    "sin": ("Синус угла x (по умолчанию x в радианах).", "x burchakning sinusi (standart holda x radianda).", "sin(pi / 2)"),
    "sinh": ("Гиперболический синус.", "Giperbolik sinus.", "sinh(0)"),
    "sqrt": ("Квадратный корень (x ≥ 0).", "Kvadrat ildiz (x ≥ 0).", "sqrt(16)"),
    "tan": ("Тангенс угла x (по умолчанию x в радианах).", "x burchakning tangensi (standart holda x radianda).", "tan(0)"),
    "tanh": ("Гиперболический тангенс.", "Giperbolik tangens.", "tanh(0)"),
    # ── aralash ──
    "calculate": ("Вычисляет выражение, записанное строкой (вложенность не глубже 4).",
                  "Satr ko'rinishida yozilgan ifodani hisoblaydi (ichma-ichlik 4 dan oshmaydi).", "calculate('2 + 3 * 4')"),
    "if": ("Выбор по условию: условие истинно — второй аргумент, иначе третий. Вычисляется только выбранная ветвь.",
           "Shart bo'yicha tanlash: shart rost bo'lsa — ikkinchi argument, aks holda uchinchi. Faqat tanlangan tarmoq hisoblanadi.",
           "if(5 > 3, 'A', 'B')"),
    "format": ("Число в текст по образцу: 0 — обязательная цифра, # — необязательная, . — десятичный разделитель, , — разделитель групп, "
               "% — умножить на 100, ; — отдельный образец для отрицательных.",
               "Sonni namuna bo'yicha matnga aylantiradi: 0 — majburiy raqam, # — ixtiyoriy, . — kasr ajratgichi, , — guruh ajratgichi, "
               "% — 100 ga ko'paytirish, ; — manfiylar uchun alohida namuna.", "format('0.00', 3.14159)"),
    "now": ("Текущие дата и время по образцу: yyyy — год, MM — месяц, dd — день, HH — часы, mm — минуты, ss — секунды, "
            "MMMM — название месяца на языке интерфейса.",
            "Joriy sana va vaqt namuna bo'yicha: yyyy — yil, MM — oy, dd — kun, HH — soat, mm — daqiqa, ss — soniya, "
            "MMMM — oy nomi (interfeys tilida).", "now('yyyy.MM.dd')"),
    "uuid": ("Случайный идентификатор (36 символов); каждый вызов даёт новый.",
             "Tasodifiy identifikator (36 belgi); har chaqiruvda yangi.", "UUID()"),
    # ── matn ──
    "len": ("Длина строки (число символов).", "Satr uzunligi (belgilar soni).", "len('kroy')"),
    "mid": ("Часть строки: mid(s, начало, длина). Позиции считаются с 1.", "Satrning bir qismi: mid(s, boshi, uzunlik). Pozitsiya 1 dan sanaladi.",
            "mid('abcdef', 2, 3)"),
    "left": ("Первые n символов строки.", "Satrning birinchi n belgisi.", "left('abcdef', 2)"),
    "right": ("Последние n символов строки (число тоже принимается как текст).", "Satrning oxirgi n belgisi (son ham matn sifatida qabul qilinadi).",
              "right('abcdef', 2)"),
    "lspace": ("Дополняет строку справа заданным символом до длины n; текст остаётся слева (слишком длинная строка обрезается).",
               "Satrni o'ngdan berilgan belgi bilan n uzunlikkacha to'ldiradi; matn chapda qoladi (uzun satr qirqiladi).", "lspace('ab', 5, '0')"),
    "rspace": ("Дополняет строку слева заданным символом до длины n; текст прижат вправо (слишком длинная строка обрезается слева).",
               "Satrni chapdan berilgan belgi bilan n uzunlikkacha to'ldiradi; matn o'ngga siqiladi (uzun satr chapdan qirqiladi).", "rspace('ab', 5, '0')"),
    "rept": ("Повторяет строку n раз.", "Satrni n marta takrorlaydi.", "rept('ab', 3)"),
    "ns": ("Строка без null: пустое значение (null) → пустая строка, иначе значение как текст.",
           "null siz satr: bo'sh qiymat (null) → bo'sh satr, aks holda qiymat matn sifatida.", "ns(null)"),
    "empty": ("Истина, если значение пустое (null или пустая строка).", "Qiymat bo'sh (null yoki bo'sh satr) bo'lsa — rost.", "empty('')"),
    "trim": ("Убирает пробелы с обоих концов строки.", "Satrning ikki chetidagi bo'shliqlarni olib tashlaydi.", "trim('  a b  ')"),
    "ltrim": ("Убирает пробелы слева.", "Chapdagi bo'shliqlarni olib tashlaydi.", "ltrim('  ab')"),
    "rtrim": ("Убирает пробелы справа.", "O'ngdagi bo'shliqlarni olib tashlaydi.", "rtrim('ab  ')"),
    "ucase": ("Переводит строку в верхний регистр.", "Satrni bosh harflarga o'tkazadi.", "ucase('Abc')"),
    "lcase": ("Переводит строку в нижний регистр.", "Satrni kichik harflarga o'tkazadi.", "lcase('Abc')"),
    "find": ("Позиция первого вхождения подстроки (с 1), поиск от позиции start; не найдено — 0. Регистр важен.",
             "Qism satrning birinchi uchrashgan o'rni (1 dan), start dan boshlab qidiriladi; topilmasa — 0. Harf registri muhim.",
             "find('abcabc', 'ca')"),
    "findr": ("Позиция последнего вхождения подстроки (поиск справа налево); не найдено — 0.",
              "Qism satrning oxirgi uchrashgan o'rni (o'ngdan chapga qidiriladi); topilmasa — 0.", "findr('abcabc', 'bc')"),
    "replace": ("Заменяет все вхождения подстроки на другую: replace(s, старое, новое).",
                "Qism satrning barcha uchrashishlarini boshqasiga almashtiradi: replace(s, eski, yangi).", "replace('1-2-3', '-', '/')"),
    "startswith": ("Истина, если строка начинается с указанного текста.", "Satr ko'rsatilgan matn bilan boshlansa — rost.",
                   "startswith('Shkaf-1', 'Sh')"),
    "endswith": ("Истина, если строка заканчивается указанным текстом.", "Satr ko'rsatilgan matn bilan tugasa — rost.", "endswith('Shkaf-1', '-1')"),
    "double": ("Строку или число → дробное число (запятая как десятичный разделитель допустима).",
               "Satr yoki sonni kasr songa aylantiradi (kasr ajratgichi sifatida vergul ham mumkin).", "double('2,5')"),
    "integer": ("Строку или число → целое (дробная часть отбрасывается).", "Satr yoki sonni butunga aylantiradi (kasr qismi tashlanadi).",
                "integer('42.9')"),
    "boolean": ("Строку → логическое значение: «true», «t», «1» (регистр не важен) — истина, всё остальное — ложь.",
                "Satrni mantiqiy qiymatga aylantiradi: «true», «t», «1» (registr muhim emas) — rost, qolgani — yolg'on.", "boolean('T')"),
    "translit": ("Переводит кириллицу в латиницу.", "Kirill harflarini lotinga o'tkazadi.", "translit('Шкаф')"),
    "crc16": ("Контрольная сумма CRC-16 (вариант ARC) строки в UTF-8: число 0–65535 (удобно для кодов в штрихкоде).",
              "Satrning (UTF-8) CRC-16 (ARC varianti) nazorat yig'indisi: 0–65535 oralig'idagi son (shtrixkod kodlari uchun qulay).", "crc16('test')"),
    "crc32": ("Контрольная сумма CRC-32 строки; знаковое 32-битное целое.", "Satrning CRC-32 nazorat yig'indisi; ishorali 32 bitli butun son.",
              "crc32('test')"),
    # ── sonli o'zgartirishlar ──
    "dectohex": ("Целое → строка в шестнадцатеричной записи.", "Butun sonni o'n oltilik yozuvdagi satrga aylantiradi.", "DecToHex(255)"),
    "hextodec": ("Строка в шестнадцатеричной записи → целое.", "O'n oltilik yozuvdagi satrni butun songa aylantiradi.", "HexToDec('ff')"),
    "dectooct": ("Целое → строка в восьмеричной записи.", "Butun sonni sakkizlik yozuvdagi satrga aylantiradi.", "DecToOct(8)"),
    "octtodec": ("Строка в восьмеричной записи → целое.", "Sakkizlik yozuvdagi satrni butun songa aylantiradi.", "OctToDec('17')"),
    "dectobin": ("Целое → строка в двоичной записи.", "Butun sonni ikkilik yozuvdagi satrga aylantiradi.", "DecToBin(5)"),
    "bintodec": ("Строка в двоичной записи → целое.", "Ikkilik yozuvdagi satrni butun songa aylantiradi.", "BinToDec('101')"),
    "roman": ("Целое от 1 до 3999 → римская запись.", "1 dan 3999 gacha butun son → rim raqami.", "roman(2026)"),
}

# tasodifiy / vaqtga bog'liq funksiyalar: natija o'rniga tavsif
DYNAMIC: dict[str, str] = {
    "random": "0.0 … 1.0",
    "uuid": "xxxxxxxx-xxxx-4xxx-xxxx-xxxxxxxxxxxx",
    "now": "",                      # joriy sana (dvigatel soatidan)
}

# (nom, ru, uz, misol)
CONSTANTS: list[tuple[str, str, str, str]] = [
    ("pi", "Число π (3.14159…).", "π soni (3.14159…).", "pi"),
    ("e", "Число e — основание натуральных логарифмов (2.71828…).", "e soni — natural logarifm asosi (2.71828…).", "e"),
    ("true", "Логическая истина.", "Mantiqiy rost.", "true"),
    ("false", "Логическая ложь.", "Mantiqiy yolg'on.", "false"),
    ("null", "Пустое значение (нет значения).", "Bo'sh qiymat (qiymat yo'q).", "null"),
]

# (operator, ru, uz, misol)
OPERATORS: list[tuple[str, str, str, str]] = [
    ("+  −  *  /", "Четыре действия. Целое ÷ целое = целое (7 / 2 = 3); если есть дробное — результат дробный.",
     "To'rt amal. Butun ÷ butun = butun (7 / 2 = 3); kasr qatnashsa — natija kasr.", "7 / 2"),
    ("%", "Остаток от деления (знак — как у делимого).", "Bo'lishdan qoldiq (ishorasi bo'linuvchi kabi).", "7 % 3"),
    ("^", "Возведение в степень (справа налево, сильнее унарного минуса: −2^2 = −4).",
     "Darajaga ko'tarish (o'ngdan chapga, unar minusdan kuchli: −2^2 = −4).", "2 ^ 10"),
    ("<  >  <=  >=", "Сравнение; результат логический.", "Taqqoslash; natija mantiqiy.", "3 <= 5"),
    ("=  ==  <>  !=", "Равно / не равно (допускаются обе записи).", "Teng / teng emas (ikkala yozuv ham mumkin).", "1 <> 2"),
    ("not  and  xor  or", "Логические операции (приоритет по убыванию: not, and, xor, or).",
     "Mantiqiy amallar (ustuvorlik kamayish tartibida: not, and, xor, or).", "not (1 > 2) and true"),
    ("'текст'", "Строка в одинарных (или двойных) кавычках; + — склеивание: 'x' + 1 = 'x1'. Escape: \\n \\t \\' \\\\ \\uXXXX.",
     "Bitta (yoki ikkita) qo'shtirnoqdagi satr; + — birlashtirish: 'x' + 1 = 'x1'. Escape: \\n \\t \\' \\\\ \\uXXXX.", "'N' + (1 + 2)"),
]

@lru_cache(maxsize=None)
def _compute(example: str, lang: str) -> tuple[str, str]:
    """Misol natijasi: (matn, tur). Xato bo'lsa — ('', 'error')."""
    try:
        v = E.evaluate(example, {}, rng=_random.Random(1), lang=lang)
    except ValueError:
        return "", "error"
    return E.to_text(v), type_name(v)


def type_name(v) -> str:
    """Qiymat turi nomi (yordamdagi nomlar): integer | double | boolean | string | null."""
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "boolean"
    if isinstance(v, int):
        return "integer"
    if isinstance(v, float):
        return "double"
    return "string"


def example_result(name: str, example: str, lang: str = "ru") -> tuple[str, str]:
    """(natija matni, turi). Dinamik funksiyalar uchun — tavsifiy matn."""
    if name in DYNAMIC:
        if name == "now":
            return E.evaluate(example, {}, clock=lambda: _dt.datetime.now(), lang=lang), "string"
        return DYNAMIC[name], "string" if name == "uuid" else "double"
    return _compute(example, lang)


def function_rows(lang: str = "ru") -> list[dict]:
    """Yassi ro'yxat: guruh, nom, imzo, ru/uz tavsif, misol va uning natijasi (jonli hisoblangan)."""
    rows: list[dict] = []
    for g in GROUP_ORDER:
        for name, sig in E.FUNCTION_GROUPS.get(g, []):
            ru, uz, ex = DOCS[name]
            res, rtype = example_result(name, ex, lang)
            rows.append(dict(group=g, name=name, signature=sig, description_ru=ru, description_uz=uz,
                             description=uz if lang == "uz" else ru, example=ex, example_result=res, example_type=rtype,
                             pure=name not in E._IMPURE))
    return rows


def group_rows() -> list[dict]:
    return [dict(key=g, title_ru=GROUP_TITLES[g][0], title_uz=GROUP_TITLES[g][1],
                 count=len(E.FUNCTION_GROUPS.get(g, []))) for g in GROUP_ORDER]


def constant_rows(lang: str = "ru") -> list[dict]:
    out = []
    for name, ru, uz, ex in CONSTANTS:
        res, rtype = _compute(ex, lang)
        out.append(dict(name=name, description_ru=ru, description_uz=uz, description=uz if lang == "uz" else ru,
                        example=ex, example_result=res, example_type=rtype))
    return out


def operator_rows(lang: str = "ru") -> list[dict]:
    out = []
    for op, ru, uz, ex in OPERATORS:
        res, rtype = _compute(ex, lang)
        out.append(dict(operator=op, description_ru=ru, description_uz=uz, description=uz if lang == "uz" else ru,
                        example=ex, example_result=res, example_type=rtype))
    return out
