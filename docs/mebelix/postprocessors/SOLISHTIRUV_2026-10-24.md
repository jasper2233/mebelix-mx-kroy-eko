# Postprotsessorlar ↔ onlayn tizim: bir xil kroyda solishtiruv (2026-10-24)

Foydalanuvchi talabi: MX dan tanlangan stanokka ketadigan fayl aynan shu stanok o'qiydigan bo'lsin. Natija onlayn tizim
bilan bir xil bo'lguncha tekshirilsin; nima xato bo'lgani ko'rsatilsin.

## Usul (avvalgidan farqi)
* Avval: MX o'z optimizatori bilan kesib, fayl korxona namunasi bilan solishtirilardi. Kroy boshqacha bo'lgani uchun ko'p
  maydonlar faqat «tuzilishi bo'yicha» tekshirilardi, ayrim xatolar ko'rinmay qolgan.
* Endi: onlayn tizimdagi sinov loyihasi («test uchun / Без имени», 124 operatsiya: 3 CS, 120 XNC, CN) kesildi. Har stanok
  uchun fayl yuklab olindi va loyiha `.project` sifatida eksport qilindi. MX shu loyihani import qiladi, **onlayn kroyning
  o'zini** `data` blokidan tiklaydi (`tools/bench/pp_online_cut.py`; 7 karta, 114 detal, LT 207.549 m — onlayn bilan bir
  xil) va o'z generatori bilan fayl yasaydi. Fayllar bayt-ma-bayt solishtiriladi (`tools/bench/pp_online_same_cut.py`).
* Namunalar: `post prtsessorlar/ONLINE_2026-10-24/` (repoga kirmaydi).
* Ikki manba farq qilsa — **korxonaning o'z stanok namunalari ustun** (`post prtsessorlar/PILNIY APPARAT`,
  `PRISADKA APPARAT`: ular lokal tizimning yangiroq versiyasidan, stanoklar aynan shularni o'qigan). Onlayn tizim 2021 yil
  versiyasi.

## Natija — arra (pilniy) markazlari, op 1 (7 karta) va op 3 (3 karta, деловой qoldiq bilan)
| Format | Bir xil | Qolgan farq (ataylab) |
|---|---|---|
| HOLZMA PTX, CadMatic3 (.SPL), Giben G57, GVisionXP, GDrive, Homag CHF, Felder PC7, Nanxing CutSawFG / NXCutSaw, Scheer, Shelling (MCS), AES Alpha, F4Classic (.txt), Lisec, KDT .qk | hammasi | — |
| Felder PC6 | ha | etiketka bloki (`#n=eJ…`), dastur nomi maydoni |
| SCM WinCut | ha | etiketka bloki (30-maydon) |
| SCM MaestroCut | ha | `GibLabLabel` bloki, `Header GibLabID`, `Campo64` tasodifiy ID, `Campo36` (korxona namunasidagidek detal kodi) |
| HOLZMA CadMatic4 (.LC4), KDT .lbd | daraxt | etiketka satriga qo'shiladigan blob |
| KDT XML | ha | `id` hisoblagichining boshlanishi (qadamlari bir xil) |
| Biesse NC300 | kesish + dastur | `B_LABEL` (ichki o'zgaruvchilarsiz) |
| Biesse OSI | detallar, bo'laklar, kartalar | `Chk` (algoritm noma'lum), bo'laklar ro'yxati tartibi (onlaynda xesh tartibi) |
| F4Classic `.ZPL`, KDT XML `.emf`, Scheer `etikett.bin`, Shelling `GibLabData.xml` | — | etiketka / ichki fayllar — yozilmaydi |

## Natija — prisadka (XNC), 118 dastur
BiesseWorks, TPA, Homag WoodWOP, SCM Xilog v3, KDT Trepan, HIRZT/Maggi, Daron, XDWoodCam — **118/118**; SCM Startech — 2/2.
IMA, Holz-Her, Masterwood MW310, G CODE, AES Sirius — onlaynda asbob jadvali bo'sh (fayl chiqmadi / bo'sh dastur), 2026-10-04
namunalari bilan 36/36. Nanxing SyntecCad — MX ataylab lokal (yangi) formatda: onlayn 2021 formati stanokda «Mill path node not on
panel outline» xatosini bergan (2026-10-22). Vitap Bridge — onlayn tizimning o'zida ichki xato (TypeError), namuna yo'q.

## Topilgan va tuzatilgan xatolar
| Format | Xato (avval) | Sabab / dalil | Endi |
|---|---|---|---|
| **Scheer** | `holz0000.rec` boshida doim «4» | eski namunada 3 karta (0-blok + 3 = 4) — doimiy deb olingan; 7 kartali faylda 8 | bloklar soni = kartalar + 1 |
| **F4Classic** | detal raqami = detal ID | Bazis loyihalarida ID = tartib raqami, farq ko'rinmagan; ko'p materialli loyihada noto'g'ri detal (91 o'rniga 62) | operatsiyadagi tartib raqami |
| **Felder PC6** | kromka bayroqlari maydoni 1 belgiga siljigan (« 1» o'rniga «  1») | bo'sh tomon 1 bo'shliq bilan yozilardi | har tomon 2 belgi (korxona namunasi ham shunday) |
| **Felder PC6, AES Alpha, Shelling** | kirill harflar fayldagidek yozilardi | onlayn tizim lotinga o'giradi («Без имени» → «Bez imeni»); qat'iy kenglikli formatlar | lotin (kenglikdan oldin) |
| **Felder PC6/PC7, G57, KDT XML** | list / material raqami 1, 125, 7… | onlayn — loyihadagi list (`part id` 139) va material (`good id` 7) raqami | import qilingan loyihada asl raqamlar (`StockSheet.uid`, `Operation.material_uid`) |
| **PTX** | mahsulot raqami doim «1» | 26-maydon — mahsulotning loyihadagi tartib raqami | tartib raqami |
| **MaestroCut** | bo'sh kromka `" "`; matn cp1251 | korxona va onlayn: `""`; onlayn UTF-8 | qiymat qirqiladi; UTF-8 |
| **XDWoodCam** | `Description` cp1251 | onlayn UTF-8 | UTF-8 |
| **Felder PC7, MaestroCut va b. — «фрезеровка» bayrog'i** | har qanday freza → `true` | korxona PC7: teshib o'tuvchi kesim (`throughCutDepth`) bo'lsa `false` (9 + 15 holat) — 2026-10-22 dagi `throughCutDepth` tuzatishidan keyin yuzaga chiqqan | `render.part_mill_flag` |

Tekshirilib, **o'zgartirilmagan** (korxona namunasi onlayndan farq qiladi, korxona ustun): OSI kesimlar tartibi (onlayn Y bo'ylab
teskari, korxona — daraxt tartibida, 80/80), PTX 30-maydon («(CS) material», onlayn «mahsulot (CS) material»), MaestroCut
`Campo36` (detal kodi), CutSawFG ichki zip (boshqa materiallar).

## Yangi formatlar
* **Altendorf (ELMO)** `.saw` — `saw_altendorf.py`, tavsif `altendorf-elmo.md`. ACUT/BLOCK/LINE geometriyasi onlayn bilan bir
  xil (10 karta); tirgak harfi (P/L) 212/236 kesimda mos.
* **Lisec (XOpt)** `.DAT` — `saw_lisec.py`, tavsif `lisec-xopt.md`. 10/10 karta (`[LPL_REF]` dan tashqari).
* **(CN) nesting**: CNC (NCStudio), KDT (GCode), Homag WoodWOP, TPA, BiesseWorks — `cn_nest.py`, tavsif `cn-nesting.md`.
  Onlayn yo'llar bilan 15/15 fayl bayt-ma-bayt. CN kroy oynasida «Постпроцессор» ro'yxatida, sozlamalari «Настройки →
  Постпроцессоры» da («Выступ снизу», asbob, tezliklar).

## Ochiq savollar
1. Altendorf: 24 kesimda onlayn tizim ko'ndalang tirgakni (L) tanlagan — qoidasi aniqlanmadi (asosan blokdagi oxirgi kesim).
2. Biesse OSI `Chk`.
3. Vitap Bridge (onlayn xato), FastPanel (bu safar yuklab olinmadi; 2026-10-04 namunasi bilan mos), GibCut (`.gibcut` — onlayn
   tizimning o'z formati, qo'shilmaydi), Glass GCODE (shisha bo'lmagan materialda fayl bermadi).
4. CN: onlayn tizim qo'shni detallar orasidagi umumiy kesimni bir marta o'tadi; MX har detal konturini aylanadi (uzunroq,
   lekin xavfsiz). Umumiy kesim — keyingi bosqich.
