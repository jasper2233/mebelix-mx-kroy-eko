# Postprotsessorlar: savollar holati (2026-10-04, onlayn solishtiruvdan keyin)

Manbalar: korxona namunalari (`post prtsessorlar/`), `.project` fayllar, internet tadqiqoti
(`WEB_homag_holzma_schelling.md`, `WEB_biesse_scm_felder_tpa.md`, `WEB_asia_formats.md`, `../WEB_giblab_xulq.md`).

## Javob topilgan (yopildi)
| Savol | Javob | Manba |
|---|---|---|
| Stanok fayllarida torsovka 5 mm (loyihada 2) | torsovka = loyiha torsovkasi + arra qalinligi (arra 6 da 8) | 3159 namunasi; PTX spetsifikatsiyasi («trim includes saw kerf») |
| Paket (book) | ⌊paket balandligi / qalinlik⌋; PTX `QTY_CYCLES = ⌈listlar / paket⌉` (tuzatildi) | Cut Rite PTX V1.14; 1 925 kroy |
| Etiketka bloblari / `GibLabData.xml` stanokka kerakmi | Kesish uchun kerak emas — alohida etiketka bosish dasturi o'qiydi; Schelling: `F 06` bo'lmasa standart etiketka | Schelling NC data format 4.12; yordam sahifalari |
| «Faqat 1-material» | Postprotsessor bitta CS operatsiyadan ishlaydi (bizda ham) | 20xx / 31xx namunalari |
| XNC ifodalari | radian; butun÷butun = butun | yordam sahifalari |
| «Минимальная обрезка» | (qoldiq + propil) ≥ min | 230 ichki tugun (KDT XML) |
| PTX `FUNCTION` kodlari, `OFFCUTS`, `BOARDS.INFORMATION` | 0 bosh, 1 uzunasiga, 2 ko'ndalang, 3–9 qayta kesim, 90+ trim; INFORMATION — erkin matn | Cut Rite PTX V1.14 |
| Homag NPS400 daraja kodlari | 1 bosh, 2 rip, 3 cross, 7 recut, 9 notekis recut; maks. 5 daraja | Magi-Cut yordami |
| woodWOP freza korreksiyasi | WRKL = chap, WRKR = o'ng; XNC C=1 (ekranda «справа», Y pastga) → stanokda chap | MPR4x format |
| TPA: `#40`, `#36`, `#8514/#8515`, qirra teshigi balandligi | 1 chap / 2 o'ng; korreksiya radiusi; mashina/guruh; ostki yuzadan (`dz − z` to'g'ri) | TpaCAD qo'llanmasi |
| BiesseWorks BPP konstantalari | BG `32,32,50,45` = DX, DY, R, DA; CUT_G `<W>` = paz eni; ARC DIR 1 = CW | BppLib |
| Daron `.ban` | `Grain`: DIR_NONE / DIR_HOR / DIR_VER; `SlotA` — soat miliga teskari; Outline — tashqi kontur | MicroDraw BAN V3.0 |
| KDT / Nanxing torsovka qiymatlari | format konstantasi emas — postprotsessor sozlamasi | BAZIS-Раскрой qo'llanmasi |

## Onlayn solishtiruv (2026-10-04, bitta loyiha — 35 detal, 3 list, 36 XNC dastur)
Bir xil loyiha ikkala tizimda ishga tushirildi; fayllar yonma-yon solishtirildi (kroy kartalari har tizimda o'ziniki).

**Prisadka (XNC) — 10 format, 325 fayl:** Xilog v3, WoodWOP, BiesseWorks, TPA, KDT/WDX, HIRZT, Startech — bayt-ma-bayt bir xil
(217 fayl); XDWoodCam, Syntec, Daron — faqat dastur nomi / vaqt / loyiha nomi farqi (100 fayl); 4 ta yoyli frezali detalda
Syntec va Daron'da oxirgi kasr raqam farqi (1e-5 mm, 1e-14°) — amalda ahamiyatsiz. Solishtiruvdan topilib tuzatilgani:
* yoy detal chetini kesgan joyda aniq kesishuv + yoy bo'lagini qayta bo'lish (`_cnc2.cut_poly`);
* Syntec: yarim — yuqoriga yaxlitlash (240.6865 → 240.687);
* BiesseWorks `ROUT`: kontur yoy bilan boshlansa `TIN, AIN = 1, 88` (to'g'ri chiziqda `9, 0`).

**Arra — 18 format:** qator shablonlari bo'yicha PTX, LC4 (35/35 detal qatori), Giben G57 / GVisionXP, KDT XML, KS33X, KDT `.qk`
(fayl hajmi bir xil), Nanxing CutSawFG / NXCutSaw, Shelling MCS, Homag CHF, SCM WinCut / MaestroCut, Biesse OSI, Felder PC6 / PC7,
AES — tuzilishi bir xil. Farqlar faqat: etiketka bloblari (ko'chirilmaydi), dastur nomi, loyiha nomi maydoni.
Yangi: **Felder F4Classic** generatori (namunadan), AES kromka nomi boshidagi bo'sh joy saqlanadi.

**Sozlama mos kelmasa:** onlayn tizim FastPanel uchun «Макс. количество вращений ≤ 3» deb xato beradi — bizda kroy shu cheklov
bilan avtomatik qayta bajariladi (`ROT_LIMIT`, sarlavha `X-PP-Refit`, foydalanuvchiga xabar). Qoldiqlar omborga yozilgan bo'lsa —
avtomatik emas, tushunarli xabar.

**Onlayn tizimda ochilmaganlar** (brauzerning tizim oynasi chiqadi, avtomatik sinab bo'lmadi): Holzma CadMatic v3, Giben GDrive,
Biesse NC300, Scheer, Masterwood MW310. Versiya tanlash oynasi bor: KDT `.qk` (V1.4.0P / V6.3.2P / V3.3.0P / V4x old),
FastPanel (2.1.4 / 2.1.5) — bizda bittadan (namunadagi) versiya.

## Foydalanuvchi javoblari va 2-bosqich tadqiqot (2026-10-04 kech)
**Qarorlar (foydalanuvchi):** (1) tizim universal — hamma model va versiyalar qo'shiladi; (2) fayllarga **joriy loyiha nomi** yoziladi
(mahsulotdagi eski buyurtma matni emas — `ppfmt.order_text`); (3) etiketka arra yonida «GibSaw» tizimi orqali chiqadi, MES da bu
qism bor (hozir chek chiqadi) — arra fayllariga begona etiketka bloblari kerak emas; (4) har stanok o'z asboblari bilan —
«Инструменты» jadvali (`ppfmt/tooling.py`, `GET/PUT /postprocessors/machines/{key}/tools`, sozlamalarda jadval).

**Onlayn tizimdan aniqlangani:**
* Qotib qolish sababi — brauzerning tizim oynalari: «Введите 8-символьное имя программы для пильной станции» (CadMatic v3, GDrive,
  NC300, Scheer; standart — loyiha nomining lotincha 8 belgisi) va ogohlantirishlar («Номер инструмента не указан!»,
  «Наименование не должно быть пустым!»). Avtomatik javob bilan hammasi yuklab olindi (namunalar — `post prtsessorlar/ONLINE_2026-10-04/`).
* Burilish chegaralari: **Scheer ≤ 3**, **FastPanel 2.1.5 ≤ 3, 2.1.4 ≤ 2** (`ppfmt.rot_limit`; FastPanel versiyasi — stanok sozlamasi).
* KDT `.qk` versiyalari: **V6.3.2P = V1.4.0P** (bayt-ma-bayt; `kdt_new`), **V4.x (old) = KS33X v4.4** (`kdt_ks33x`),
  **V3.3.0P — boshqa format** (o'zgaruvchan uzunlikdagi yozuvlar; `kdt_presize_qk`).
* Asbob talablari: MW310 va AES Sirius — har asbobga raqam; Holz-Her — frezaga raqam; IMA — frezaga nom. AES Sirius qisqichlarga
  tegadigan ishlovni rad etadi («Обработка задевает прижимы!»). Vitap Bridge — u tizimning o'zida ichki xato (namuna olinmadi).

**Internet tadqiqoti** (`WEB_biesse_tin_chk.md`, `WEB_missing_formats.md`, `WEB_tooling.md`):
* BiesseWorks `TIN/TOU`: 0 None, 1 Curve, 2 Line, 3 TgLineCurve, 5 Helix, 6–8 3D, **9 CorrectedLine**, 14 Profile3D; `AIN` — gradus,
  ma'nosi turga bog'liq. `AIN = 88` hech bir manbada yo'q (boshqa dasturlar 45 / 90 / 0 yozadi) — konstanta sifatida qoldirildi.
* Biesse Selco OSI `Chk`: stanok **tekshiradi** («programs import into OSI but cannot be run» — bitta manba), algoritm topilmadi →
  Selco uchun **NC300** tavsiya etiladi; OSI fayli «import bo'ladi, lekin ishga tushmasligi mumkin» deb belgilanadi.
* Asboblar: teshik deyarli hamma tizimda diametr + tur bilan beriladi, shpindelni stanok tanlaydi; freza va paz arrasi aniq
  raqam / nom talab qiladi; paz arrasi deyarli hamma stanokda faqat X bo'ylab. Zavod «standart diametrlari» hech bir hujjatda
  yo'q — har sexning o'z jadvali (shuning uchun jadval foydalanuvchi sozlamasi).
* NC-HOPS `.hop` va Giben `.AC` — ochiq manbalarda yaxshi hujjatlangan; KDT `.qk`, FastPanel `.ocm`, Scheer, Giben `.DAX/.CPX`,
  Felder `PR_*`, AES G-code — ochiq manbada yo'q (faqat namunadan).

## Javob topilmadi (foydalanuvchidan / stanokda sinov kerak)
1. **Qaysi stanoklar korxonada haqiqatan bor?** (sinov shu stanoklarda o'tkaziladi; qolganlari namunaga mos holda qoladi).
2. **Biesse Selco OSI `Chk`** nazorat summasi — algoritm topilmadi (yozilmaydi). Stanok tekshiradimi — sinash kerak.
3. **Namunalarda yo'q holatlar** (stanokda bitta sinov detali bilan): orqa tomonda qirra teshigi / freza; keng paz
   (TPA: `#8503` — manbada bor, sinalmagan; Xilog: `T=-1`); kirill nomlar kodlashi (hozir cp1251 / transliteratsiya);
   kasr o'lchamlar (346.5); Giben G-Drive `0xFC` bayti (589, 720, 851 … mm).
4. **Kesim darajasi chegarasi** (Holzma SPL 4, HOMAG CHF 4, HOMAG 5, KDT KS33X 4, Giben GDrive 3): dastur burilishlarni o'zi
   cheklasinmi yoki xabar chiqarsinmi (hozir — xabar).
5. **Detal raqamlari**: stanok / etiketkada GibLab'dagi eski `part id` saqlansinmi (hozir importda 1..N qayta raqamlanadi).
6. **Etiketka bosish**: arra yonida etiketka bosish dasturi ishlatiladimi? (ishlatilsa — o'zimizning etiketka chiqishimiz kerak).
7. **SCM Startech**: frezalash faylga chiqmaydi (namunada ham); arra faqat X bo'ylab — «Y bo'ylab» paz qatorlarini stanok
   qanday bajaradi.
8. **(SP)** material Длина/Ширина/Толщина hisobga qanday ta'sir qiladi («Площадь материала» formulasi).
9. **BiesseWorks `ROUT` kirish burchagi**: yoy bilan boshlanadigan konturda `1, 88` (bitta namuna) — boshqa yoylarda 88 o'zgaradimi.
10. **KDT `.qk` va FastPanel versiyasi**: korxona stanogida qaysi versiya (bizda V1.4.0P va namunadagi `.ocm`).
11. **Formatlar ichki tuzilishi topilmaganlar** (faqat namuna asosida): Holzma `.SPL`/`.LC4`, Felder `.may`, Giben `.fdt/.DAX`,
   KDT `.qk/.lbd`, Nanxing `.CUT/.ncp`, AES `.ss`, FastPanel `.ocm`, HIRZT `.pd4`, XDWoodCam `.wxf`, Syntec `.scx` — namunada
   uchramagan holatlar uchun stanokda sinov kerak.
