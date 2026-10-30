# -*- coding: utf-8 -*-
"""2026-10-30 — «Раскроечные станки»: stanok standarti (pila, торцовка, вращения …) faqat parol bilan o'zgaradi; operator
o'zgarishi faqat o'sha loyihada. `a(kalit, ru, uz)` — i18n_src.py ichida."""

a("settings.page.saw_machines", "Раскроечные станки", "Kesish stanoklari")
a("saw.machine", "Станок", "Stanok")
a("saw.main", "Основной станок", "Asosiy stanok")
a("saw.default_s", "основной", "asosiy")
a("saw.std", "стандарт", "standart")
a("saw.diff", "Отличается от стандарта станка «{{m}}» (изменено только в этом проекте):",
  "«{{m}}» stanok standartidan farq qiladi (faqat shu loyihada o'zgartirilgan):")
a("saw.restore", "Вернуть стандарт станка", "Stanok standartini qaytarish")
a("saw.save_note", "Параметры материала и раскроя станут стандартом для новых проектов. Параметры станка (пила, торцовка, вращения, полосы) меняются только с паролем — изменения оператора в проекте на другие проекты не переходят.",
  "Material va kroy parametrlari yangi loyihalar uchun standart bo'ladi. Stanok parametrlari (pila, torsovka, burilishlar, polosalar) faqat parol bilan o'zgaradi — operatorning loyihadagi o'zgarishi boshqa loyihalarga o'tmaydi.")
a("saw.save_machine_too", "Сохранить также параметры станка", "Stanok parametrlarini ham saqlash")
a("saw.no_diff", "Параметры станка совпадают со стандартом.", "Stanok parametrlari standart bilan bir xil.")
a("saw.password", "Пароль пользователя {{login}}", "{{login}} foydalanuvchisi paroli")
a("saw.add", "Добавить станок", "Stanok qo'shish")
a("saw.edit", "Изменить", "O'zgartirish")
a("saw.delete", "Удалить станок", "Stanokni o'chirish")
a("saw.name", "Название", "Nomi")
a("saw.changed", "Изменено", "O'zgartirilgan")
a("saw.mine", "Мой станок", "Mening stanogim")
a("saw.make_default", "Основной станок предприятия", "Korxonaning asosiy stanogi")
a("saw.page_note", "У каждого станка свой стандарт (толщина диска пилы может меняться). Новые операции раскроя и импорт (если в файле нет параметров) берут параметры станка пользователя, иначе — основного. Изменение стандарта — только с паролем пользователя; записывается, кто и когда изменил.",
  "Har stanokning o'z standarti bor (arra diski qalinligi o'zgarib turishi mumkin). Yangi kroy operatsiyalari va import (faylda parametr bo'lmasa) foydalanuvchi stanogidan, bo'lmasa asosiy stanokdan oladi. Standartni o'zgartirish — faqat foydalanuvchi paroli bilan; kim va qachon o'zgartirgani yoziladi.")
a("saw.mine_note", "«Мой станок» — для входа {{login}}: новые проекты этого пользователя берут параметры выбранного станка.",
  "«Mening stanogim» — {{login}} logini uchun: shu foydalanuvchining yangi loyihalari tanlangan stanok parametrlarini oladi.")
a("saw.f.kerf", "Толщина пилы", "Pila qalinligi")
a("saw.f.kerf_group", "Толщина пилы для групповых деталей", "Guruh detallar uchun pila qalinligi")
a("saw.f.trim_length", "Торцовка по длине", "Uzunlik bo'yicha torsovka")
a("saw.f.trim_width", "Торцовка по ширине", "En bo'yicha torsovka")
a("saw.f.trim_includes_kerf", "Торцовка включает пилу", "Torsovka pilani o'z ichiga oladi")
a("saw.f.end_offset_bottom", "Мин. отступ в конце (снизу)", "Oxiridagi min. otstup (pastda)")
a("saw.f.end_offset_right", "Мин. отступ в конце (справа)", "Oxiridagi min. otstup (o'ngda)")
a("saw.f.max_rotations", "Макс. количество вращений", "Maks. burilishlar soni")
a("saw.f.pack_height", "Высота пакета", "Paket balandligi")
a("saw.f.complex_strips", "Сложные полосы", "Murakkab polosalar")
a("saw.f.strip_sort", "Сортировка полос", "Polosalarni saralash")
a("saw.f.in_strip_sort", "Сортировка в полосе", "Polosa ichida saralash")
a("saw.f.min_strip_width", "Мин. ширина полосы", "Polosaning min. eni")
a("saw.f.max_strip_width", "Макс. ширина полосы", "Polosaning maks. eni")
a("saw.f.max_strip_length", "Макс. длина полосы", "Polosaning maks. uzunligi")
a("saw.f.min_trim_cut", "Минимальная обрезка", "Minimal qirqim")
