# Giben GDrive — `.zip` → `.DAX` + `.CPX` (ikkilik) postprotsessori

Holat: **to'liq** (generatsiya uchun). 10/10 `.DAX` va 7/7 `.CPX` (G57 bilan solishtiriladigan buyurtmalar) loyiha + kesish daraxtidan **bayt-ma-bayt qayta yasaldi**. Siqish belgilari (`FC nn`) ning ichki ma'nosi va bir nechta doimiy baytlar taxminiy (6-bo'lim).

Manba: `post prtsessorlar/PILNIY APPARAT/Giben GDrive/*.zip` (10 ta: 3151–3161, 3154 yo'q).
Mos loyiha: `giblab project/3 Eldor/<NNNN> <mijoz>/<NNNN>_<mijoz>.project` (pastki chiziqli variant).

---

## 1. Fayllar

| Xususiyat | Qiymat |
|---|---|
| Tashqi fayl | `<loyiha nomining birinchi 8 belgisi>.zip` — DOS 8.3 nom: `3161_<mijoz ismining 3 harfi>.zip` (masalan `3161_Mij.zip`) |
| Zip ichida | 2 ta fayl, papkasiz: `<8 belgi>.DAX`, `<8 belgi>.CPX` (shu tartibda); deflate (method 8), flag `0x0808` (data descriptor + UTF-8 nom) |
| Soni | buyurtmaga 1 zip — faqat **birinchi CS operatsiyasi** (birinchi material). Material nomi zip ichida **umuman yo'q** |
| Kodlash | ikkilik, little-endian; matn maydonlari cp1251/ASCII, kirill **transliteratsiya qilinadi** (`Фронтальная` → `Frontalynaya`) |
| Birlik | o'lchamlar mm × 1000, `int32` |
| `.DAX` | detallar va list ro'yxati (data) |
| `.CPX` | kesish kartalari (cutting patterns) |

## 2. Kodlash: maydon-siqish belgilari

Ikkala fayl ham `04 00` (uint16 = 4, versiya) bilan boshlanadi, keyin **yozuvlar** ketma-ketligi. Yozuv ichida sonli maydonlar xom yoziladi; **bayt-massiv (matn/zahira) maydonlari** esa «oxiridagi nollar siqilgan» shaklda:

* `<mazmun, oxirgi nol bo'lmagan baytgacha>` + `FC nn` — maydonning qolgan `nn` bayti `00` (nn = 1..255).
* to'liq bo'sh maydon → faqat `FC nn` (nn = maydon uzunligi);
* maydon to'liq to'lgan bo'lsa — `FC` belgisi yo'q (namunada uchramadi);
* `FC 00` — **yozuv oxiri** belgisi.

Shu model bilan har bir `.DAX` yozuvi ochilganda aynan **201 bayt**, `.CPX` kesim yozuvi **48 bayt**, karta sarlavhasi **96 bayt** chiqadi (izchil). Sonli maydonlardagi nollar siqilmaydi (masalan `01 00 00 00` xom). Generator uchun eng xavfsiz yo'l — quyidagi shablonlarni **aynan** takrorlash.

## 3. `.DAX` tuzilmasi

```
04 00                                   versiya
yozuv A (doimiy):  FC 37  80 3E  FC 67  FC 01  FC 28  FC 00
yozuv B (doimiy):  FF FF  FC 32  01 FC 13  FC 01  FC 80  FC 00
list yozuvi        (1 ta)
detal yozuvlari    (N ta, CS operatsiyasi tartibida)
DOREZAT yozuvi     (1 ta, doimiy)
```
* Yozuv A: 55 nol + `0x3E80` (=16000 — ehtimol qalinlik 16 mm ×1000, barcha namunalarda 16 mm bo'lgani uchun tasdiqlanmagan) + 103 nol + 1 + 40 nol.
* Yozuv B: `FFFF` + 50 nol + `01` + 19 nol + 1 + 128 nol. 10/10 faylda bayt-ma-bayt bir xil.

### 3.1 Detal yozuvi (list va DOREZAT ham shu shaklda)

| Bayt | Tur | Maydon | Detal | List | DOREZAT |
|---|---|---|---|---|---|
| 0 | int32 | indeks / id | 1..N (tartib raqami) | `5001` (`89 13 00 00`, doimiy) | `999` |
| 4 | int32 | uzunlik ×1000 | `part/@l` | `sheet/@l` (2750000) | `1000000` |
| 8 | int32 | en ×1000 | `part/@w` | `sheet/@w` (1830000) | `1000000` |
| 12 | int32 | miqdor | `part/@count` | jami listlar (`cMaterialCount`) | `1000` |
| 16 | 24 bayt | zahira | `FC 18` (bo'sh) | `FC 18` | `FC 18` |
| 40 | 40 bayt | nom | detal `@name` (transliteratsiya, cp1251) + `FC (40−uzunlik)` | `FC 28` (bo'sh) | `DOREZAT!!!` + `FC 1E` |
| 80 | int32 | tur | `1` | `4` | `1` |
| 84 | int32 | miqdor (takror) | `count` | listlar soni | `1000` |
| 88 | int32 | miqdor (takror) | `count` | listlar soni | `1000` |
| — | — | yozuv dumi | `FC 44 FC 01 FC 28 FC 00` (68 + 1 + 40 nol, oxir) | xuddi shu | xuddi shu |

Misol (3161, 1-detal `01_001 bok` 1900×347, 1 dona):
```
01 00 00 00  E0 FD 1C 00  78 4B 05 00  01 00 00 00  FC 18
30 31 5F 30 30 31 20 62 6F 6B  FC 1E                    "01_001 bok" + 30 nol
01 00 00 00  01 00 00 00  01 00 00 00
FC 44 FC 01 FC 28 FC 00
```
`DOREZAT!!!` (rus. «дорезать» — qo'lda qayta kesish) — 999-raqamli soxta detal 1000×1000, 1000 dona; `.CPX` da 4-daraja kesim kerak bo'lgan bo'laklar shu raqam bilan belgilanadi (4.2).

Tekshiruv: 10/10 faylda detal yozuvlari soni = CS operatsiyasidagi detal-qatorlar (29, 29, 55, 23, 42, 22, 30, 11, 107, 10), tartib = operatsiyadagi `<part>` tartibi, `l/w/count/name` 100 % mos (3160 dagi yagona kirill nom transliteratsiya bilan).

## 4. `.CPX` tuzilmasi

```
04 00
{ karta sarlavhasi, 2-daraja yozuvi, kesim yozuvlari… } × kartalar soni
```

### 4.1 Karta sarlavhasi (har karta boshida)
| Bayt | Tur | Maydon | Qiymat |
|---|---|---|---|
| 0 | uint16 | belgi | `FF FF` |
| 2 | uint16 | karta raqami | 1, 2, … |
| 4 | int32 | list havolasi | doim `1` |
| 8 | int32 | shu sxema bo'yicha listlar soni | `RIPETIZIONI` (1 yoki 2) |
| 12 | int32 | DIMX ×1000 | 1830000 yoki 2750000 |
| 16 | int32 | DIMY ×1000 | 2750000 yoki 1830000 |
| 20 | uint8 | ? | doim `01` |
| — | | | `FC 4B FC 00` (75 nol, yozuv oxiri) |

Keyin darhol **2-daraja yozuvi** (butun karta): `02 00 00 00 <DIMX int32> 01 00 FC 26 FC 00`.

### 4.2 Kesim yozuvi (10 bayt + `FC 26 FC 00`)
| Bayt | Tur | Maydon |
|---|---|---|
| 0 | int16 | daraja: 3, 4, 5 (G57 `TIPOTG` bilan bir xil raqam) |
| 2 | int16 | detal: `0` — bo'lak keyin yana kesiladi; `1..N` — tayyor detal (`.DAX` dagi tartib raqami); `999` — 4-daraja kerak (DOREZAT) |
| 4 | int32 | bo'lak o'lchami ×1000 (`QUOTATG`) |
| 8 | int16 | takror soni (`QTARIP`) |

Kesimlar daraxtning **pre-order** o'tishi (G57 `Tagli_Ed` bilan bir xil tartib), lekin:
* **faqat 3 daraja** (3, 4, 5). 5-darajadagi bo'lak 6-daraja kesim talab qilsa (G57 da farzandli `TIPOTG=5`), u `detal=999` bilan yoziladi va **uning farzandlari tashlab yuboriladi** — operator qo'lda qayta kesadi.
* `takror>1` bo'lgan barg — bir xil detal deb faraz qilinadi; indeks birinchi nusxaning detali (namunalarda takrorlangan barglarda har doim bir xil detal edi).

Tekshiruv: 7/7 buyurtmada barcha kartalar G57 daraxtidan shu qoida bilan olingan ketma-ketlikka **aynan** teng (masalan 3161: 26 yozuv, 3 ta `999`).

## 5. Kesish rejasi xulosasi
* Kartalar soni, orientatsiyasi, listlar soni («kitob») — sarlavhada. Jami listlar `.DAX` list yozuvida.
* Detal joylashuvi koordinatalari yo'q — faqat kesimlar ketma-ketligi va barglardagi detal raqami.
* Kromka, tekstura, material nomi, kerf, trim — **yo'q** (kerf va trim kesim o'lchamlariga «singdirilgan»).
* Qoldiq (business waste) yozilmaydi.

## 6. Loyiha → fayl moslashuvi (misollar, tekshirilgan)

| Loyiha | Fayl | Misol |
|---|---|---|
| `project/@name` birinchi 8 belgi | zip va ichki fayl nomlari | `3161_<mijoz>` → `3161_Mij.DAX/.CPX` |
| `sheet/@l,@w`, `@cMaterialCount` | DAX list yozuvi | 3156: `2750000, 1830000, 8` |
| `part/@l,@w,@count,@name` | DAX detal yozuvi | 3155 13-indeks `01_031 polka` 777×270, 8 dona |
| detal tartibi | DAX indeks 1..N | CS `<part>` tartibi (3151: id 42 → 1, id 44 → 2, id 43 → 3) |
| kesim daraxti | CPX | 3161 1-karta: `03 00 00 00 B0 64 22 00 01 00` (T3 2254) → `04 00 00 00 A0 68 06 00 01 00` (T4 420) → (5, detal 7, 498000, ×2) → (5, 999, 868000, ×1 — ichida 346 lik 4-daraja kesim kerak) … |
| `RIPETIZIONI` | CPX sarlavha +8 | 3157 1- va 2-karta: 2 |

## 7. Minimal misol (sintetik, anonim)

List 2750×1830, detallar: 1 — `01_001 bok` 1000×500 ×2, 2 — `01_002 polka` 600×400 ×1; bitta karta `DIMX=1830`: T3 1000 → T4 500 ×2 (detal 1) → T4 400 → T5 600 (detal 2).

`.DAX` (hex):
```
04 00
FC 37 80 3E FC 67 FC 01 FC 28 FC 00
FF FF FC 32 01 FC 13 FC 01 FC 80 FC 00
89 13 00 00 30 F6 29 00 70 EC 1B 00 01 00 00 00 FC 18 FC 28 04 00 00 00 01 00 00 00 01 00 00 00 FC 44 FC 01 FC 28 FC 00
01 00 00 00 40 42 0F 00 20 A1 07 00 02 00 00 00 FC 18 30 31 5F 30 30 31 20 62 6F 6B FC 1E 01 00 00 00 02 00 00 00 02 00 00 00 FC 44 FC 01 FC 28 FC 00
02 00 00 00 C0 27 09 00 80 1A 06 00 01 00 00 00 FC 18 30 31 5F 30 30 32 20 70 6F 6C 6B 61 FC 1C 01 00 00 00 01 00 00 00 01 00 00 00 FC 44 FC 01 FC 28 FC 00
E7 03 00 00 40 42 0F 00 40 42 0F 00 E8 03 00 00 FC 18 44 4F 52 45 5A 41 54 21 21 21 FC 1E 01 00 00 00 E8 03 00 00 E8 03 00 00 FC 44 FC 01 FC 28 FC 00
```
`.CPX` (hex):
```
04 00
FF FF 01 00 01 00 00 00 01 00 00 00 70 EC 1B 00 30 F6 29 00 01 FC 4B FC 00
02 00 00 00 70 EC 1B 00 01 00 FC 26 FC 00          2-daraja: butun karta 1830
03 00 00 00 40 42 0F 00 01 00 FC 26 FC 00          T3 1000
04 00 01 00 20 A1 07 00 02 00 FC 26 FC 00          T4 500 ×2 → detal 1
04 00 00 00 80 1A 06 00 01 00 FC 26 FC 00          T4 400 (yana kesiladi)
05 00 02 00 C0 27 09 00 01 00 FC 26 FC 00          T5 600 → detal 2
```

## 8. Noaniq joylar va savollar

1. `FC nn` siqish modeli namunalar bilan izchil, lekin maydon chegaralari (qaysi baytlar «massiv» maydon) taxmin. Masalan son maydonida `0xFC` bayti uchrasa (1..2999 oralig'idagi butun mm lardan faqat 10 tasida bor: **589, 720, 851, 1441, 1572, 1703, 1834, 2424, 2555, 2686** mm — masalan 720 mm = `80 FC 0A 00`; namunalarda bunday o'lcham uchramadi. Bizning generator ularni xom yozadi — stanok o'qishini sinash kerak) qanday ekranlanadi? Namunalarda uchramadi. 40 belgilik to'liq nom ham uchramadi.
2. Yozuv A dagi `0x3E80` = 16000 — material qalinligimi (×1000)? Boshqa qalinlikdagi (masalan 18 mm, 3 mm XDF) namuna kerak.
3. List yozuvi id `5001` va tur `4`, detal tur `1` — doimiylarmi? Bir nechta list formati bo'lsa (qoldiq + butun list) qanday yoziladi?
4. Faqat birinchi material eksport qilinadi va material nomi faylda yo'q — stanok operatori materialni qanday biladi? Har material uchun alohida zip kerakmi (nomlar to'qnashuvi: hammasi `<8 belgi>.zip`)?
5. 4-daraja kesimlar `999 / DOREZAT!!!` ga aylantiriladi (stanok 3 darajali). Optimizatorimiz GDrive uchun daraja ≤ 3 cheklovi bilan ishlashi kerakmi?
6. Kirill transliteratsiya jadvali: namunada faqat `Фронтальная → Frontalynaya` (ь → `y`, я → `ya`). To'liq jadval qanday (ы, щ, ц, ё, й…)?
7. Detal nomi 40 baytdan uzun bo'lsa — qirqiladimi?
8. `RIPETIZIONI` 2 dan katta (kitob 3+ list) bo'lgan namuna yo'q.

---

## 9. 2026-10-04 onlayn namunasi bilan tekshiruv

Bitta loyiha (3 karta, burilishlar 4): `.DAX` va `.CPX` namuna bilan **bayt-ma-bayt bir xil**, ichki nomlar `Bez_imen.DAX/.CPX`
(loyiha nomi lotinga o'girilib, 8 belgi) — `tools/bench/pp_online_check_saw.py gdrive`. Generator o'zgartirilmadi. Namunada
4-daraja bo'laklar `999` («DOREZAT!!!») bilan belgilangan (stanok 3 darajani biladi) — bizniki bilan bir xil.
