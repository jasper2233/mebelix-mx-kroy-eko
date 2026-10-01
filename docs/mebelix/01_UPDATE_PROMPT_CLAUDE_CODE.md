# PROMPT — Claude Code uchun: MebeliX Kroy **v2 yangilanishini** qo'llash

> Bu faylni Claude Code'ga to'liq bering. Siz allaqachon v1 paket (`PROMPT_CLAUDE_CODE.md`, `UI_SPEC.md`,
> `backend/`, `screens/`) asosida ishlashni boshlagansiz. Bu — **ustiga qo'yiladigan yangilanish**.
> v1 dagi mualliflik huquqi qoidalari to'liq kuchda (GibLab kodi, nomi, logosi, ikonkalari, yordam matnlari
> ko'chirilmaydi; faqat ish oqimi va joylashuv o'xshash).

## 0. Kontekst (nima o'zgardi)

GibLab'ning ichki yordami (barcha bo'limlar), video-darsi va xodimlar hisobi o'rganildi. Natijada:
* v1 da **bir nechta biznes qoidasi noto'g'ri** edi (torsovka o'qlari, kromka formulasi, taxminiy sarf,
  narx semantikasi) — tuzatildi;
* optimizator **rekursiv gilyotina** sifatida qayta yozildi (2..6 daraja, min kesish, oldindan ko'rish);
* ko'p yangi funksiya va ekran tafsilotlari qo'shildi;
* muhim kashfiyot: xodimlar detallarni **Bazis-Mebelshik → GibLab XML** orqali oladi → shu XML importi qo'shildi.

To'liq ro'yxat: `docs/N_CHANGES_FROM_v1.md`. Qisqa xulosa: `02_YAKUNIY_XULOSA.md`.

## 1. Hujjatlarni loyihaga qo'shing

```
<repo>/docs/mebelix/            ← shu paketdagi docs/*.md (A..O)
<repo>/docs/mebelix/screens_v2/ ← screens_v2/*
<repo>/CLAUDE.md                ← quyidagi «Doimiy qoidalar» bo'limini qo'shing
```
**Doimiy qoidalar (CLAUDE.md ga):**
1. Biznes qoidalari manbai — `docs/mebelix/B_DOMAIN_RULES.md`; optimizator — `C_CS_OPTIMIZER_SPEC.md`;
   UI — `D_UI_SPEC_v2.md` (+ v1 `UI_SPEC.md`); yorliqlar — `E_HOTKEYS.md`; atamalar — `A_GLOSSARY.md`.
2. Formulani o'zgartirishdan oldin `L_ACCEPTANCE_TESTS.md` dagi raqamlarni tekshiring — ular GibLab bilan solishtirilgan.
3. UI yorliqlari (rus) va xodimlar ustun nomlari (o'zbek) — `A_GLOSSARY.md` dagi kabi; i18n orqali.
4. GibLab matnlari/rasmlari/kodi ishlatilmaydi.

## 2. Backendni birlashtiring (merge, ko'r-ko'rona almashtirmang)

Reference: shu paketdagi `backend/` (to'liq v2, **31 test yashil**).
1. Agar sizning `backend/` v1 dan deyarli o'zgarmagan bo'lsa — v2 fayllari bilan almashtiring va testlarni ishga tushiring.
2. Agar o'zgargan bo'lsa — `docs/N_CHANGES_FROM_v1.md` jadvalidagi har bandni alohida kommit bilan kiriting:
   * N1 (tuzatishlar 1–14) — **birinchi navbatda**, har biriga test;
   * N2 — `services/optimizer.py` ni v2 bilan almashtiring (API bir xil: `optimize(items, stock, cut, mat)`,
     `Item(...)` ga ixtiyoriy blok maydonlari qo'shilgan);
   * N3 — yangi endpoint va servislar (`cl_optimizer.py`, `giblab_project.py`, `labels.py`, importers yangilanishi).
3. `models.py` o'zgarishlari va eski JSON uchun `migrate_v1_to_v2()` — `docs/F_DATA_MODEL_v2.md §F2`.
4. `tests/test_v2.py` + `tests/conftest.py` ni qo'shing; v1 `tests/test_kroy.py` ni o'chiring.
5. `pytest -q` → hammasi yashil. Benchmark: «Detskiy kravat» 1-list ≥ 92 %.

## 3. Frontendni yangilang (qaysi bosqichda bo'lsangiz — shu bosqichdan)

Muhim UI tafsilotlari (`D_UI_SPEC_v2.md`):
* Detallar jadvali: **Space** (Ткт va kromka kataklarida), **Shift+Space** (perimetr), Tab/Enter oqimi,
  Ctrl+PgUp/PgDn, Ctrl+V (paste endpoint), birinchi ochilishda o'lcham rejimi oynasi, yangi qatorda Ткт ✓.
* Har parametr yonida «?» → kontekst yordami; «Сохранить текущие параметры…» → settings API.
* «Минимальный отступ в конце» oynasi; «Группировка деталей по свойствам» — faqat «Объединение деталей» ✓ da faol.
* «Листы и остатки» — kroydan keyingi qoldiqlar qatorlari; ombordan yuklash/saqlash tugmalari.
* «Раскрой»: status ko'rsatkichlari sozlamasi (12 ta), F2 izoh satri, «До кроить», detalni bosish — o'xshashlarni
  ajratish, ikki marta bosish — xossalar, g'ildirak — masshtab, qoldiq raqamlari ko'k, kromka chiziqlari/harflari.
* «Изделия» xossalari oynasi (Свойства | Программа), umumiy «Сортировка» oynasi, ustun profillari.
* «Товары» (katalog) oynasi — MES katalogi daraxti.
* Chop oynalari: Поля страницы, Изделия, (EL), (XNC) statistika — `H_REPORTS_LABELS.md`.
* Import: «Bazis / GibLab XML» (`/api/projects/import-giblab`), Excel oynasi profillar bilan.

## 4. Ustuvorlik (yangilangan)

1. N1 tuzatishlar + testlar (hisob-kitob to'g'riligi — xodimlar GibLab bilan solishtiradi!).
2. Detallar jadvali klaviatura oqimi + paste + import-giblab (kundalik ish).
3. Kroy ekrani (status, kartalar, izoh, До кроить, buyruqlar jadvali) + optimizator v2.
4. Chop (KROYGA profili kabi: talabnoma, CS detallar/listlar, kartalar, EL, XNC shtamp) va etiketkalar.
5. MES: katalog, qoldiqlar ombori, «Заказать» webhook.
6. Qolganlari: qo'lda tahrir, XNC redaktor, CL/SP, postprotsessor.

## 5. Ochiq savollar (foydalanuvchidan so'rang, taxmin qilmang)

1. Kromka qalinligi (PVC 1 mm) GibLab'da 0 — shunday qolsinmi? (`M_STAFF_HABITS.md §M2`)
2. Arra stanogi modeli va postprotsessor formati (namuna fayl).
3. MES API manzillari, auth, webhook formati.
4. Etiketka printeri va o'lchami.
5. Haqiqiy `.project` fayl (Bazis eksporti) — import testiga fixture sifatida.

## 6. Har bosqich oxirida

Nima qilindi, qaysi testlar qo'shildi, qanday ishga tushiriladi, keyingi qadam — qisqa hisobot.
