# MX Kroy yangilanishi — 2026-11-10 (server dasturchilari uchun)

**Nima o'zgardi:** faqat backend optimizatori (`backend/app/services/optimizer.py`). Baza, API, migratsiyalar va frontend o'zgarmagan,
baza qayta tiklanmaydi.

| | |
| --- | --- |
| Kod | `MebeliX_Kroy` `master` va `mebelix-mx-kroy-eko` `eko-integratsiya` — shu fayl qo'shilgan commit |
| Yangilash | kodni olish → backend konteynerini (API + kroy ishchilari) qayta ishga tushirish |
| Xodimlarga | F5 shart emas (kroy serverda hisoblanadi); eski natijalar o'zgarmaydi — kerak bo'lsa «Раскроить» qayta bosiladi |

## O'zgarish (xodim videosi, 2026-11-10)

**Qoldiq list (soni cheklangan) + butun listlar:** avval MX qoldiqni ishlatmay bitta butun listni ortiqcha sarflashi mumkin edi
(xodim loyihasi: qoldiq 750×1830 + 2750×1830, 80 detal — MX 6 butun list, onlayn / lokal tizim qoldiq + 5 list). Endi optimizator
qoldiqqa bir nechta detal to'plamini sinab, qolganini kamroq butun listga joylashga harakat qiladi; faqat material kamaysa olinadi.
Natija: qoldiq + 5 list (onlayn tizim bilan bir xil). «Стандарт» rejimida kroy vaqti ≈ 11 s.

## Tekshirish

* `cd backend && pytest -q` (yangi `tests/test_cs_remnant_prefix.py`).
* `cd tools/bench && python compare_stock.py normal` — 44 ko'p-listli kroy: 573.47 m² (avval 573.98), xato 0.
