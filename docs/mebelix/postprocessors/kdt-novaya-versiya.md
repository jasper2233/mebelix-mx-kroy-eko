# KDT «Новий версия» — `.zip` → `NUM=k … .qk` + `.lbd` (KS33X ning yangi varianti)

Holat: **qisman** (KS33X bilan bir xil sabab): kesish rejasi **to'liq** — 30/30 `.qk` bayt-ma-bayt qayta yasaldi, 30/30 `.lbd` daraxti mos va `.lbd` sintaksisi 100 % o'qildi; etiketka blobi ochiq savol.

Manba: `post prtsessorlar/PILNIY APPARAT/KDT Новий версия/*.zip` (7 ta: 3151, 3153, 3155, 3156, 3157, 3159, 3161).
Asosiy tavsif — **`kdt-ks33x.md`**; bu hujjat faqat farqlarni beradi. Ikkala papkadagi fayllar bir xil buyurtmalardan 1–2 daqiqa farq bilan eksport qilingan.

---

## 1. Fayllar
KS33X bilan aynan bir xil: `<loyiha>_<material>.zip`, ichida har karta uchun `NUM=<k>   PANELS( <n> x 1 = <n> ).qk` va `.lbd`; deflate, flag `0x0808`; faqat birinchi CS operatsiyasi. Farq — fayl hajmlari:

| Fayl | KS33X | Yangi versiya |
|---|---|---|
| `.qk` | 2 720 032 bayt | **2 920 032 bayt** |
| `.lbd` | X bayt | **X + 1 bayt** (oxirida qo'shimcha `00`) |

## 2. Tuzilma farqlari

### 2.1 `.qk`
* Offset 0: `float32` kerf — bir xil.
* **Jadval A** yozuvi **13 bayt**: `f32 f0, f32 f1, f32 f2, u8 bayroq` — ishlatilgan yozuvda `bayroq = 01`, bo'shida `00`. Manzil `4 + 13·i`; indekslar KS33X dagi kabi (`i=1` karta, `11+r1`, `101+r2`, `1001+r3`), qiymatlar ham bir xil. Natijada yozuvlar 4 baytga tekislanmagan (masalan 3161 da karta yozuvi offset 17 da: `00 00 A0 40 | 00 E0 2B 45 | 00 C0 E4 44 | 01`).
* **Jadval B** boshi `B = 4 + 13·20000 + 1 = 260005` (1 bayt qo'shimcha siljish), yozuv **12 bayt** (`f32 cut, i32 0, i32 takror`), indekslar KS33X dagi kabi (`1`, `2+r1`, `102+r2`, `1002+r3`, `10022+r4`), manzil `B + 12·i`.
* Qolgan hammasi nol; 30/30 faylda nol bo'lmagan barcha baytlar shu model bilan tushuntirildi.

### 2.2 `.lbd`
* Daraxt qismi KS33X bilan **bayt-ma-bayt bir xil** (30/30), etiketka bloblari ham bayt-ma-bayt bir xil (223/223).
* Etiketka CSV **2-maydoni** (indeks 2): KS33X da — loyihadagi jami miqdor (`count`), yangi versiyada — **shu kartadagi bitta listda nechta** (218/218: kartadagi barglar × takrorlar; `num` ga ko'paytirilmagan). Masalan 3155 4-karta: `01_020 bok` loyihada 2 dona → KS33X `2`, yangi `1`.
* Fayl oxirida qo'shimcha bitta `00` bayt (etiketkalardan keyin; ehtimol «davomi yo'q» mantiqiy qiymati).

## 3. Kesish rejasi
KS33X bilan bir xil (`kdt-ks33x.md` 2.4): 1-daraja teskari tartibda, farzandli bo'lak takrorlari `⌊swPackageHeight/(t·listlar)⌋` bo'yicha bo'linadi, 4-daraja faqat B jadvalida, qoldiq faqat `.lbd` da («Остаток», `rest.fme`).

## 4. Loyiha → fayl moslashuvi
`kdt-ks33x.md` 4-bo'lim bilan bir xil; tekshiruv: 7 buyurtma, 30 karta, `.qk` 30/30 bayt-ma-bayt, `.lbd` daraxti 30/30.

## 5. Minimal misol
`kdt-ks33x.md` 5-bo'limdagi sintetik buyurtma uchun `.qk` (2 920 032 bayt) nol bo'lmagan qismlari:
```
0        : 00 00 40 40                          kerf 3.0
17..29   : 00 00 A0 40  00 E0 2B 45  00 C0 E4 44  01      A[1]  (5, 2750, 1830) + bayroq
147..159 : 00 00 A0 40  00 C0 E4 44  00 00 7A 44  01      A[11] (5, 1830, 1000)
1317..1329: 00 00 00 00 00 00 7A 44  00 00 FA 43  01      A[101] (0, 1000, 500)
1330..1342: 00 00 00 00 00 00 7A 44  00 00 C8 43  01      A[102] (0, 1000, 400)
13277..13289: 00 00 00 00 00 00 C8 43 00 00 16 44  01     A[1021] (0, 400, 600)
260017   : 2750.0, 1830.0, 0                    B[1]
260029   : 1000.0, 0, 1                         B[2]
261229   : 500.0, 0, 2                          B[102]
261241   : 400.0, 0, 1                          B[103]
272269   : 600.0, 0, 1                          B[1022]
```
`.lbd` — KS33X misoli bilan bir xil, faqat CSV 2-maydoni kartadagi soni (detal 1 uchun `2`, detal 2 uchun `1` — bu misolda farq qilmaydi) va fayl oxirida `00`.

## 6. Noaniq joylar va savollar
1. Qaysi stanok/dastur versiyasi yangi formatni o'qiydi — ikkalasi ham kerakmi yoki faqat yangisi? (Sozlamada «KS33X» / «yangi versiya» tanlovi bo'lsinmi?)
2. A jadvalidagi `bayroq` bayti (01 — ishlatilgan) va B jadvalining 1 baytli siljishi — boshqa ma'nosi bormi (masalan, «aylantirish» yoki «yoqilgan» bayrog'i)? Namunalarda faqat 00/01.
3. `.lbd` oxiridagi qo'shimcha `00` ma'nosi.
4. Qolgan savollar — `kdt-ks33x.md` 6-bo'lim (blob, kitob qoidasi, qoldiq idx, massiv chegaralari, fayl nomidagi bo'shliqlar).
