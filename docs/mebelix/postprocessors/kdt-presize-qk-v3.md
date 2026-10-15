# KDT PreSize V3.3.0P — `.zip` → `NUM=k … .qk` (o'zgaruvchan uzunlik) + `.lbd`

Holat: **kesish rejasi to'liq** — bitta namuna (3 karta, burilishlar 4): `.qk` 3/3 bayt-ma-bayt, `.lbd` daraxti va etiketka
qatorlari (blobsiz) 3/3. Manba: 2026-10-04 onlayn namunasi. Generator: `backend/app/services/ppfmt/saw_kdt_qk3.py`
(kalit `kdt_presize_qk`), tekshiruv: `tools/bench/pp_online_check_saw.py qk3 kdt`, testlar: `test_ppfmt_saw_online.py`.
Asosiy tavsif — `kdt-ks33x.md` va `kdt-novaya-versiya.md`; bu hujjat faqat farqlarni beradi.

## 1. KDT versiyalari (onlayn tizimdagi tanlov)
| Versiya | Format | Bizning kalit | Tekshiruv (A kroy, 3 karta) |
|---|---|---|---|
| V1.4.0P | `.qk` 2 920 032 bayt | `kdt_new` | avvalgi namunalar (30/30) |
| **V6.3.2P** | V1.4.0P bilan **bayt-ma-bayt bir xil** | `kdt_new` | `.qk` 3/3, `.lbd` (blobsiz) 3/3 |
| **V4.x (eski)** | KS33X bilan **bayt-ma-bayt bir xil** (`.qk` 2 720 032 bayt) | `kdt_ks33x` | `.qk` 3/3, `.lbd` (blobsiz) 3/3 |
| **V3.3.0P** | shu hujjat | `kdt_presize_qk` | `.qk` 3/3, `.lbd` (blobsiz) 3/3 |

## 2. `.qk` (little-endian)
Qat'iy o'lchamli jadval o'rniga faqat **to'ldirilgan** yozuvlar ketma-ket yoziladi (namunada 1104 … 4926 bayt).
```
sarlavha (12 bayt):  float32 kerf, float32 dimy, float32 dimx
yozuv (273 bayt), har farzandli bo'lak uchun, preorder (ildizdan boshlab):
  int32   bolalar blokining boshi = BASE[daraja] + 20 × tartib raqami      BASE = 0, 100, 1000, 10020
  int32   bo'lak indeksi          = IDX[daraja] + tartib raqami            IDX  = 1, 11, 101, 1001
  float32 siljish, ota o'lchami, o'lcham          (KS33X A yozuvi: ildiz — off1, dimy, dimx; 1-daraja — off1, dimx, cut;
                                                   chuqurroq — 0, ota cut, cut)
  int32   1
  float32 qalinlik
  uint8   1
  20 × (float32 cut, int32 0, int32 takror)       bolalar (KS33X B yozuvi), bo'shlari nol
  float32 qoldiq
```
* `dimy` — 1-daraja kesimlar bo'ylab list o'lchami, `dimx` — ikkinchisi; `off1` — torsovka + propil.
* Daraja: 0 — ildiz (karta), 1…3 — farzandli bo'laklar; tartib raqami: 1-darajada `j`, chuqurroqda `ota tartibi × 20 + j`
  (KS33X dagi kabi). 4-daraja bo'laklar faqat 3-daraja yozuvining bolalari sifatida → **≤ 4 kesim darajasi**, har bo'lakda **≤ 20**
  kesim (ildizda ham — yozuvda 20 ta joy).
* **Qoldiq** = `o'lcham − siljish − Σ (cut + kerf) × takror`, manfiy bo'lsa 0. `o'lcham`: ildizda — **list uzunligi**, 1-daraja
  bo'lakda — **list eni**, chuqurroqda — ota o'lchami. (Karta list eni bo'ylab polosalangan bo'lsa ham shunday: namunada ildiz
  qoldig'i 930 = 2750 − 1820, 1-daraja qoldig'i 0.)
* Delovoy qoldiq bo'lagi `.qk` ga yozilmaydi (faqat `.lbd` da).

## 3. Bo'laklar tartibi
* 1-daraja **list uzunligi** bo'ylab (burilmagan karta): KS33X bilan bir xil — 1-daraja teskari tartibda, qolganlari o'z tartibida.
* 1-daraja **list eni** bo'ylab: karta 90° burilgandek — 1-daraja o'z (geometrik) tartibida, 3-daraja (yana list eni bo'ylab)
  **teskari**, 2- va 4-daraja o'z tartibida. Namuna: 2-karta `459 → [448, 426→380]` fayllarda `[426, 448]`,
  `350 → [100×3, 100]` → `[100, 100×3]`.

## 4. `.lbd`
KDT «yangi versiya» (`kdt_new`) bilan bir xil tuzilma (oxirida `00`, CSV 2-maydon — kartadagi soni); daraxt 3-bo'limdagi
tartibda, etiketka qatorlari — xesh-jadval tartibida (savat ichida daraxtda birinchi uchrash tartibi). Avvalgi dasturning
etiketka blobi (CSV 31-maydon) yozilmaydi. Burilmagan kartada `.lbd` `kdt_new` niki bilan bayt-ma-bayt bir xil.

## 5. Noaniq joylar
1. Yozuvdagi `int32 1` va `uint8 1` — doimiy deb olindi (namunada karta nusxasi 1; nusxalar soni bo'lishi mumkin).
2. 3-bo'limdagi tartib va qoldiq qoidasi bitta namunadan (2 ta «en bo'ylab» karta, 1 ta «uzunlik bo'ylab»); delovoy qoldiq
   bo'lagi bor karta namunada yo'q.
3. Etiketka qatoridagi indeks (`idx`) — onlayn tizimda loyiha faylidagi detal `id`; bizda — detal uid (1…N). Xesh-jadval
   tartibi shu kalitga bog'liq (stanok uchun ahamiyati yo'q deb hisoblandi).
