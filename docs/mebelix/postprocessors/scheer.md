# Scheer («Pa») — `.zip` → `NAME.CUT` + `soll.cut` + `holz0000.rec` + `teile.lst`

Holat: **kesish rejasi to'liq** — bitta namuna (3 karta, 35 detal, burilishlar 3) 4 fayl bo'yicha bayt-ma-bayt qayta yasaldi;
etiketka fayli (`etikett.bin`) **chiqarilmaydi**. Manba: 2026-10-04 onlayn namunasi (bitta loyiha). Generator:
`backend/app/services/ppfmt/saw_scheer.py` (kalit `scheer`), tekshiruv: `tools/bench/pp_online_check_saw.py scheer`,
testlar: `backend/tests/test_ppfmt_saw_online.py`.

## 1. Fayllar
| Fayl | Mazmuni |
|---|---|
| `NAME.CUT` | dastur nomi, 32 belgigacha bo'sh joy bilan to'ldirilgan + CRLF |
| `soll.cut` | kartalar ro'yxati (har karta — bitta qator, CRLF) |
| `holz0000.rec` | ikkilik kesish rejasi (little-endian) |
| `teile.lst` | detallar ro'yxati (har detal kesim yozuvi — bitta qator, CRLF) |
| `etikett.bin` | etiketkalar (1024 baytli yozuvlar, ZPL) — **yozilmaydi**, 6-bo'lim |

Dastur nomi — **8 belgi**: loyiha nomi lotinga o'giriladi, bo'sh joy → `_` (`Без имени` → `Bez_imen`); loyiha raqami bo'lsa va
nom shu raqam bilan boshlanmasa — oldiga qo'shiladi. Stanok sozlamasi `program_name` berilsa — o'sha (8 belgigacha).
Matnlar — ASCII, lotin, **katta harflar** (material va loyiha nomi); vergul — maydon ajratuvchi, matnda bo'sh joyga almashtiriladi.

Stanok **3 kesim darajasini** biladi → «Макс. количество вращений» ≤ 3 (chuqurroq daraxtda generator `ValueError` beradi).

## 2. `soll.cut`
```
   1,2750.0,1830.0,  16.0,LDSP BELIY KARON,   1,   0.0, ,BEZ IMENI                      
```
| # | Kenglik | Maydon |
|---|---|---|
| 1 | 4 (o'ngga) | karta raqami |
| 2 | 6, `%.1f` | list o'lchami — 1-daraja kesimlarga **ko'ndalang** (polosa uzunligi) |
| 3 | 6, `%.1f` | list o'lchami — 1-daraja kesimlar **bo'ylab** |
| 4 | 6, `%.1f` | qalinlik |
| 5 | 16 | material (katta harf, 16 belgi) |
| 6 | 4 | karta nusxalari |
| 7 | 6 | `0.0` (doimiy) |
| 8 | 1 | bo'sh joy |
| 9 | 31 | loyiha nomi (katta harf) |

## 3. `holz0000.rec`
`0x180` bayt fayl sarlavhasi + `0x580` baytli bloklar: 0-blok (stanokning standart yozuvi) + har karta uchun bitta blok.
Namuna: 3 karta → `0x180 + 4 × 0x580 = 6016` bayt.

### 3.1 Fayl sarlavhasi (0x180) — doimiy
Ikki yozuv (`0x000` va `0x100`): `int32` (4 / 2), `float32` 110, 3000, 3, 110, 6345, 3; `0x24…0x6F` — stanok dasturi qoldirgan
baytlar; `0x70` — `16 00 2D 00 00 00` + `d:\scheer\`; `0xC8` — `1000, 2000` (int16), `150.0, 190.0`. Kroyga bog'liq maydon
topilmadi — generator namunadagi qiymatlarni o'zgarmas holda yozadi.

### 3.2 Karta bloki (0x580 = 128 + 64 × 20)
Sarlavha (128 bayt; ko'rsatilmagan baytlar — nol):
| Ofset | Tur | Qiymat |
|---|---|---|
| 0x00 | int16 | `11` (0-blokda `1`) |
| 0x02 | float32 | list o'lchami 1-daraja kesimlar bo'ylab |
| 0x06 | float32 | ikkinchi o'lcham |
| 0x0A | float32 | qalinlik |
| 0x0E | int16 | karta raqami (1 dan) |
| 0x14 | int16 ×3 | `4, 1, 6696` (doimiy; 0-blokda `3, 1, 0`) |
| 0x1A | float32 | `10.0` |
| 0x1E | 4 bayt | `03 01 03 01` |
| 0x22 | float32 ×2 | `10.0, 200.0` (0-blokda `10.0, 500.0`) |
| 0x2A | int32 | `1` |
| 0x2E | 16 belgi | material (katta harf; 0-blokda `DAMS1`) |
| 0x43 | bayt | `4` |
| 0x4A | float32 ×5 | `500, 500, −99, −99, 29.83` |

Kesim yozuvi (20 bayt, `<hffh8s`), preorder, 64 tagacha, qolgani nol:
| Maydon | 1-daraja | 2-daraja | 3-daraja |
|---|---|---|---|
| int16 soni | takror | takror | **100 + takror** |
| float32 A | o'lcham | 0 | o'lcham |
| float32 B | 0 | o'lcham | 0 |
| int16 | 0 | 0 | 0 |
| 8 belgi | detal raqami (konteynerda 8 ta bo'sh joy) | | |

O'lcham — ota o'qi bo'ylab (propilsiz); detal raqami — CS operatsiyasidagi tartib raqami (1 dan). 1-daraja bo'laklar doim
konteyner; ota bo'lakni to'liq egallamagan detal oraliq konteynerga o'raladi. Ketma-ket bir xil bo'laklar (bir xil detal yoki
bir xil pastki daraxt) bitta yozuvga yig'iladi. Chiqindi va delovoy qoldiq yozilmaydi. Torsovka va propil faylda yo'q.

Misol (namunaning 1-kartasi, 1-polosa): `460` polosa → `2500` (detal 10), `100 → 434` (detal 14), `100 → 434` (detal 15):
```
(1, 460, 0, "")  (1, 0, 2500, "10")  (1, 0, 100, "")  (101, 434, 0, "14")  (1, 0, 100, "")  (101, 434, 0, "15")
```

## 4. `teile.lst`
Har detal kesim yozuvi (rec dagi barg yozuvi) uchun bitta qator, 169 belgi + CRLF, maydonlar vergul bilan:
```
Bez_imen,Bez_imen,  1,  1,LDSP BELIY KARON,16.0,10        ,  1,  1, 2500.0,  460.0,0,    ,    ,            ,<30 bo'sh>,<30 bo'sh>
```
dastur nomi (8) ×2, karta raqami (3) ×2, material (16), qalinlik (`%4.1f`), detal raqami (10, chapga), jami soni (3),
**shu paytgacha kesilgani** (3; o'sib boruvchi, shu yozuvdagi donalar bilan), loyiha uzunligi va eni (`%7.1f`), tekstura
(`1` — «Ткт» belgilangan, aks holda `0`), keyin 4, 4, 12, 30, 30 belgilik bo'sh maydonlar.

## 5. Tekshiruv
`pp_online_check_saw.py scheer`: B kroy daraxti (`.ocm` + detal raqamlari) → `NAME.CUT`, `soll.cut`, `holz0000.rec`,
`teile.lst` — 4/4 bayt-ma-bayt; A kroy (4 daraja) → `ValueError`; bizning optimizator (burilishlar 3) bilan oxiridan-oxirigacha.

## 6. Yozilmaydigan va noaniq joylar
1. **`etikett.bin`** — 1024 baytli yozuvlar (0-yozuv `@R` — qoldiq etiketkasi, keyin har detal: raqam (8) + soni (4) + `0000` +
   ZPL matni + `;@`, bo'sh joy bilan to'ldirilgan, oxirida CRLF). Mazmuni — avvalgi dasturning ZPL etiketka dizayni; nusxalanmaydi.
   Stanok bu faylsiz dasturni qabul qiladimi — stanokda sinash kerak; kerak bo'lsa bizning etiketka shablonimizdan chiqariladi.
2. Fayl sarlavhasi va karta sarlavhasidagi doimiylar (`4, 1, 6696`, `10 / 10 / 200`, `500 / 500 / −99 / −99 / 29.83`,
   sarlavhadagi `3.0` — propil bo'lishi mumkin) ma'nosi noma'lum: bitta namunada hammasi bir xil.
3. Karta nusxalari > 1 bo'lganda `teile.lst` dagi o'sib boruvchi son nusxalarga ko'paytiriladi deb olindi (namunada nusxa 1).
4. Bitta kartada 64 dan ortiq kesim yozuvi — blok o'lchami qat'iy deb olindi (generator xato beradi).
5. Zip nomi — `<loyiha>_<material>.zip` (namuna qayta nomlangan, asl nomi noma'lum).
