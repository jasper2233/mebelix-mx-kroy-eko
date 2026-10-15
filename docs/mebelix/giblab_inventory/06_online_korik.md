# 06. Onlayn GibLab ko'rigi (2026-10-02) — faqat ko'rish

Foydalanuvchi ruxsati bilan, uning Chrome oynasida kirilgan sessiya orqali ko'rildi (sozlamalar dialoglari ochilib «Отмена» bilan
yopildi; hech narsa o'zgartirilmadi, yaratilmadi, buyurtma qilinmadi). Mazmun o'z so'zlarimiz bilan yozilgan; rasmlar saqlanmagan.

## 1. Onlayn menyu (Настройки)
Hisob: parolni/emailni almashtirish. Dialoglar: «Режимы ввода деталей» (4 variant: taklif qilmaslik / zagotovka o'lchami /
detal o'lchami kromka bilan / prifugovkadan keyin kromkasiz — bizdagi bilan bir xil), «Постпроцессоры», «XNC Редактор»,
«Сохранить данные на локальный диск», «Импорт из 3D-Constructor», Dropbox (token) va uning papkalari (loyihalar, XNC shablonlari,
etiketkalar, tovarlar katalogi — Dropbox ulanmaguncha xira), «Модуль заказов», sozlamalarni `GibLabLocal.ini` ga yuklash/chiqarish.
Loyiha menyusi: Справка, Обновить, Отменить/Вернуть, Сохранить, Общие действия, Экспортировать/Импортировать, Импорт из Excel,
Импорт из других программ, **Заказать** (+ panel: buyurtma ID, narxlar). Loyiha ro'yxati ustunlari: ID, Владелец, Состояние, Дата,
Стоимость, Наименование. Onlayn build 2021-05-21; lokal 2023-05-17 (fayl `version` atributi).

## 2. Postprotsessor sozlamalari (19 stanok + «Общие»)
«Общие»: faqat «fayl nomi boshiga stanok nomini qo'shish» (bizda bor). Har stanok — parametrlar jadvali (guruh → parametr → qiymat) va
(ko'pida) «Данные для этикеток» (nom → ifoda) jadvali. Ifodalar GibLab ifoda tilida; o'zgaruvchi nomlari: `project.name`,
`material.name/code`, `product.name`, `name`, `description`, `part.id`, `length`, `width`, `detail.length/width`, `usedCount`, `waste`,
`indexInOperation`, `txt`, `ets/ebs/els/ers` (kromka belgisi), `ett/ebt/elt/ert` (qalinlik), `etn/ebn/eln/ern` (nom), `grtn/grbn/grln/grrn`
(paz), `XNC1/XNC2`, `mill`, `drill`, `groove`. Funksiyalar: `if`, `empty`, `format`, `now`, `rspace`, `crc16`.

| Stanok | Parametrlar (standart) |
|---|---|
| SCM WinCut | Fayl nomi transliteratsiyasi (yo'q) · Etiketka bosish (ha), rejim «Обычный (x,x,x,x)(x,x,x,x)» · SCM ro'yxat faylini yaratish (yo'q) · plita soni va paket balandligi ro'yxati (yo'q) · ro'yxatda list o'lchami nomda (yo'q) · ro'yxat va kartalar lst papkasiga (ha) · ro'yxat papkasi `C:\wincut\lst\`, karta papkasi `C:\wincut\prg\` · barcha kesimlarni akslantirish (ha) · kratnost bilan bitta polosaga yoyish (yo'q) · U/V kesimlarda torsovka (0 mm), propil hisobi bilan torsovka (ha) · P-kesimlar (yo'q) · VelRotaz 3000 · VelAvanz 30 · etiketka maydonlari Campo10…14 |
| SCM MaestroCut | Etiketka bosish (ha), rejim, GibLab etiketka maydon raqami (64) · SCM ro'yxat fayli (ha) · list o'lchami nomda (yo'q) · ro'yxat papkasi `C:\MaestroCut\Client\xMix\` · akslantirish (ha) · bitta polosaga yoyish (yo'q) · U/V torsovka (0) · P-kesim (yo'q) · etiketka maydonlari (Codice, Lunghezza, Larghezza, Richiesti, CodiceBordo1…4, Job, …) |
| HOLZMA PTX | optimallashtirish parametrlari fayli (`*.prm`), arra parametrlari fayli (`*.spm`) · oldindan kesim: bosh kesimda / dokroy oldida / orqasida (0 mm) · etiketka ma'lumotlari «@» (yo'q) · PARTS_UDI foydalanuvchi yozuvlari jadvali |
| HOLZMA CadMatic4 | yo'nalish (birinchi kesimlar vertikal) · kesim tartibi (CadMatic sozlamasidan) · detal yozuvi (raqam) · oldindan kesim ×3 · etiketka axborotini qo'shish joyi (PartMaterial) · etiketka maydonlari |
| HOLZMA CadMatic3 | yo'nalish (birinchi kesim bo'yicha) · etiketka fayllarini yaratish (yo'q) |
| Biesse OSI | dastur versiyasi · yo'nalish (gorizontal) · buyurtma nomi (buyurtma sanasi) · etiketka maydonlari (kod, koord min/max, ustuvorlik, uzunlik, kenglik, tekstura, Finish, PartNo, Comment, Job, Name, …) |
| Biesse NC300 | yo'nalish (gorizontal) · RDIV · MAGP |
| FELDER Format4 PC6 | qoldiqlarni karta ustiga qo'yish (yo'q) · etiketkani detal raqamiga mos bosish (yo'q) · etiketka maydonlari (Part description(16), Headdata.text(30), Material.headline1–3(30), Part.text0(12) … text11(30)) |
| FELDER Format4 PC7 | faqat etiketka maydonlari (Part description, Headdata.text, Edge top/bottom/left/right, Part.text1…11) |
| F4Classic | etiketka fayllarini yaratish (ha), etiketka o'lchami DX 58 × DY 60.5 mm, shablonni ochish/ko'rish (shtrixkod NC1/NC2, kromka belgilari), ZPL sarlavhasi |
| Homag CHF 41/44/44 NPS400 | Z/W kesimlarda torsovka (0) · lotin harflari (yo'q) · yo'nalish (birinchi kesim bo'yicha, 5 burilish) |
| KDT-PreSize QK | propilni torsovkaga kiritish (ha) · uchinchi burilishdan boshlab torsovka (0) · etiketka fayllari (ha) · kartalar sonini paketlarga taqsimlash (ha) |
| KDT-PreSize XML | etiketka fayllari (ha), 58 × 60.5 mm, shablonni ochish/ko'rish |
| Scheer | etiketka 58 × 40 mm, shtrixkod (yo'q) |
| Nanxing CutSawFG | etiketka maydonlari Field1…20 |
| Nanxing NXCutSaw | etiketka maydonlari F1…F20 |
| Shelling MCS | uchinchi burilishdan boshlab torsovka (0) · PARTS_UDI jadvali |
| ELMO 3 (Altendorf) | torsovka (yo'q) · arra diski balandligi 49 mm · balandlik/eni nisbati 4 · bo'ylama tirgak 2…1600 mm · ko'ndalang tirgak 146…3200 mm · USB `SAW` papkasi haqida eslatma |
| GlassGCODE | versiya (NCStudio v7) |

Etiketka o'lchami 58 × 60.5 mm (F4Classic, KDT XML) va 58 × 40 (Scheer) — termo-etiketka printeri (ZPL) ishlatilishini ko'rsatadi.

## 3. «XNC Редактор» sozlamalari
- **Инструменты:** tekislik (oldingi, chap, o'ng, yuqori, pastki) · diametr · tuynuk (sквозное) · nom · chuqurlik · izoh. Standart: oldingi Bore35/26/25/20/18/15/10/8/7/5/4.5/3; yon tekisliklarda Bore8 va Bore4.5.
- **Палитра:** buyruq belgilari ro'yxati, har biri yoqiladi/o'chiriladi (Сверление va h.k.).
- **Ограничения** (stanok cheklovlari; rejim: o'chirish/ogohlantirish/…): detal gabaritlari (uzunlik X 200…3000, kenglik Y 70…950, qalinlik Z 12…60); uzun tomon bo'yicha burish (gorizontal/vertikal); kromka bilan burchakka burish (chap yuqori); gorizontal teshik markazidan frontal tekislikkacha max masofa (4 tomondan 30 mm); paz (gorizontal/vertikal ruxsat) va pazning detal chetidan min. masofasi (4 tomon 30 mm); freza radiusi uchun detaldan frezagacha max masofa 100 mm; burg'ulash: pastdan gorizontal teshiklar nomaqbul, ko'r vertikal teshik chuqurligi detal qalinligidan 2 mm kam, teshik chetlari orasi 5 mm, detal chetidan frontal teshikkacha 4 mm, gorizontal teshikkacha 3 mm.

## 4. «Модуль заказов» (mijoz buyurtma veb-moduli) — MES jamoasi
Yoqish katakchasi, URL (`/order?user=<ID>`), bosh sahifa, mavjud operatsiyalar (varaq kroy, pogonaj kroy; komplektatsiya o'chiq), buyurtmalarni saqlash joyi
(sayt bazasi / Dropbox), buyurtma holati papkalari (tasdiqlangan, buyurtma qilinmagan, buyurtma qilingan, tayyor), logotip o'lchami (70 px, menyu
190 px). Qo'shimcha yorliqlar: qo'shimcha sozlamalar, salomlashuv sahifasi, pochta bildirishnomalari, detallar jadvali sozlamalari.

## 5. CS parametrlari (onlayn, tekshirilgan)
«Максимальное количество вращений» ro'yxati: **2, 3, 4, 5, 6** (bizda ham 2…6). «Минимальный размер детали» (30 mm) — «Ограничения» bo'limida;
yordamda va internetda ma'nosi yozilmagan; foydalanuvchi: sex uskunasiga qarab har xil, GibLab sozlamasida bor → bizda ham sozlanadigan
parametr (mavjud: `min_part_size`, kichik detalda ogohlantirish).
