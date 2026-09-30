"""Backend xabarlari tarjimasi (ru / uz). Til — so'rovning `Accept-Language` sarlavhasidan (frontend yuboradi).

Foydalanish:  from .i18n import _ ;  raise HTTPException(404, _("project_not_found"))
"""
from __future__ import annotations

from contextvars import ContextVar

LANG: ContextVar[str] = ContextVar("mebelix_lang", default="ru")

MSG: dict[str, tuple[str, str]] = {
    # umumiy
    "project_not_found": ("Проект не найден", "Loyiha topilmadi"),
    "op_not_found": ("Операция не найдена", "Operatsiya topilmadi"),
    "part_not_found": ("Деталь не найдена", "Detal topilmadi"),
    "folder_not_found": ("Папка не найдена", "Papka topilmadi"),
    "folder_into_itself": ("Нельзя переместить папку внутрь самой себя", "Papkani o'z ichiga ko'chirib bo'lmaydi"),
    "folder_not_empty": ("Папка не пуста", "Papka bo'sh emas"),
    "product_not_found": ("Изделие не найдено", "Mahsulot topilmadi"),
    "cs_only": ("Только для операции листового раскроя (CS)", "Faqat CS (listli kroy) operatsiyasi uchun"),
    "no_parts": ("Нет деталей", "Detallar yo'q"),
    "no_sheets": ("Нет листов", "Listlar yo'q"),
    "no_parts_or_sheets": ("Нет деталей или листов", "Detallar yoki listlar yo'q"),
    "no_map": ("Карта не найдена", "Karta topilmadi"),
    "not_xnc": ("Это не операция XNC", "Bu XNC operatsiyasi emas"),
    "cut_first": ("Сначала выполните «Раскроить»", "Avval «Раскроить» ni bajaring"),
    "pp_not_found": ("Постпроцессор не найден", "Postprotsessor topilmadi"),
    "pp_not_selected": ("Постпроцессор не выбран", "Postprotsessor tanlanmagan"),
    "template_error": ("Ошибка шаблона: {e}", "Shablon xatosi: {e}"),
    "template_limit": ("Шаблон превысил ограничение (время / объём / циклы): {e}",
                       "Shablon chegaradan chiqdi (vaqt / hajm / sikllar): {e}"),
    "no_weasyprint": ("Для PDF на сервере не установлен weasyprint — используйте «Печать → Сохранить как PDF» в браузере",
                      "Serverda PDF uchun weasyprint o'rnatilmagan — brauzerda «Chop etish → PDF» dan foydalaning"),
    "catalog_item_not_found": ("Товар не найден", "Tovar topilmadi"),
    "import_error": ("Ошибка импорта: {e}", "Import xatosi: {e}"),
    "file_unreadable": ("Не удалось прочитать файл: {e}", "Fayl o'qilmadi: {e}"),
    "bad_project_file": ("Неверный формат файла (нужен .mxk.json или поддерживаемый импорт): {e}",
                         "Fayl formati noto'g'ri (.mxk.json yoki qo'llab-quvvatlanadigan import): {e}"),
    "move_to_cut_only": ("Детали можно перенести только в операцию раскроя", "Detallarni faqat kroy operatsiyasiga ko'chirish mumkin"),
    "sort_fields": ("Поле сортировки: {f}", "Saralash maydoni: {f}"),
    "cannot_undo": ("Нечего отменять", "Bekor qiladigan amal yo'q"),
    "cannot_redo": ("Нечего возвращать", "Qaytaradigan amal yo'q"),
    "no_result": ("Нет результата раскроя", "Kroy natijasi yo'q"),
    "remnants_already": ("Остатки уже записаны на склад", "Qoldiqlar allaqachon omborga yozilgan"),
    "remnant_not_found": ("Остаток не найден", "Qoldiq topilmadi"),
    "default_project": ("Без названия", "Nomsiz"),
    "default_folder": ("Папка", "Papka"),
    "default_product": ("Изделие 1", "Mahsulot 1"),
    "copy_suffix": (" (копия)", " (nusxa)"),
    "remnant_sheet": ("остаток №{id}", "qoldiq №{id}"),
    "remnant_word": ("остаток", "qoldiq"),
    "unit_sheets": ("Листы", "List"),
    "unit_pcs": ("шт", "dona"),
    "unit_m": ("м", "m"),
    "note_cut": ("Длина реза: {m} м", "Kesish uzunligi: {m} m"),
    "note_edge": ("Кромкование (работа): {m} м", "Kromkalash (ish): {m} m"),
    "set_unknown_scope": ("Неизвестный тип настроек: {s}", "Noma'lum sozlama turi: {s}"),
    "set_json_object": ("Ожидается JSON-объект", "JSON obyekt kutilgan"),
    "set_invalid": ("Неверные настройки: {e}", "Sozlamalar noto'g'ri: {e}"),
    "remnant_short": ("На складе не хватает остатков: {items}. Обновите «Листы и остатки» и раскроите заново",
                      "Omborda qoldiq yetarli emas: {items}. «Листы и остатки» ni yangilab, qayta kroy qiling"),
    "remnant_short_item": ("№{id} — нужно {need}, есть {have}", "№{id} — kerak {need}, bor {have}"),
    "remnant_positive": ("Размеры и количество должны быть положительными", "O'lcham va soni musbat bo'lishi kerak"),
    "unknown_scope": ("Неизвестный тип настроек: {s}", "Noma'lum sozlama turi: {s}"),
    "profile_not_found": ("Профиль не найден", "Profil topilmadi"),
    "pp_sample": ("Для примера выберите операцию CS с выполненным раскроем", "Namuna uchun kroy qilingan CS operatsiyasini tanlang"),
    "order_approved": ("Заказ {ref} уже утверждён (проект №{n})", "Buyurtma {ref} allaqachon tasdiqlangan (loyiha №{n})"),
    "order_not_found": ("Заказ не найден", "Buyurtma topilmadi"),
    "qr_bad": ("QR-код не в формате MebeliX", "QR kod MebeliX formatida emas"),
    "project_no_n": ("Проект №{n} не найден", "Loyiha №{n} topilmadi"),
    "part_uid_not_found": ("Деталь {uid} не найдена", "Detal {uid} topilmadi"),
    "scan_map_needed": ("Это этикетка детали — отсканируйте QR карты кроя", "Bu detal etiketkasi — karta QR kodini skanerlang"),
    "webhook_no_url": ("MES_WEBHOOK_URL не задан", "MES_WEBHOOK_URL o'rnatilmagan"),
    "jwt_no_key": ("Не настроен ключ JWT (MEBELIX_JWT_SECRET или MEBELIX_JWT_PUBLIC_KEY)",
                   "JWT kaliti sozlanmagan (MEBELIX_JWT_SECRET yoki MEBELIX_JWT_PUBLIC_KEY)"),
    "jwt_bad": ("Недействительный токен: {e}", "Token yaroqsiz: {e}"),
    "auth_required": ("Требуется авторизация (Authorization: Bearer <token>)", "Avtorizatsiya talab qilinadi (Authorization: Bearer <token>)"),
    "import_not_xml": ("Файл не прочитан (не XML или повреждён): {e}", "Fayl o'qilmadi (XML emas yoki buzilgan): {e}"),
    "import_not_project": ("Это не файл проекта .project", "Bu .project loyiha fayli emas"),
    "imp_part_dup": ("Деталь {id} есть в нескольких операциях раскроя — сделана копия", "Detal {id} bir nechta kroy operatsiyasida — nusxa olindi"),
    "imp_edge_missing": ("Деталь {id}: кромка {ref} не найдена", "Detal {id}: kromka {ref} topilmadi"),
    "imp_parts_skipped": ("{n} дет. не входят ни в одну операцию раскроя (не импортированы)", "{n} ta detal hech bir kroy operatsiyasiga kirmagan (import qilinmadi)"),
    "imp_ops_skipped": ("Пропущено операций другого типа: {n}", "{n} ta boshqa turdagi operatsiya o'tkazib yuborildi"),
    "imp_desc": ("Импорт: прежний раскрой — {n} лист(ов)", "Import: oldingi kroy — {n} list"),
    # tahrir (редактор раскроя)
    "ed.bad_axis": ("Неверная ось узла дерева", "Daraxt tuguni o'qi noto'g'ri"),
    "ed.part_missing": ("Детали {uid} нет в этой операции", "Detal {uid} bu operatsiyada yo'q"),
    "ed.bad_kind": ("Неизвестный тип узла: {k}", "Noma'lum tugun turi: {k}"),
    "ed.node_missing": ("Элемент не найден (карта могла измениться)", "Tanlangan element topilmadi (karta o'zgargan bo'lishi mumkin)"),
    "ed.place_on_waste": ("Деталь можно поставить только на свободное место", "Detalni faqat bo'sh (chiqindi) joyga qo'yish mumkin"),
    "ed.grain_no_rotate": ("Деталь {uid}: текстура — поворот запрещён", "Detal {uid}: tekstura — aylantirish mumkin emas"),
    "ed.no_fit": ("Деталь {uid} ({size}) не помещается в это место ({free})", "Detal {uid} ({size}) bu joyga sig'maydi ({free})"),
    "ed.no_fit_any": ("Деталь {uid} не помещается ни в одно свободное место карты", "Detal {uid} kartadagi hech bir bo'sh joyga sig'maydi"),
    "ed.root_move": ("Корень нельзя переместить", "Ildizni ko'chirib bo'lmaydi"),
    "ed.waste_move": ("Свободное место нельзя переместить — выберите деталь или полосу", "Bo'sh joyni ko'chirib bo'lmaydi — detal yoki polosani tanlang"),
    "ed.bad_dir": ("Неизвестное направление: {d}", "Noma'lum yo'nalish: {d}"),
    "ed.clone_select": ("Для клонирования выберите деталь или полосу", "Nusxalash uchun detal yoki polosani tanlang"),
    "ed.clone_space": ("В этой полосе нет места для копии", "Bu polosada nusxa uchun bo'sh joy yetarli emas"),
    "ed.expand_select": ("Для расширения выберите полосу", "Kengaytirish uchun polosani tanlang"),
    "ed.expand_space": ("После полосы нет свободного места", "Polosadan keyin bo'sh joy yo'q"),
    "ed.rotate_select": ("Выберите полосу или область", "Qayta kesish uchun polosa yoki hududni tanlang"),
    "ed.rotate_empty": ("В области нет деталей", "Hududda detal yo'q"),
    "ed.rotate_fail": ("В другом направлении детали в эту область не помещаются", "Detallar boshqa yo'nalishda bu hududga sig'madi"),
    "ed.sheet_missing": ("Карта {map}: лист не найден", "Karta {map}: list topilmadi"),
    "ed.no_tree": ("Карта {map}: нет дерева резов — редактирование невозможно", "Karta {map}: kesish daraxti yo'q — tahrirlab bo'lmaydi"),
    "ed.tree_empty": ("Карта {map}: пустое дерево", "Karta {map}: daraxt bo'sh"),
    "ed.too_deep": ("Карта {map}: уровней резов {d} > «Макс. количество вращений» {m}", "Karta {map}: kesish darajalari {d} > «Макс. количество вращений» {m}"),
    "ed.too_many": ("Деталь {uid}: на картах {n} шт, нужно {need} шт", "Detal {uid}: kartalarda {n} ta, kerak {need} ta"),
    "ed.sheets_exceeded": ("Лист {size}: использовано {n}, в наличии {q}", "List {size}: {n} ta ishlatildi, omborda {q} ta"),
    "ed.no_sheet": ("Лист не выбран", "List tanlanmagan"),
    "ed.sheet_small": ("Лист слишком мал после торцовки", "List torsovkadan keyin juda kichik"),
    "ed.no_map": ("Карта не выбрана", "Karta tanlanmagan"),
    "ed.none_left": ("Деталь {uid}: не осталось для размещения (карта в {c} экз.)", "Detal {uid}: joylashtirish uchun qolmagan (karta {c} nusxada)"),
    "ed.clone_parts": ("Деталь {uid}: не хватает для копии (осталось {n})", "Detal {uid}: nusxa uchun yetarli emas (qolgan {n})"),
    "ed.bad_action": ("Неизвестное действие: {a}", "Noma'lum amal: {a}"),
    "ed.map_empty": ("Карта осталась пустой", "Karta bo'sh bo'lib qoldi"),
    # tekshiruv (validate)
    "v.unknown_sheet": ("Карта {map}: неизвестный лист {id}", "Karta {map}: noma'lum list {id}"),
    "v.outside": ("Карта {map}: деталь {uid} за пределами листа", "Karta {map}: detal {uid} list tashqarisida"),
    "v.bad_size": ("Карта {map}: деталь {uid} — неверный размер/поворот ({l}×{w})", "Karta {map}: detal {uid} o'lchami/aylanishi noto'g'ri ({l}×{w})"),
    "v.overlap": ("Карта {map}: детали {a} и {b} наложены или без пропила", "Karta {map}: detallar {a} va {b} ustma-ust yoki propilsiz"),
    "v.tree_cross": ("Карта {map}: узел ({x},{y}) — дочерний элемент не совпадает по поперечному размеру", "Karta {map}: tugun ({x},{y}) bolasi ko'ndalang o'lchamda mos emas"),
    "v.tree_overlap": ("Карта {map}: узел ({x},{y}) — элементы наложены (без пропила)", "Karta {map}: tugun ({x},{y}) bolalari ustma-ust (propilsiz)"),
    "v.tree_out": ("Карта {map}: узел ({x},{y}) — элемент выходит за границу", "Karta {map}: tugun ({x},{y}) bolasi chegaradan chiqqan"),
    "v.trim": ("Карта {map}: обрезок {r} мм меньше минимальной обрезки {mt} мм (узел {x},{y})", "Karta {map}: {r} mm qirindi < minimal qirqim {mt} mm (tugun {x},{y})"),
    "v.tree_count": ("Карта {map}: деталей в дереве {a} ≠ размещений {b}", "Karta {map}: daraxtdagi detallar {a} ≠ joylashuvlar {b}"),
    "v.count": ("Количество деталей не совпадает: {d}", "Detallar soni mos emas: {d}"),
}


def _(key: str, **kw) -> str:
    pair = MSG.get(key)
    if pair is None:
        return key.format(**kw) if kw else key
    text = pair[1] if LANG.get() == "uz" else pair[0]
    try:
        return text.format(**kw)
    except (KeyError, IndexError, ValueError):
        return text


def set_lang(header: str | None) -> None:
    v = (header or "").strip().lower()[:2]
    LANG.set("uz" if v == "uz" else "ru")
