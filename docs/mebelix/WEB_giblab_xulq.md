# WEB. GibLab xulqi bo'yicha ochiq savollarga javoblar (2026-10-04)

Maqsad: `U_OCHIQ_SAVOLLAR.md`, `postprocessors/README.md`, `V_ONLAYN_SOLISHTIRISH.md` dagi funksional savollarni yopish.
Matn o'z so'zlarimiz bilan yozilgan; iqtiboslar 15 so'zdan qisqa.

**Manbalar.**
- **H** — lokal yordam sahifalari `GibLabLocal\pages\help\**` (faqat ma'nosi o'qildi).
- **P** — korxonaning o'z `.project` fayllari (`giblab project\**`, 3 508 ta CS, 3 ta CL, 43 439 ta XNC operatsiya; faqat XML atributlari, `data` blobi ochilmadi).
- **S** — postprotsessor namunalari `post prtsessorlar\PILNIY APPARAT\**`.
- **W** — ochiq internet. `giblab.com` sahifalari skript bilan chiziladi (matn olinmadi); promebelclub.ru va informdom.com 403 qaytardi.
  O'qilganlari: `service.giblab.com/help/datasheet_ru.html` va yordam ko'zgusi `raskroy.fairtech-marketing.com/operations/cs_ru.html`.

Ishonch: **yuqori** — hujjat va fayllar bir-birini tasdiqlaydi; **o'rta** — bitta manba yoki bilvosita dalil; **past** — taxmin.

---

## 1. Postprotsessordagi torsovka = loyiha torsovkasi + propil

**JAVOB (yuqori).** Ha. GibLab'da «Торцовка» qiymati propilni o'z ichiga olmaydi; stanokka `cTrim + swSawthick` yoziladi.
Buni arra (stanok) xossasi `swTrimIncludeSaw` boshqaradi: `false` — torsovkaga propil qo'shiladi, `true` — torsovka propilni o'z ichiga olgan deb hisoblanadi.

**Dalil.**
- H `operations/cs_ru.html`: «Значение не включает толщину пилы»; misol: foydali o'lcham = `1000 − (20+10)·2 = 940`.
- P: 2 214 ta arra yozuvining hammasida `swTrimIncludeSaw="false"`; odatiy to'plam `cTrimL=cTrimW=2`, `swSawthick=3` (2 202 ta).
- S, arra 3 mm (3151): Holzma PTX `MATERIALS,…,16,2,3,3,5,5,5,5`; KDT XML `saw="3"`, `trim="5"`.
- S, arra 6 mm (3159, `cTrim=2`): PTX `MATERIALS,…,16,2,6,6,8,8,8,8`, `CUTS,…,90,8`; KDT XML `saw="6"`, `trim="8"`. Demak 2 + 6 = 8 — taxmin tasdiqlandi.
- S, Giben G57: xom qiymat alohida yoziladi — `RIFILO3/4 = 2000` (2 mm), `SPESSORELAMA = 3000 / 6000`. Ya'ni bu formatda propil qo'shilmaydi, stanok o'zi qo'shadi.

**Qaysi sozlamalar.**
- Loyiha darajasi: arra xossasi `swTrimIncludeSaw` (bizda `CSCutParams.trim_includes_kerf`, `models.py:225`).
- Postprotsessor darajasi (onlayn ko'rikdan, `giblab_inventory/06_online_korik.md` §2): SCM WinCut — «propil hisobi bilan torsovka (ha)» va «U/V kesimlarda torsovka (0)»;
  KDT-PreSize QK — «propilni torsovkaga kiritish (ha)», «uchinchi burilishdan boshlab torsovka (0)»; Shelling MCS — «uchinchi burilishdan boshlab torsovka (0)»;
  Homag CHF — «Z/W kesimlarda torsovka (0)». Yordamda bu parametrlarning ta'rifi yo'q (postprotsessor sahifalari deyarli bo'sh).

**Qo'shimcha kuzatuv (KDT XML, `layer ≥ 3` da `trim="2.5"`).** Arra 6 mm bo'lganda ham 2.5 — demak propilga bog'liq emas.
Ichki polosalarda `polosa uzunligi − Σdetal − propil·(n−1)` eng kichik qiymati aynan 5 (= `swMinPruning`), boshida 2.5 va oxirida 2.5.
Taxmin (past): 2.5 = `swMinPruning / 2`. Barcha loyihalarda `swMinPruning=5`, shuning uchun boshqa qiymat bilan tekshirib bo'lmadi.

**MebeliX uchun.**
- Mantiq to'g'ri, o'zgartirish shart emas: `optimizer.py:617` (`add = 0 if p.trim_includes_kerf else p.kerf`), `ppfmt/saw_holzma_ptx.py:237-239`, `biesse_nc300.py:39`, `felder_format4.py:48`, `scm_maestrocut.py:48`, `saw_holzma_lc4.py:282`, `_saw_strips.py:173`.
- Tekshirish kerak: `ppfmt/saw_nanxing_ncp.py:38` da `tail_trim: float = 5.0` standart qiymati qattiq yozilgan — chaqiruvda doim `trim + kerf` uzatilayotganiga ishonch hosil qiling (arra 6 da 8 chiqishi kerak).
- `ppfmt/saw_kdt_xml.py:92-93`: chuqur qatlamda bizda 0, GibLab'da 2.5. Stanok uchun xavfli emas, lekin fayl GibLab bilan bir xil bo'lishi uchun optimizator ichki polosani `swMinPruning` ga kengaytirib, mazmunni o'rtaga qo'yishi kerak bo'ladi (4-savolga qarang).
- README dagi «TrimSize=5 / Sx=Sy=5 / T=5 manbai» savollari yopildi: 2 + 3.

## 2. XNC ifoda tili: `sin(90)` va `7/2`

**JAVOB (yuqori — hujjat bo'yicha; amalda sinalmagan).** Burchak **radianda**. Ikkala operand butun bo'lsa, bo'lish natijasi ham **butun** (`7/2 = 3`); bitta operand haqiqiy bo'lsa — haqiqiy (`7/2.0 = 3.5`).

**Dalil.**
- H `expression/fuctions/mathFunctions.html`: `sin`, `cos`, `tan` — «угла в радианах»; misol `sin(pi) = 1.22E-16`, `cot(90) = -0.50` (faqat radianda shunday).
- H `expression/mathExpression.html`: butun operandlarda «деление дают значение … целочисленного типа».
- H `format_ru.html`: XNC atributlari turi `Expression` — o'sha umumiy ifoda tili.
- P: 43 439 ta XNC dasturida `sin/cos/tan` ham, son/son bo'lish ham **bir marta ham uchramadi** — xodimlar ishlatmaydi.

Yana shu sahifadan: `round(2.5)=3`, `round(-1.5)=-1` (yarim — yuqoriga); `ceil/floor` haqiqiy son qaytaradi (`ceil(12)=12.0`); `%` — butun bo'lish qoldig'i; `^` — daraja.

**MebeliX uchun.** `backend/app/services/xnc.py:99` `XNC_DEGREES = False` — to'g'ri, qoldiriladi. `expr.py:519` dagi `round` (yarim +∞ ga) yordamga mos. U-ro'yxatdagi A1 yopildi.

## 3. Qirra (gorizontal) teshigi: `z` va `m`

**JAVOB.**
- `m` (**yuqori**): «qalinlik o'rtasida». Standart `true`. `m=true` bo'lsa teshik `dz/2` balandlikda, `z` e'tiborga olinmaydi.
- `z` (**o'rta**): `m=false` bo'lganda Z bo'yicha koordinata. Yordamda qaysi yuzadan o'lchanishi yozilmagan. Namunalarga ko'ra Homag va TPA fayliga `dz − z`, SCM Startech fayliga `z` yoziladi. Bu stanoklar balandlikni stoldan (pastdan) o'lchasa, XNC `z` **lits (yuqori) yuzadan** o'lchanadi — lekin buni hujjat tasdiqlamaydi.

**Dalil.**
- H `format_ru.html`, `<bl>/<br>/<bt>/<bb>`: `z` — «Координата Z / Смещение по Z»; `m` — «Середина по Z. По умолчанию: true».
- P: 99 % teshik `m=true, z=dz/2` (masalan `z=8, dz=16` — 99 110 ta). `m=false` kam: `z=8, dz=18` — 157 ta, `z=7.5, dz=16` — 38 ta va h.k.
- S (bizning tahlil): `homag-woodwop-v6.md` §2.5 va `tpa-genesis-evolution-8-9.md` — `m=false, z=8, dz=18` → `ZA=10` / `#2=10`.

**MebeliX uchun.** Postprotsessorlardagi `m → dz/2`, `m=false → dz − z` (Homag/TPA) qoidasi qoladi. UI yorlig'ini «Z (lits yuzadan)» deb qat'iy yozmang — «JAVOB TOPILMADI» ro'yxatiga qarang. Tekshirish usuli: 18 mm detalda `z=5, m=false` teshikni stanokda parmalab o'lchash.

## 4. «Минимальная обрезка» va «Минимальный размер детали»

### 4a. Минимальная обрезка (`swMinPruning`)
**JAVOB (o'rta).** Qoida — **(qoldiq + propil) ≥ min**, ya'ni polosa uzunligi minus detallar va ular orasidagi propillar yo 0, yo `swMinPruning` dan kichik emas. Toza tilim (propildan keyin qolgani) `min − propil` bo'lishi mumkin: propil 3 / min 5 da **2 mm li tilim chiqadi**.

**Dalil.**
- H `cs_ru.html`: parametr 0…5 mm obrezkada detal siljishi yoki arra qizishi uchun; «большим, чем толщина самой пилы» qo'yish tavsiya qilinadi (demak qiymat propilni o'z ichiga oladi).
- H `format_ru.html`: `swMinPruning` — 0 bo'lsa cheklov ishlamaydi; standart 0.
- S, KDT XML 10 ta fayl, ichki (3-qatlam va chuqurroq) 230 ta tugun: ortiqcha uzunlik `E = l − Σcut − saw·(n−1)` hech qachon 0 < E < 5 emas; aynan 5 — 51 marta, 6 — 10, 7 — 2, 8 — 9.
- S, 3159 (arra **6**): polosa 2400 = 564 + 6 + 1825 + **5**. Ortiqcha 5 propildan (6) kichik — demak 5 ga propil kiradi, «toza qoldiq ≥ 5» qoidasi emas.

### 4b. Минимальный размер детали (`cMinDimDetail`)
**JAVOB (o'rta).** Kichik detal kroyga **kirmaydi** (faqat ogohlantirish emas).

**Dalil.**
- H `format_ru.html`: `cMinDimDetail` — «Мин. размер детали», bo'lim «Ограничения раскроя»; ta'rif yo'q.
- P: `cMinDimDetail=30` bo'lgan loyihalarda 30 mm dan kichik tomoni bor detal 6 ta (4 operatsiya: 20×2190, 1×1, 10×10 …). To'rttala operatsiyada kroy natijasi yo'q, `usedCount=0`. Umumiy fonda natijasiz CS operatsiyalar ulushi 12 % (275 / 2 211) — tasodif ehtimoli juda kichik.
- Cheklov: bu operatsiyalarda **faqat** kichik detallar bor; «aralash» holat (katta + kichik) namunasi yo'q.

**MebeliX uchun.**
- `validate.py:109` `_check_trim` (`TOL < rest < mt` — xato; `rest` propilni o'z ichiga oladi) — to'g'ri, o'zgarmaydi. A2 yopildi: 2 mm li tilim chiqadi.
- `calc.py:74,192` (kichik detal kroyga kirmaydi + ogohlantirish) — to'g'ri, A3 yopildi. Standart `models.py:206` = 30 korxona fayllariga mos.
- Farq: GibLab ichki polosani mazmundan aynan `swMinPruning` ga katta qilib kesadi (51 holat). Bizning optimizator 0 qoldiq bilan ham joylaydi — GibLab kartalariga yaqinlashish uchun `optimizer._shrink_size` (484-497-qatorlar) atrofida ko'rib chiqish mumkin; majburiy emas.

## 5. (SP) Обработка поверхности: material Длина/Ширина/Толщина va «Площадь материала»

**JAVOB (past).** Hujjatda SP uchun alohida yordam sahifasi **yo'q**, korxona fayllarida ham SP operatsiya **yo'q** (0 ta). Format ta'rifida SP hisobiga kiradigan atributlar faqat beshta: `spCalcMat`, `spWastePRC`, `spRestSide`, `spSizeMode`, `spCost`. Material o'lchamlari ular orasida yo'q — ya'ni Длина/Ширина/Толщина material (tovar) xossasi bo'lib, formulada qatnashishi tasdiqlanmagan. «Площадь материала» formulasi topilmadi.

**Dalil.**
- H `format_ru.html`, SP: `spRestSide` — «Длина остатка по краям»; `spSizeMode` — «-1=пильный размер; 0=заготовки»; `spCost` — narx 1 m² uchun.
- O'xshash operatsiya EL (H `el_ru.html`): 1000 mm tomonda qoldiq 20 bo'lsa sarf `1000 + 20·2 = 1040` — qoldiq **har ikki chetda**; foiz — qo'shimcha sarf.

**MebeliX uchun.** Hozirgi model o'zgarmaydi: `sp_ops.py:22` `REST_BOTH_EDGES = True` (EL ga o'xshash, har chetda `r`), `models.py:365` `SP_DEFAULT_SIZE_MODE = -1`, material sarfi `calc.surface_usage` (`(L+2r)·(W+2r)·tomonlar·soni·(1+%)`). `SPParams.length/width/thickness` — faqat ma'lumot sifatida qoladi. Korxona SP ishlatmaydi → ustuvorlik past.

## 6. (CL) Pogonaj: maqsad, «Длина делового остатка», «по полосам» yaxlitlash

**JAVOB.**
- **Optimallashtirish maqsadi (past):** yordamda yozilmagan. Faqat «расчет и оптимизация погонажных раскроев» deyilgan.
- **F foizi maxraji (yuqori):** detallar uzunligi / ishlatilgan polosalarning to'liq uzunligi.
- **«Длина делового остатка» (`cBusinessWaste`) (yuqori):** birligi **metr**, standart 1 m. Shu uzunlikdan uzun qoldiq «деловой» bo'ladi va material sarfiga kirmaydi.
- **Qoldiq uzunligi (yuqori):** `cTrimWaste=true` bo'lsa torsovkasiz: `L − 2·(torsovka + propil) − Σdetal − propillar`.
- **«По полосам» (o'rta):** `cCostByItem=true` — material narxi polosa uchun (aks holda metr uchun). `cCostByItemRound`: 11 — butun polosagacha; 32 / 33 / 34 — uzunlik bo'yicha 1/2, 1/3, 1/4 polosagacha yaxlitlash.
- **Dastlabki (kroygacha) hisob (yuqori):** material = detallar uzunligi × (2 − `cCPF`).
- **Kratnost (yuqori):** CS bilan bir xil — paket balandligi / material qalinligi.

**Dalil.**
- H `cl_ru.html`: «Минимальная длина отхода … не будет учитываться в расходе материала»; narx asoslari 4 ta (torsovkali kesim, torsovkasiz kesim, material uzunligi, detallar uzunligi).
- H `format_ru.html`, CL: `cBusinessWaste` — «По умолчанию: 1м»; `cCostByItemRound` qiymatlari 11/32/33/34; `cost` — «за метр … или за полосу».
- P `5000_kupe.project` (yagona hisoblangan CL): 4 × 1948 mm, polosa 3200, torsovka 10, arra 3 → `cPartAmount=7.792`, `cMaterialAmount=12.8`, `cFilling=0.60874` (= 7.792/12.8); `cWasteAmount=4.892` (= 4 × 1223; 1223 = 3200 − 13 − 1948 − 3 − 13); `cMaterialAmountP=8.5712` (= 7.792 × 1.1); `cBusinessWaste=10` → деловой qoldiq 0.
- P: shu faylda `cTrimCountP=4`, `cTrimLengthP=0.172` (= 4 × 43 mm) — amalda detalga **1** kesim, yordamda «2 kesim» deyilgan.

**MebeliX uchun.** `cl_calc.py` dagi `price_by_strip` va `rounded_strip_count` (11/32/33/34) format ta'rifiga mos. `cBusinessWaste` ni metr deb o'qish to'g'ri. `cl_calc.py` da torsovkali/torsovkasiz kesim uzunligi bor — mos. B8 dagi «CL korxonada ishlatiladimi» — 3 508 CS ga 3 ta CL: ishlatilmaydi desa bo'ladi.

## 7. Paket (book/stack): «Высота пакета», «Кратность», «Большой пакет»

**JAVOB.**
- **Kratnost (yuqori):** `⌊Высота пакета / material qalinligi⌋`, kamida 1. Bitta paketga shundan ortiq list tushmaydi.
- **Paketlar soni (yuqori):** `cCountPackets ≥ ⌈listlar / kratnost⌉`; faqat **bir xil kartali** listlar paketga birlashadi (har karta alohida, nusxalari kratnost bo'yicha bo'linadi).
- **«Большой пакет для серийного производства» (o'rta/past):** 2021-yil martda qo'shilgan; shu yangilanishda «Процент заполнения для кратности» olib tashlanib, avtomatik hisoblanadigan bo'lgan. Aniq algoritm hujjatda yo'q. Taxmin: optimizator bir xil kartalarni to'liq paketgacha takrorlashni afzal ko'radi.

**Dalil.**
- H `cs_ru.html`: «кратность = высота пакета / толщина материала»; to'ldirilish foizi chegaradan yuqori bo'lsa listlarni paketga birlashtirishga harakat qiladi.
- H `update_ru.html` (12.03.21): «Добавлен параметр "Большой пакет для сирийного производства"»; «Удален параметр "Процент заполнения для кратности"».
- P: 1 925 ta hisoblangan CS da `packets ≥ ⌈sheets/⌊40/t⌋⌉` **0 ta buzilish**. `t=26/30/40` (kratnost 1) da doim `packets = sheets` (112 ta). `t=16` da 1 241 tadan 946 tasida `packets = sheets` — turli kartalar birlashtirilmaydi.
- S Holzma PTX: `MATERIALS` da kitob maydoni 2 (`t=16`, paket 40); 3156: 8 list → 7 ta `PATTERNS`, bittasi `run=2`; loyihada `cMaterialCount=8`, `cCountPackets=7`.
- P: hamma CS da `cPrefLargePacket="true"`, `swPackageHeight="40"`, `cFillRep="0.9"` (fayl eski atributni hali ham saqlaydi).

**MebeliX uchun.** `prefer_big_pack` (`models.py:237`, standart `True`) va «faqat bir xil kartalarni takrorlash» (`optimizer._job_key`) korxona fayllariga mos; Q-12 («turli kartalar bitta paketga birlashadimi») — **yo'q**. Holzma README savoli «book = ⌊swPackageHeight/t⌋» tasdiqlandi.

## 8. «Объединение деталей», «Группировка деталей по свойствам», «Сохранение чертежа карт кроя»

**JAVOB.**
- **«Сохранение чертежа карт кроя» (`cSaveDrawCut`) (o'rta/yuqori):** yoqilsa loyiha fayliga ikkilik `data` dan tashqari o'qiladigan XML `draw` atributi ham yoziladi (kartalar, kesimlar, detallar, qoldiqlar koordinatalari bilan). Tashqi dasturlar uchun. Standart `false`. Kroyning o'ziga ta'sir qilmaydi.
- **«Объединение деталей» (`cCombiningParts`) (past):** hujjatda ta'rif yo'q. Fayl atributi — mantiqiy, standart `false`. Taxmin: bir xil o'lchamli detallarni optimizatsiyada bitta pozitsiyaga birlashtirish.
- **«Группировка деталей по свойствам» (`cGroupParts`) (past):** butun son, hamma faylda `0`. Qaysi xossalar tanlanishi — topilmadi.
- Adashtirmang: detal xossasidagi «Группировать в блок» (`groupInBlock`: 0 — yo'q, 1 — uzunlik, 2 — kenglik bo'yicha, min/max soni) — bu boshqa narsa va hujjatlangan.

**Dalil.**
- H `format_ru.html`: `cSaveDrawCut` — «Сохранение чертежа карт кроя. По умолчанию: false»; `draw` — «Рисунок карт кроя», teglar `p` (karta), `c` (kesim), `d` (detal), `r` (qoldiq).
- P: 2 211 ta CS ning hammasida `cCombiningParts="false"`, `cGroupParts="0"`, `cSaveDrawCut="false"` — **xodimlar uchalasini ham ishlatmaydi**.
- H `update_ru.html` (20.05.25): KDT XML postprotsessorida bir xil o'lchamli detallarni birlashtirish — paketli kroyda etiketka to'g'ri bosilishi uchun (boshqa joydagi o'xshash tushuncha).

**MebeliX uchun.**
- `models.py:245` `save_drawings: bool = True` → standartni **`False`** qiling (GibLab standarti va korxona fayllari), `plugins/legacy_project.py:411` dagi zaxira qiymat ham `False`. Ma'nosi: `.project` eksportida `draw` yozish-yozmaslik (`project_export.py`); hozircha `draw` yozilmasa, belgini «faqat eksport uchun» deb izohlang.
- `merge_parts` (`models.py:244`, `False`) va `group_props` — optimizatorga ulash shart emas; UI'da o'chiq holda qolsin (CS-020/021 ustuvorligi past).

## 9. «Общие действия» → «Оптимизировать операции»

**JAVOB TOPILMADI.** Yordam sahifalarida bu buyruqning ta'rifi yo'q; internetda ham topilmadi.

Yaqin ma'lumot (H `update_ru.html`, 20.08.03): «Общие действия» ga ikkita buyruq qo'shilgan — bir xil kodli va bir xil material nomli operatsiyalarni birlashtirish; kromkalash operatsiyalarini kroy materiallari bo'yicha ajratish.

**MebeliX uchun.** `main.py:1109` `optimize_operations` (bo'sh CS / ishlatilmagan EL va XNC ni olib tashlash, bir xillarni birlashtirish, tartiblash) — taxminga asoslangan; o'zgartirmang, lekin onlayn GibLab'da test loyihada bosib, oldin/keyin operatsiyalar ro'yxatini solishtiring. Alohida «birlashtirish» va «kromkani material bo'yicha ajratish» buyruqlari GibLab'da bor — bizda birinchisi `main.py` `_merge_same`; ikkinchisi `optimize_operations` dan oldingi funksiyaga o'xshaydi (tekshirilmadi).

## 10. Arra stanoklari uchun etiketka ma'lumoti va GibSaw roli

**JAVOB (o'rta).**
- Fayllardagi etiketka bloblari va `GibLabData.<ID>.xml` **kesish uchun kerak emas**. Ularni stanok kompyuteriga o'rnatiladigan GibLab «модуль печати этикеток» (`PrintLabel.exe`, shablon `print\part.lbl`) o'qiydi; u stanok dasturi (CadMatic, WinCut …) papkasida turadi va detal kesilganda etiketka bosadi.
- Modul o'rnatilmagan stanokda bu ma'lumot ishlatilmaydi; stanokning o'z etiketka tizimi bo'lsa, u formatning o'z maydonlarini (PTX `PARTS_UDI`, Maestro `Campo…`, Nanxing `F1…F20`) oladi.
- **GibSaw** — alohida dastur: ChPU'siz format-kesish stanogi yonidagi sensorli ekran. Kartalarni ko'rsatadi, etiketka bosadi, bajarilganini belgilaydi. Ma'lumotni o'zining alohida postprotsessori orqali oladi. Schelling/Holzma uchun kerak **emas**.

**Dalil.**
- H `labels_ru.html`: «Модуль печати этикеток на пильных центрах»; shablon joyi misollari — `D:\Cadv4x\Bin\print\part.lbl`, `C:\CAD30\print\part.lbl`, `C:\WinCut\print\part.lbl`.
- H `update_ru.html`: «постпроцессор и модуль печати для пильного центра Shelling (ShellingMCS)»; xuddi shunday Scheer, AES Alpha uchun; yangi etiketka imkoniyatlari uchun `PrintLabel.exe` va `GibSaw.exe` ni yangilash kerakligi.
- W `service.giblab.com/help/datasheet_ru.html`: «Программа для форматно-раскроечного станка GibSaw» — postprotsessorlar ro'yxatida alohida buyruq.
- S: `Shelling (MCS)` arxivida `0000.ncl` + `NNNN.ncp` (kesish) va alohida `GibLabData.<id>.xml` (150 KB, etiketka ma'lumoti).

**MebeliX uchun.** README dagi «GibLabData.xml / B_LABEL / GibLabLabel blobi / LC4 blobi majburiymi» savollari: kesish uchun **majburiy emas**. Sexdagi stanok kompyuterida GibLab bosma moduli o'rnatilganmi — shuni so'rash kerak. O'rnatilmagan bo'lsa bloblarni yozmaslik (yoki bo'sh qoldirish) xavfsiz; o'rnatilgan bo'lsa etiketkani MebeliX'ning o'z LB/ZPL oqimi bilan almashtirish rejasini tuzing. GibSaw funksiyalari — MES jamoasida (o'zgarmaydi).

## 11. Qaysi namuna faqat birinchi materialni eksport qilgan va nega

**JAVOB (o'rta/yuqori).** Bu postprotsessor xususiyati **emas** — namunalar qanday olinganiga bog'liq. Postprotsessor CS operatsiyaning «Раскрой» yorlig'idan ishga tushadi va **bitta operatsiya (= bitta material)** ni chiqaradi.

**Dalil.**
- H `cs_ru.html`: «Постпроцессор (Конвертация в формат пильной станции)» — «Раскрой» yorlig'idagi amal.
- S: **31xx** to'plami (3151–3161, 3167–3182) — **barcha** stanok papkalarida buyurtmaga 1 ta fayl, garchi loyihalarda 2–10 ta CS bo'lsa ham (AES Alpha, Biesse NC300/OSI, Felder PC6/PC7, Giben G57/GDrive/GVisionXP, Holzma/2/3, HOMAG, KDT XML/KS33X/«Новий версия», Nanxing CutSaw/NXCutSAW, SCM MaestroCut/WinCut, Shelling).
- S: **20xx** to'plami (2027–2037) — barcha materiallar: AESS Alpha (SS), FastPanel, Nanxing (NXCutSaw) — buyurtma papkasida 2–3 fayl; Nanxing (CutSawFG) va Shelling (MCS) — boshqa materiallar ichki zip (8 va 10 ta); HOMAG CHF NPS400 — bitta zip.
- Fayl nomi `<loyiha>_<material>` — yordamdagi standart shablon `project.name + ' ' + operation.name` ga mos (H `postprocessors/HolzmaPTX_…html`).
- S: ichki zip yozuvining vaqti (19:47) tashqi a'zolarnikidan (16:47) farq qiladi — ichki arxivlar alohida bosqichda qo'shilgan.

**MebeliX uchun.** README dagi «nega faqat 1-material» (Nanxing CutSaw, NXCutSAW, G57, GDrive, KDT XML, KS33X) savollari yopildi: stanok cheklovi yo'q. Eksport operatsiya bo'yicha qoladi (`api_export.py`), ustiga «loyihadagi barcha CS» varianti: zip chiqaradigan formatlarda boshqa materiallar ichki zip, oddiy fayllarda alohida fayllar (GibLab 20xx namunalaridagi kabi). 8 belgili nom to'qnashuvi (Selco NC300, GDrive) shu rejimda hal qilinishi kerak.

---

## Yo'l-yo'lakay topilgan narsalar
- **Format ta'rifida yo'q, lekin fayllarda bor atributlar:** arra — `swTrimIncludeSaw`, `swSawthickDiv` (doim −1); CS — `cMaxPartsOnPattern` (doim 0), `cPrefLargePacket`, `cCombiningParts`, `cGroupParts`, `cSortPatterns`, `cAllowanceWorkpiece`.
- **Eski fayllarda qiymatlar o'rni almashgan:** 1 367 ta CS da `cCostByItem="1"` va `cCostByItemRound="false"` (844 tasida to'g'ri: `true` / `11`). Importer (`plugins/legacy_project.py`, `_round_code`) ikkala ko'rinishni ham to'g'ri o'qishini testlang.
- **Korxona standartlari (P):** `swMaxturns` 4 — 1 898 ta, 6 — 152, 3 — 116, 5 — 48 (B1: yangi CS uchun 4 qilish asosli); `cMinDimRegWaste1/2 = 1000/500`; `cBusinessWaste = 0.5` m²; `cTrimWaste = true`; `swPackageHeight = 40`.
- **CS narx asoslari (H):** kesim uzunligi (paketdagi listlar soniga ko'paytiriladi), detallar perimetri, material maydoni (деловой qoldiqsiz), detallar maydoni. Dastlabki sarf = detallar maydoni × (2 − hisobiy foiz/100).
- **«Торцовка остатков»** 2020-yilda «Размер остатков с учетом торцовки» deb qayta nomlangan (H `update_ru.html`).

## JAVOB TOPILMADI
1. **«Оптимизировать операции»** ning aniq ta'siri (9-savol) — hujjatda ham, internetda ham yo'q. Onlayn GibLab'da sinash kerak.
2. **«Объединение деталей» va «Группировка деталей по свойствам»** ning aniq algoritmi va xossalar ro'yxati (8-savol). Korxona ishlatmaydi.
3. **SP «Площадь материала» formulasi** va material Длина/Ширина/Толщина ning hisobdagi roli (5-savol) — SP yordam sahifasi yo'q, namuna yo'q.
4. **CL optimizatorining maqsadi** (kam polosa / kam chiqit / uzun qoldiq ustuvorligi) (6-savol).
5. **XNC `z` qaysi yuzadan o'lchanadi** (3-savol) — faqat bilvosita xulosa; stanokda bitta sinov teshigi bilan aniqlanadi.
6. **«Большой пакет» ning aniq algoritmi** (7-savol) — faqat nomi va qo'shilgan sanasi ma'lum.
7. **KDT XML `trim="2.5"`** — `swMinPruning/2` ekani taxmin; boshqa `swMinPruning` qiymatli namuna kerak.
8. **Postprotsessor sozlamalarining ta'riflari** («U/V kesimlarda torsovka», «uchinchi burilishdan boshlab torsovka» va h.k.) — yordam sahifalari bo'sh.
9. **«Минимальный размер детали» aralash holatda** (katta va kichik detallar bitta operatsiyada): kroy bajarilib, kichiklar tashlab ketiladimi yoki butun kroy to'xtaydimi — namuna yo'q.
10. `sin(90)` / `7/2` **amalda** sinalmadi (faqat hujjat); korxona dasturlarida ishlatilmaydi.
