# KDT — korxonada stanokda hozir ishlayotgan fayllar (2026-10-26)

> Manba: korxonaning 10 buyurtmasi (`post/` — repoga kirmaydi): pilniy markaz (arra) zip'lari, prisadka zip'lari va shu fayllarni
> bergan `.project` lar. Faqat chiqish fayllari va loyiha XML o'qildi; boshqa dastur kodi / ichki ma'lumotlari ishlatilmadi.
> Solishtiruv vositasi: `tools/bench/pp_kdt_real.py` (fayldagi tayyor kroy bilan — optimizator farqi chiqarib tashlanadi).

## Natija

| | Fayllar | Natija |
|---|---|---|
| Prisadka (`kdt_panel`, `KDTPanelFormat`) | 680 | **629 bayt-ma-bayt bir xil**; 51 — teshik / freza / paz aynan bir xil, faqat asbob yo'li tartibi boshqacha |
| Arra (`kdt_presize_xml`, v2) | 32 | aynan o'sha kroyga ega **5 / 5 mantiqan bir xil** (farq — faqat ichki raqamlar); 27 — `.project` dagi kroy arra faylidan keyin o'zgargan (solishtirib bo'lmaydi) |
| Etiketka QR | 1038 | XNC li detal — prisadka dasturi nomi, XNC siz — QR yo'q, qoldiq — raqami; MX ham shunday |

Eski formatlar alohida kalitda qoladi: arra `kdt_presize_xml_v1` (2021), prisadka `kdt_trepan` (`AndersonXMLdata`).

## Arra — `kdt_presize_xml` (v2)

- Zip ichida `<buyurtma> <material>/<buyurtma> <material>.xml` + har detalga `<kod>.emf`, qoldiqqa `O1.emf` (aslida PNG,
  640×480, 1 bit). Papka / fayl nomi lotinda (kirill → lotin), XML ichida material nomi o'zgarmaydi.
- XML bitta qatorda, atributlar alifbo tartibida, bo'sh tugun `/>`.
- `print_code`: detal — operatsiyadagi tartib raqami; qoldiq — `O1`, `O2` …
- 3-qatlam va chuqurroq konteyner tugunlarida `trim` = (torsovka + propil) / 2 (2 + 3 → 2.5), bolalar shuncha suriladi
  (real fayllarning 481 holatining hammasida).
- Har darajada avval detallar (asl tartibda), keyin ichki bo'laklar kattasidan kichigiga; qoldiq oxirida.
- Ichki `id`, list `code`, qoldiq `code` (`O12` kabi) — onlayn tizimning eksport paytidagi ichki raqamlari; MX o'z noyob
  raqamlarini yozadi (mantiqqa ta'sir qilmaydi).
- Etiketka (o'zimizning maket): soni, prisadka dasturi nomi + **QR** (stanok etiketkani skanerlab dasturni ochadi), buyurtma,
  material, kromkalar (matn + sxema), o'lcham, `raqam_nom`, mahsulot, sana. Qoldiq: buyurtma, material, «Деловой остаток»,
  o'lcham, raqam, soni, sana, QR (raqam). QR — oddiy QR (Micro QR emas).

## Prisadka — `kdt_panel` (`KDTPanelFormat`)

- **Bitta detal — bitta fayl.** Nomi — XNC kodi; kod bo'sh bo'lsa `<ishlov nomi>_null_1`; takror — `nom (1)`, `nom (2)`.
  Arra etiketkasidagi QR — shu nom (qavssiz).
- Koordinata: X — dasturdagidek, Y — pastdan (`en − y`; dastur boshi chap-yuqorida).
- `PanelOutline`: past, o'ng, yuqori, chap tomon; kromka bo'lsa `Banding` 1.5, «(belgi) qalinlikmm», kromka rangi; bo'lmasa 0.3, «-».
- Turlar: 1 — yuza teshigi, 8 — orqa tomon ko'r teshigi, 2 — qirra teshigi (`Quadrant`: chap 1, o'ng 2, yuqori 3, past 4),
  3 — paz (`UseSaw`), 7 — freza yo'li (`Path`: Point / Line / Arc, Radius, Direction; korreksiya 1 ↔ 2).
- **Orqa tomon dasturi** shu faylda: ko'r teshiklari — 8, teshib o'tuvchilari — 1. Orqa dasturda freza / paz bo'lsa (yuzda
  yo'q) — detal **ag'dariladi**: orqa dastur asosiy (1, 3, 7), yuz tomon ko'r teshiklari — 8, hamma X — `uzunlik − x`.
- Tartib: yuza elementlari koordinata boshidan har safar eng yaqini (paz bajarilgach joriy nuqta — paz boshi); oxirida qirra
  teshiklari: chap (Y ↑), o'ng (Y ↓), past (X ↑), yuqori (X ↓). Yuza tartibining ≈ 8 % ida real fayl boshqa burchakdan
  boshlaydi — qoida aniqlanmadi (burg'ulanadigan narsa bir xil).
- CRLF, sonlar 4 kasrgacha (yoy radiusi 5).

## Ochiq

- `post/prisadka/1 JAXONGIR.zip` — arra zip'ining nusxasi (prisadka fayli yo'q): 3188 prisadka solishtirilmadi.
- Asbob yo'li tartibining qolgan 8 % i; orqa tomondagi freza / paz (namunada yo'q).
