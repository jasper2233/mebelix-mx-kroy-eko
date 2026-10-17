# -*- coding: utf-8 -*-
"""2026-10-17 · xabarlar auditi: dastur xatosi qatori, server xatolari (422 / tarmoq), xabar oynalari (i18n_src.py yuklaydi)."""

a("xnc.err_inside", "Внутри блока есть ошибка", "Blok ichida xato bor")
a("app.more_n", "… и ещё {{n}}", "… yana {{n}} ta")
a("err.unknown", "Неизвестная ошибка", "Noma'lum xato")
# server xatolari (javobda matn bo'lmasa) — holat kodi bo'yicha
a("err.http.network", "Нет связи с сервером. Проверьте, что программа запущена, и повторите.",
  "Server bilan aloqa yo'q. Dastur ishga tushirilganini tekshirib, qayta urinib ko'ring.")
a("err.http.401", "Требуется вход в систему", "Tizimga kirish kerak")
a("err.http.403", "Недостаточно прав для этого действия", "Bu amal uchun huquq yetarli emas")
a("err.http.404", "Не найдено (возможно, удалено другим пользователем)", "Topilmadi (boshqa foydalanuvchi o'chirgan bo'lishi mumkin)")
a("err.http.409", "Конфликт: данные изменились, обновите и повторите", "Ziddiyat: ma'lumot o'zgargan, yangilab qayta urinib ko'ring")
a("err.http.413", "Файл или данные слишком большие", "Fayl yoki ma'lumot juda katta")
a("err.http.422", "Неверные данные", "Ma'lumot noto'g'ri")
a("err.http.429", "Слишком много запросов, подождите немного", "So'rovlar juda ko'p, biroz kuting")
a("err.http.5xx", "Ошибка сервера ({{status}}). Повторите позже.", "Server xatosi ({{status}}). Keyinroq qayta urinib ko'ring.")
a("err.http.other", "Ошибка запроса ({{status}})", "So'rov xatosi ({{status}})")
a("projects.not_found", "Проект не найден (возможно, удалён) — открыт список проектов",
  "Loyiha topilmadi (o'chirilgan bo'lishi mumkin) — loyihalar ro'yxati ochildi")
