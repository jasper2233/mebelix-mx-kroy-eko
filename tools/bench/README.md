# Kroy sifati benchmarki (korxona loyihalari)

`projects/` — korxonaning 205 ta real `.project` fayli (Project.rar dan; mijoz ismlari bor — **git'ga kirmaydi**, faqat
zipda). `corpus.json` — ulardan olingan 398 ta listli kroy (CS): detallar (o'lcham, soni, tekstura), kesish parametrlari
(propil, torsovka, burilishlar, minimal obrezka, yo'nalish), qoldiq qoidalari va **fayl ichida saqlangan avvalgi dastur
natijasi** (listlar, деловой qoldiq m², kesish uzunligi, to'ldirish). 1 ta kroyda avvalgi natija to'liq emas — u
hisobga olinmaydi.

| Skript | Vazifa | Vaqt (2 yadro) |
|---|---|---|
| `compare.py [fast\|normal\|max] [teg]` | Har kroyni MebeliX bilan yechib, listlar / деловой qoldiq / kesish uzunligini solishtiradi, `validate()` bilan tekshiradi; `out_<teg>.json` | normal ≈ 8 daq., fast ≈ 2 daq. |
| `SEL=162,273,348 python compare.py normal qiyin` | Faqat tanlangan kroylar (indeks — corpus.json dagi tartib) | soniyalar |
| `el_check.py` | Kromka ish/material metri — saqlangan qiymatlar bilan | ≈ 1 daq. |
| `xnc_check.py` | CNC teshiklar soni, freza va arra metri — saqlangan qiymatlar bilan | ≈ 2 daq. |
| `corpus_build.py` | `projects/` dan `corpus.json` ni qayta qurish (yangi loyihalar qo'shilsa) | soniyalar |

Qoidalar: optimizatorni o'zgartirgandan keyin **listlar soni ko'paymasligi**, **tekshiruv xatosi 0** bo'lishi kerak.
Natijalar vaqt byudjetiga bog'liq (kompyuter yuklamasi) — ±1–2 list tebranish mumkin; shubhali kroyni `SEL=` bilan
alohida qayta yeching.

So'nggi natija (2026-10-01, `normal`): 1185 list (avvalgi dastur 1212), yomon 0, xato 0 —
`docs/mebelix/P_TAQQOSLASH.md`. Kromka 303/303, CNC 8359/8360 · 8360/8360 · 8360/8360 mos.
