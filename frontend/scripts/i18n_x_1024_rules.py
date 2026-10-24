# -*- coding: utf-8 -*-
"""2026-10-24 — «Правила остатков»: bazaga yuborish (foiz) va bazadan topib qo'shish qoidalari, ombor holati / jurnali,
CS «Использовать остатки со склада». `a(kalit, ru, uz)` — i18n_src.py ichida."""

a("settings.page.remnant_rules", "Правила остатков", "Qoldiq qoidalari")
a("rr.source", "Источник склада", "Ombor manbasi")
a("rr.source_mes", "База MES (основной склад)", "MES bazasi (asosiy ombor)")
a("rr.source_local", "Локальный склад MebeliX (пока API MES не подключён)", "MebeliX lokal ombori (MES API ulanmaguncha)")
a("rr.mes_url", "Адрес API склада MES", "MES ombori API manzili")
a("rr.source_mes_hint", "Все данные склада хранятся в MES: поиск и резерв остатков, приход после раскроя и продажа клиенту идут в базу MES. Статус «вышел из пилы», история и цены ведёт MES.",
  "Ombor ma'lumotlari MES da: qoldiqni qidirish va band qilish, kroydan keyingi kirim va mijozga sotish MES bazasiga yuboriladi. «Arradan chiqdi» holati, tarix va narxlarni MES yuritadi.")
a("rr.source_local_hint", "Склад ведётся в MebeliX (как сейчас). После подключения MES выберите «База MES» и укажите адрес.",
  "Ombor MebeliX da yuritiladi (hozirgidek). MES ulangach «MES bazasi» ni tanlab, manzilni yozing.")
a("rr.send", "Отправка остатков в базу", "Qoldiqni bazaga yuborish")
a("rr.send_hint", "Остаток после раскроя ≥ указанного % от площади целого листа — предприятие оставляет его себе (на склад), меньше — отдаётся клиенту. Решает только %. Правило материала важнее правила типа.",
  "Kroydan keyingi qoldiq butun list maydonining ko'rsatilgan foizidan katta yoki teng bo'lsa — korxona olib qoladi (omborga), kichigi — mijozga beriladi. Faqat foiz hal qiladi. Material qoidasi tur qoidasidan ustun.")
a("rr.type", "Тип материала", "Material turi")
a("rr.keep_pct", "Оставлять от", "Olib qolish chegarasi")
a("rr.threshold", "≈ м² (лист {{a}} м²)", "≈ m² (list {{a}} m²)")
a("rr.in_stock", "На складе, шт", "Omborda, dona")
a("rr.pending", "Ждут пилу", "Arrani kutmoqda")
a("rr.total_pct", "Всего, % листа", "Jami, list %")
a("rr.no_rule", "нет правила", "qoida yo'q")
a("rr.type_new", "Новый тип", "Yangi tur")
a("rr.materials", "Отдельные материалы", "Alohida materiallar")
a("rr.materials_hint", "Если для конкретного материала нужен свой %, добавьте его (название как в проекте; регистр и пробелы не важны).",
  "Aniq material uchun boshqa foiz kerak bo'lsa — qo'shing (nomi loyihadagidek; katta-kichik harf va bo'shliq ahamiyatsiz).")
a("rr.material_new", "Название материала", "Material nomi")
a("rr.auto_commit", "После раскроя записывать остатки в базу автоматически (без подтверждения)", "Kroydan keyin qoldiqlarni bazaga avtomatik yozish (tasdiqsiz)")
a("rr.wait_mes", "Остаток доступен только после выхода листа из пилы (сигнал MES)", "Qoldiq faqat list arradan chiqqach mavjud bo'ladi (MES signali)")
a("rr.wait_mes_off", "Сейчас интеграция MES выключена — остатки доступны сразу.", "Hozir MES integratsiyasi o'chiq — qoldiqlar darhol mavjud.")
a("rr.find", "Поиск остатков в базе", "Bazadan qoldiq topish")
a("rr.find_hint", "При отметке «Использовать остатки со склада» после раскроя ищется остаток того же материала и толщины, который уменьшает расход (детали последних листов помещаются в него). Нашёлся — окно с предложением, нет — «на складе нет подходящего остатка».",
  "«Ombor qoldig'idan foydalanish» belgisi qo'yilsa, kroydan keyin shu material va qalinlikdagi, sarfni kamaytiradigan (oxirgi listlar detallari sig'adigan) qoldiq qidiriladi. Topilsa — taklif oynasi, topilmasa — «omborda mos qoldiq yo'q».")
a("rr.use_default", "Для новых операций отметка «Использовать остатки со склада» включена", "Yangi operatsiyalarda «Ombor qoldig'idan foydalanish» yoqilgan bo'lsin")
a("rr.find_limit", "Сколько остатков проверять (самые маленькие)", "Nechta qoldiq tekshiriladi (eng kichiklari)")
a("rr.find_seconds", "Время поиска", "Qidiruv vaqti")
a("rr.sec", "с", "s")
a("rr.sale_hint", "Продажа клиенту: остаток продаётся целиком и списывается из базы, цена = м² остатка / м² листа × цена листа.",
  "Mijozga sotish: qoldiq butunligicha sotiladi va bazadan chiqariladi, narx = qoldiq m² / list m² × list narxi.")
a("rr.stock", "Остатки на складе по материалам", "Ombordagi qoldiqlar (material bo'yicha)")

a("rem.status", "Статус", "Holat")
a("rem.st.available", "Доступен", "Mavjud")
a("rem.st.reserved", "В резерве", "Band")
a("rem.st.pending", "Ждёт пилу", "Arrani kutmoqda")
a("rem.st.empty", "Израсходован", "Tugagan")
a("rem.pending", "Ждут пилу", "Kutmoqda")
a("rem.pending_total", "ждут пилу: {{n}}", "arrani kutmoqda: {{n}}")
a("rem.history", "История", "Tarix")
a("rem.move", "Движение", "Harakat")
a("rem.mv.kutish", "Оставлен (ждёт пилу)", "Olib qolindi (arrani kutmoqda)")
a("rem.mv.kirim", "Приход", "Kirim")
a("rem.mv.chiqim", "Продан в заказ", "Buyurtmaga sotildi")
a("rem.mv.qaytish", "Возврат", "Qaytarildi")
a("rem.mv.bekor", "Приход отменён", "Kirim bekor qilindi")
a("rem.mv.rezerv", "Резерв", "Band qilindi")
a("rem.mv.rezerv_bekor", "Резерв снят", "Band bekor qilindi")
a("rem.mv.mijozga", "Отдан клиенту", "Mijozga berildi")
a("rem.mv.qolda", "Вручную", "Qo'lda")
a("rem.external_hint", "Склад ведётся в базе MES — здесь только просмотр. Правила: «Настройки → Правила остатков».",
  "Ombor MES bazasida yuritiladi — bu yerda faqat ko'rish. Qoidalar: «Sozlamalar → Qoldiq qoidalari».")
a("rem.sheet", "Целый лист", "Butun list")
a("rem.calc", "Остаток {{a}} м² = {{p}} % листа ({{s}} м²)", "Qoldiq {{a}} m² = list {{p}} % ({{s}} m²)")
a("rem.commit_text_mes", "Остатки материала «{{code}}» будут отправлены в базу MES (использованные остатки — как проданные).",
  "«{{code}}» materiali qoldiqlari MES bazasiga yuboriladi (ishlatilgan qoldiqlar — sotilgan sifatida).")
a("rem.rule_line", "Правило: остаток ≥ {{p}} % листа — на склад, меньше — клиенту", "Qoida: qoldiq ≥ list {{p}} % — omborga, kichigi — mijozga")
a("rem.client_line", "Клиенту", "Mijozga")
a("rem.pending_note", "Остатки станут доступны после выхода листа из пилы (сигнал MES).", "Qoldiqlar list arradan chiqqach mavjud bo'ladi (MES signali).")

a("cs.p.use_warehouse", "Использовать остатки со склада", "Ombor qoldig'idan foydalanish")
a("cs.p.use_warehouse_hint", "После раскроя искать в базе остаток, в который помещаются детали последних листов (уменьшает расход). Нет — сообщение «на складе нет подходящего остатка».",
  "Kroydan keyin bazadan oxirgi listlar detallari sig'adigan (sarfni kamaytiradigan) qoldiq qidiriladi. Yo'q bo'lsa — «omborda mos qoldiq yo'q» xabari.")
a("ro.empty", "На складе нет подходящего остатка этого материала", "Omborda bu materialdan mos qoldiq yo'q")
a("ro.price", "Цена клиенту", "Mijozga narxi")
a("ro.sale_hint", "Остаток продаётся клиенту целиком: цена = м² остатка / м² листа × цена листа.",
  "Qoldiq mijozga butunligicha sotiladi: narx = qoldiq m² / list m² × list narxi.")
