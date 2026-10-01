# Kroy sifati benchmarki (korxona loyihalari)

`corpus.json` — korxonaning 205 ta real `.project` faylidan olingan 398 ta listli kroy (CS): detallar (o'lcham,
soni, tekstura), kesish parametrlari (propil, torsovka, burilishlar, minimal obrezka, yo'nalish), qoldiq
qoidalari va **fayl ichida saqlangan avvalgi dastur natijasi** (listlar soni, деловой qoldiq m², kesish uzunligi,
to'ldirish). 1 ta kroyda avvalgi natija to'liq emas (detallarning bir qismi joylanmagan) — u hisobga olinmaydi.

```bash
cd tools/bench
python3 compare.py normal          # ~8 daqiqa (2 yadro); fast — ~3 daqiqa
SEL=162,273,348 python3 compare.py normal qiyin   # faqat tanlangan kroylar
```

Qoidalar: optimizatorni o'zgartirgandan keyin **listlar soni ko'paymasligi**, **tekshiruv xatosi 0** bo'lishi kerak.
Natijalar vaqt byudjetiga bog'liq (kompyuter yuklamasi) — ±1–2 list tebranish mumkin; shubhali kroyni
`SEL=` bilan alohida qayta yeching.

So'nggi natija (2026-10-01, `normal`, 2 yadroli server): `docs/mebelix/P_TAQQOSLASH.md`.
