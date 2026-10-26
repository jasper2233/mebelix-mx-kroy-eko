# KDT — korxonada stanokda hozir ishlayotgan fayllar (2026-10-26)

Stanoklar: pilniy markaz **KDT KS832**, prisadka **KDT KD-612KHS** (CNC burg'ulash markazi, 2023).

> Manba: korxonaning 10 buyurtmasi (`post/` — repoga kirmaydi): pilniy markaz (arra) zip'lari, prisadka zip'lari va `.project` lar.
> **Muhim:** `.project` lar — MX kroyi; ular onlayn tizimga olinib, U YERDA qayta kesilgan, keyin postprotsessor fayllari olingan.
> Shuning uchun arra fayllaridagi kroy `.project` dagidan boshqa. Tekshiruv usullari:
> 1. `tools/bench/pp_kdt_xml_roundtrip.py` — real arra XML dagi kroy (daraxt, koordinatalar) faylning o'zidan tiklanib, MX
>    yozuvchisiga beriladi: **32 / 32 mantiqan bir xil** (`.project` ga bog'liq emas);
> 2. onlayn tizimda qayta kesilgan loyiha (`--gl NUM=fayl`) bilan `pp_kdt_real.py` (3189: arra 2/2, prisadka 6/6);
> 3. `tools/bench/pp_kdt_own_cut.py` — MX ning O'Z kroyi bilan: 32 arra + 817 prisadka fayli, xato 0 (XML izchil, detallar
>    soni, etiketka QR = prisadka fayli). Faqat chiqish fayllari va loyiha XML o'qildi; boshqa dastur kodi / ichki ma'lumotlari ishlatilmadi.
> Solishtiruv vositasi: `tools/bench/pp_kdt_real.py` (fayldagi tayyor kroy bilan — optimizator farqi chiqarib tashlanadi).

## Natija

| | Fayllar | Natija |
|---|---|---|
| Prisadka (`kdt_panel`, `KDTPanelFormat`) | 680 | **629 bayt-ma-bayt bir xil**; 51 — teshik / freza / paz aynan bir xil, faqat asbob yo'li tartibi boshqacha |
| Arra (`kdt_presize_xml`, v2) | 32 | fayldagi kroy bilan **32 / 32 mantiqan bir xil** (farq — faqat ichki raqamlar: `id`, list `code`, qoldiq `O12`) |
| Etiketka QR | 1038 | XNC li detal — prisadka dasturi nomi, XNC siz — QR yo'q, qoldiq — raqami; MX ham shunday |

Eski formatlar alohida kalitda qoladi: arra `kdt_presize_xml_v1` (2021), prisadka `kdt_trepan` (`AndersonXMLdata`).

## Arra — `kdt_presize_xml` (v2)

- Zip ichida `<buyurtma> <material>/<buyurtma> <material>.xml` + har detalga `<kod>.emf`, qoldiqqa `O1.emf` (aslida PNG,
  640×480, 1 bit). Papka / fayl nomi lotinda (kirill → lotin), XML ichida material nomi o'zgarmaydi.
- XML bitta qatorda, atributlar alifbo tartibida, bo'sh tugun `/>`.
- `print_code`: detal — operatsiyadagi tartib raqami; qoldiq — `O1`, `O2` …
- 3-qatlam va chuqurroq konteyner tugunlarida `trim` = (torsovka + propil) / 2 (2 + 3 → 2.5), bolalar shuncha suriladi
  (real fayllarning 481 holatining hammasida).
- Bo'laklar — kartadagi joylashuv tartibida (koordinata bo'yicha). Polosa oxiridagi деловой qoldiq ham `type="3"`
  (avval MX faqat 1-darajadagi qoldiqni yozardi).
- `<parts>` dagi qoldiq: `l` — list uzunligi bo'ylab, `w` — eni bo'ylab. Panel `l` — birinchi kesimlar bo'ylab o'lcham (list eni
  bo'ylab kesilsa `l` = list eni).
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
- Birinchi tahlilda «detallar avval, keyin kattadan kichikka» qoidasi chiqarilgan edi — u `.project` dagi MX kroyini onlayn
  kroy bilan solishtirishdan kelib chiqqan xato xulosa; olib tashlandi (real fayldan tiklangan kroy buni rad etdi).
- Asbob yo'li tartibining qolgan 8 % i; orqa tomondagi freza / paz (namunada yo'q).
