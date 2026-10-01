# B. Biznes qoidalari va formulalar (v2 — aniqlashtirilgan)

Manba: GibLab ichidagi yordam (Справка) va video-darsni o'rganish, xodimlar loyihasi bilan
solishtirish. Matnlar o'z so'zlarimiz bilan yozilgan. Har qoida uchun test: `docs/L_ACCEPTANCE_TESTS.md`.

Birliklar: o'lchamlar **mm** (aniqlik 0.0001), maydon **m²**, uzunlik hisobotda **m**.
Koordinatalar: X — list uzunligi (chapdan o'ngga), Y — list eni (yuqoridan pastga).

---

## B1. Detal tomonlari

```
            ОВ (edge_top)  — UZUNLIK bo'ylab
        ┌──────────────────────────────┐
 ОЛ     │                              │  ОП
(left)  │           Длина (X)  →       │ (right)   ← EN bo'ylab
        │                              │
        └──────────────────────────────┘
            ОН (edge_bottom) — UZUNLIK bo'ylab
```
* ОВ/ОН — uzunlik tomonlari (kromka uzunligi = detal **uzunligi**), ular detal **ENiga** ta'sir qiladi.
* ОЛ/ОП — en tomonlari (kromka uzunligi = detal **eni**), ular detal **UZUNLIGiga** ta'sir qiladi.

## B2. To'rt xil o'lcham va kiritish rejimi

Har detalning 4 o'lchami: **детали** (kromka bilan tayyor), **после прифуговки** (kromkasiz),
**заготовки** (frezadan oldin), **пильный** (arra o'lchami).

| Rejim (loyiha `size_mode`) | Kiritilgan qiymat | Hisob |
|---|---|---|
| `blank` — заготовка | заготовка | jointed = blank − Σprifugovka; detail = jointed + Σkromka_qalinligi |
| `detail` — деталь (с кромкой) | detal | jointed = detail − Σkromka_qalinligi; blank = jointed + Σprifugovka |
| `jointed` — после прифуговки | jointed | detail = jointed + Σqalinlik; blank = jointed + Σprifugovka |

`пильный = заготовка + ▽+△ (en bo'yicha) + ▷+◁ (uzunlik bo'yicha) + 2×«Припуск на обработку заготовки»`.
Σ — shu o'lchamga ta'sir qiluvchi kromkali tomonlar bo'yicha (B1).

Misol (kromka 2 mm, prifugovka 1 mm, ОВ+ОН, kiritilgan 300×300):

| Rejim | детали | после прифуг. | заготовка | пильный |
|---|---|---|---|---|
| blank | 300×302 | 300×298 | **300×300** | 300×300 |
| detail | **300×300** | 300×296 | 300×298 | 300×298 |
| jointed | 300×304 | **300×300** | 300×302 | 300×302 |

UI: detal xossalari oynasida kiritilgan qator ajratib ko'rsatiladi — blank: ko'k fon;
detail: yashil matn; jointed: qizil kursiv. Пильный qatori to'q sariq.
Kiritish rejimini detallar kiritilgandan KEYIN o'zgartirish tavsiya etilmaydi (o'lchamlar qayta hisoblanadi) —
UI ogohlantirish chiqaradi.

## B3. Torsovka va foydali zona (CS)

* **Торцовка по длине** (`trim_length`) — listning **YUQORI** chetidan kesiladi; **pastki** chetda
  «minimal otstup» qoldiriladi (standart = shu qiymat). ⇒ **ENni** kamaytiradi.
* **Торцовка по ширине** (`trim_width`) — **CHAP** chetdan; **o'ng** chetda minimal otstup. ⇒ **UZUNLIKni** kamaytiradi.
* Qiymat propilni o'z ichiga olmaydi (agar «Торцовка включает толщину пропила» ✓ bo'lmasa).
* 0 — torsovka yo'q (propil ham qo'shilmaydi).
* «Минимальный отступ в конце» oynasi: «снизу» va «справа» qiymatlarini alohida belgilash
  (☐ belgilanmasa — torsovka qiymati ishlatiladi).
* Har list qatorida ТД/ТШ bo'lsa — operatsiya qiymati o'rniga shu ishlatiladi.

```
foydali_en    = W − (trim_length + kerf) − (end_bottom + kerf)
foydali_uzun  = L − (trim_width  + kerf) − (end_right  + kerf)
```
Misol: 1200×1000, trim 20, propil 10 → foydali en = 1000 − 30 − 30 = **940**, foydali uzunlik = **1140**.

Buyruqlar: `T1` — list yuqori cheti bir marta; `T2` — **har polosaning** chap cheti (polosa burilgandan keyin).

## B4. Qoldiqlar (CS)

| Tur | Shart |
|---|---|
| chiqindi (`waste`) | qolgan hamma bo'laklar |
| qoldiq (`remnant`) | katta tomon ≥ «Мин. размер остатка первой стороны» **va** kichik tomon ≥ «второй стороны» |
| delovoy qoldiq (`business`) | qoldiq **va** maydoni ≥ «Площадь делового остатка» (m²) |

* Delovoy qoldiqlar **material sarfiga kirmaydi** (keyingi kroylarda ishlatiladi).
* «Размер остатков с учетом торцовки» ✓ — qoldiq o'lchami foydali zona ichida;
  ☐ — list chetiga tegib turgan qoldiq torsovka/otstup zonasigacha kengaytiriladi.
* Kartada: qoldiqlar ko'k (delovoy — to'qroq), markazida **raqami** (1, 2, …), buyruqlar jadvalida `W` qatorining `Д` ustunida.
* Kroydan keyin qoldiqlar «Листы и остатки» jadvaliga qator sifatida qo'shiladi
  (Nomi = Qoldiq/Delovoy qoldiq, Ishlatildi = mijoz olib ketadigan bo'laklar soni).

## B5. CS material sarfi va narxi

**Kroygacha (taxmin):**
```
sarf_m2 = Σ(detal pilniy maydoni × ОК) × (2 − Расчетный_процент_заполнения / 100)
```
Misol: detallar 1 m², 90 % → 1.1 m².

**Kroydan keyin:**
```
Количество материала (m²) = ishlatilgan listlar maydoni − delovoy qoldiqlar maydoni
```

**Material narxi** (`price` ma'nosi «Расчет стоимости по листам» ga bog'liq):
* ✓ (`cost_by_sheets=True`): narx = **1 list** narxi; `material_narxi = yaxlitlangan_listlar_soni × price`
* ☐: narx = **1 m²** narxi; `material_narxi = sarf_m2 × price`

**Листлар yaxlitlanishi** («Окруление листы», kod GibLab bilan bir xil):
`11` к целому · `12/13/14` любое 1/2, 1/3, 1/4 · `22/23/24` по ширине · `32/33/34` по длине.
Oxirgi (bitta nusxali) kartada band qism ulushi: по длине → max(x+uzunlik)/L, по ширине → max(y+en)/W,
любое → ikkisining kichigi; ulush 1/k ga **yuqoriga** yaxlitlanadi.

**Operatsiya narxi** («Расчет стоимости операции по» × «Цена операции»):

| Asos | Qiymat |
|---|---|
| Длине реза | jami kesish uzunligi (m) — har karta kesish uzunligi × shu kartadagi listlar soni |
| Периметру деталей | Σ 2·(L+W)·ОК / 1000 |
| Площади деталей | Σ L·W·ОК / 10⁶ |
| Площади материала | Количество материала (delovoy qoldiqsiz) |

## B6. Kromka (EL)

Har kromkali tomon uchun:
```
ish (Длина оклейки)          = tomon uzunligi                       (qo'shimchasiz)
material (Количество матер.) = max(tomon, Мин. оклеиваемая длина) + 2 × Длина остатка по краям
jami material               = Σ material × (1 + Процент отхода / 100)
```
* Soni: ОК (− МК). CS va CL operatsiyalaridagi barcha detallar hisoblanadi.
* Yaxlitlash: «Округление длины материала/кромкования» kodi = o'nlik_xonalar×10 + rejim
  (0 yaqiniga, 1 kattaga ⌈⌉, 2 kichikka ⌊⌋). Masalan 10 = «[0.0] к ближайшему», 21 = «⌈0.00⌉ к большему».
* `Стоимость материала = material_m × Цена материала` (faqat «Учитывать материал» ✓ bo'lsa);
  `Стоимость операции = ish_m × Цена метра оклейки`.
* Tekshirilgan: «Detskiy kravat» — material **10.8 m**, ish **10.4 m** (GibLab bilan bir xil).
* Kromka qalinligi va prifugovka detal o'lchamiga ta'sir qiladi (B2).
* Belgi (A, B, …) — kartada va etiketkada kromkali tomon yonida; rang — detal jadvalida kromka nomi rangi;
  «Линии маркировки» 0..3 — kartada/etiketkada tomon chizig'i soni.
* «Минимальный размер стороны детали, перпендикулярной оклеиваемой стороне» (standart 40 mm) —
  undan tor detalga kromka qo'yilsa ogohlantirish.

## B7. Pazovanie (GR)

* Parametrlar: en W, chuqurlik D, chetdan otstup O, «Отступ включительно», arra qalinligi.
* O'tishlar soni = ⌈W / arra_qalinligi⌉; kesish uzunligi = paz uzunligi × o'tishlar.
* Narx = paz uzunligi (m) × «Цена метра паза».
* Detalda: 4 tomon (ПВ/ПН — uzunlik bo'yicha, ПЛ/ПП — en bo'yicha) + tomon (лицевая/обратная).

## B8. Soni (ОК), МК, ИК, Ост

```
ОК  = Сони × mahsulot soni
kroyga kiradi = ОК − МК          (МК — ombordagi tayyor detallar)
ИК  = kroyga kirgan
Ост = kirmay qolgan  (ИК + Ост = ОК − МК)
```
Mahsulot soni o'zgarsa — barcha bog'liq hisoblar qayta hisoblanadi.

## B9. Karralik va paket

`Кратность = floor(Высота пакета / material qalinligi)` (UI da o'qish uchungina, masalan 40/16 → 2).
Karta `C` listdan iborat bo'lsa: paketlar soni = ⌈C / karralik⌉.
«Большой пакет» ✓ — optimizator bir xil kartalarni ko'proq takrorlashni afzal ko'radi (seriya ishlab chiqarish).

## B10. Mahsulot narxi (Изделия jadvali)

`Ст. м-ла` va `Ст. оп-и` — **1 dona** mahsulot uchun, `Всего` = × soni. Taqsimlash:
CS/CL — detal maydoni ulushi, EL — kromka uzunligi ulushi, O — egasi, XNC — bog'langan detal.

## B11. Omborga talabnoma (Требование на склад)

| Tur | Qator | Birlik | Soni |
|---|---|---|---|
| CS | «Material (Листы: N шт, Длина реза: X м)» | list (yoki m²) | listlar soni |
| EL | «Kromka (Длина кромкования (работа): X м)» | m | material uzunligi |
| CL | profil | polosa | polosalar soni |
| O | har material qatori | o'z birligi | soni |

Chop sozlamalari: «печатать просто количество работы по резке», «печатать Длина кромки (работа)» — ✓/☐.

## B12. Detal nomidagi belgilar va tavsifdagi dastur kodlari

* Nomda: `=` — pazovanie, `*` — frezerovka (radiuslar), `%` — parmalash (hisobotda `[*] Фрезерование` legendasi).
* Tavsifda: `#KOD` — lits tomon XNC dasturi, `##KOD` — orqa tomon (probelsiz).
* Detalda XNC operatsiyasi bo'lsa `№` yonida `'` (masalan `6'`).

## B13. Operatsiya egasi

Operatsiya loyihaga yoki mahsulotga tegishli bo'lishi mumkin. Mahsulotga tegishli bo'lsa —
material miqdori va narx mahsulot soniga ko'paytiriladi (asosan O — komplektatsiya uchun).
