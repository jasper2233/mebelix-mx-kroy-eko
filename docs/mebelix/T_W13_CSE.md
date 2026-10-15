# T. W13 paketi — CSE (Редактирование раскроя) rejimlari (2026-10-02)

Manba: `giblab_inventory/01_CS_CSE_qoldiqlar.md` (CSE-001…023, 3.2.4, 4-bo'lim №11, 13, 15). Optimizator (`optimizer.py`, `colpack.py`)
o'zgarmadi. Foydalanuvchi: «GibLabdagi hamma funksiya bizda bo'lsin» — Q-8 javobsiz bo'lsa ham hammasi qilindi; noaniq joylar
(past) «Savollar» bo'limida, standart bitta joyda belgilangan.

## 1. Qilinganlar

| ID | Nima | Qaerda |
|---|---|---|
| CSE-009, 3.2.4 | **«Торцовка листа»**: kartaga alohida ТД / ТШ / minimal otstup (pastda, o'ngda). `null` — list qatori / operatsiya qiymati. Foydali zona o'zgaradi: daraxt zona boshiga nisbatan o'z joyida qoladi, oxiridagi bo'sh joy kengayadi/qisqaradi; detal sig'masa — xato. Karta torsovkasi `validate`, `rebuild`, T-buyruqlar, ko'rsatkichlarda hisobga olinadi | `models.CutMap.trim_*`, `validate.map_stock`, `editor_w13.map_trim`, `CutTrimDialog.tsx` (Alt+T) |
| CSE-016 | Kartalar tartibi (Ctrl+↑/↓, tugmalar; first/last ham API da) — qoldiq raqamlari (Д1, Д2…) qayta raqamlanadi | `editor_w13.apply_map_kind`, `CutEditor.tsx` |
| CSE-019 | **Ko'p tanlash**: Ctrl+bosish, sichqoncha ramkasi (to'liq ichidagi eng yuqori daraja tugunlar; Ctrl/Shift — qo'shish), Ctrl+A. Birga: o'chirish (Del / o'ng tugma), ko'chirish (boshiga/oxiriga/qadam — har polosada blok bo'lib, nisbiy tartib saqlanadi), nusxalash, qayta kesish (≤ 10 hudud), burish. `paths: [[…]]` — `path` bilan orqaga mos | `editor.clean_paths`, `editor_w13.*_many`, `MapView.tsx` (`nodesInRect`, `onBand`) |
| CSE-020 | Shift+bosish — tahrir rejimi: ro'yxatdan tanlangan detalni bosilgan bo'sh joyga qo'yish; Shift+Ctrl/Alt — burib (CSE-021). Oddiy bosish ham qo'yadi (avvalgi qulaylik). «Ota tugunni tanlash» → Backspace | `CutEditor.tsx` `onPick` |
| CSE-022 | **Ko'p qo'yish** (Shift+A+bosish, yoki «rejim» tugmasi): bo'sh joyga nusxalar ustun-ustun to'ldiriladi (qolgan soni, joy, daraja chegarasi); `count` — aniq son. Minimal obrezka buzilsa — nusxalar soni kamaytirilib qayta uriniladi | `editor_w13.place_multi` |
| CSE-023 | **Blok bilan kengaytirish** (Shift+W+bosish): «Группировка в блок» detali bloki (guruh tuguni yoki bir xil detallar qatori) «Макс. количество в блоке» gacha; joy yetmasa — polosa blok o'qi bo'yicha kengayadi, undan keyingi polosalar siljiydi, joy eng oxirgi bo'sh joydan olinadi, qo'shni ustunlarning chiqindisi shuncha kattalashadi | `editor_w13.expand_block` |
| — | Detalni **burish** (Alt+R; joyiga sig'sa va tekstura ruxsat bersa), **almashtirish** (boshqa detal bilan, shu joyga), ikki elementni **o'rin almashtirish** (bitta polosada) | `editor_w13.flip/replace/swap` |
| CSE-002, 3.2 | Tahrir ro'yxati: ustun sarlavhasi bosilsa saralash (o'sish / kamayish / bekor), «Итого» qatori; holat qatori — `ui.cutIndicators` (Ctrl+P) bo'yicha 12 ko'rsatkich («Раскрой» bilan umumiy `cutIndicators.ts`) | `CutEditor.tsx`, `cutIndicators.ts` |
| CSE-017/F2 | Tahrir oynasida F2 — karta izohi (2000 belgigacha; `PATCH …/maps/{n}` ham shu chegarada). «Раскрой» da F2 avvaldan bor edi | `CutEditor.tsx`, `main.patch_map` |
| §3 | Qo'lda natija: `calc._account`, `cs_cost`, qoldiq qayta tasnifi, ombor (`commit`/`rollback`), «Исп. кол-во» (kalit mavjud qoldiq guruhlariga qirqiladi), hisobot — testlar bilan tasdiqlangan. Saqlagach деловой qoldiq bo'lsa — omborga yozish taklifi (kroydan keyingidek) | `editor._carry_taken`, `CsCut.tsx` |
| §4 | Yaxlitlik: tahrir sonlari (NaN/∞/manfiy/katta/noto'g'ri tur) — 4xx; daraxt ildizi foydali zonadan chiqmasin (`ed.root_out`); parallel tahrir izi (`GET …/edit/rev` + `PUT …/result?base=` → 409); `POST …/edit/batch` (≤ 200 amal, hammasi yoki hech biri), `POST …/edit/check` | `editor.py`, `api_cse_w13.py`, `main.py` |

Yangi `ed.*` xabarlari — `app/i18n.py` («CSE: Редактирование раскроя, режимы (W13)» bo'limi); interfeys matnlari — `frontend/scripts/i18n_cse_w13.py`.

## 2. Standartlar va qarorlar (bitta joyda belgilangan)

* «Торцовка листа» (Q-8 javobsiz): 4 qiymat kartaga yoziladi; pastdagi/o'ngdagi otstup berilmasa — shu karta torsovkasiga teng (operatsiya darajasidagi qoida bilan bir xil). Konstanta: `editor_w13.MAX_TRIM = 500`.
* Ko'p qo'yish / blok kengaytirish: bitta bosishda ≤ `MAX_FILL = 5000` nusxa; qirindi qoidasi bo'yicha qayta urinishlar `ATTEMPTS = 8`.
* Ctrl+bosish endi ko'p tanlash (GibLab yordamidagi ma'no); burib qo'yish — Alt yoki Shift+Ctrl (avval Ctrl).
* Parallel tahrir: `base` berilmasa — avvalgi xulq (tekshiruvsiz). Sexdagi `done_count` (MES) izga kirmaydi, lekin eskirgan qoralamadan saqlashda qaytadan yoziladi (cheklov).
* Optimizator kuchaytirilmadi; `validate()` o'zgarishi: faqat karta torsovkasi bilan zona (`map_stock`) — torsovkasiz kartalarda xulq aynan avvalgidek.

## 3. Qilinmaganlar

* Haqiqiy GibLab «Торцовка листа» tugmasining aniq ma'nosi yordamda ochilmagan — shuning uchun yuqoridagi talqin (Savol 1).
* Sudrab-tashlash bilan detal/kartani ko'chirish (drag & drop) — qilinmadi: ko'chirish tugmalari, Ctrl+←/→/↑/↓ va ko'p tanlash bor.
* Postprotsessor shablon kontekstida (`postprocessors.py`) `op.trim_length` operatsiya darajasida qoladi; karta torsovkasi T-buyruqlarda (`commands`) to'g'ri ko'rinadi, lekin alohida maydon sifatida berilmagan.

## 4. Testlar

`backend/tests/test_cse_w13_multi.py` (6), `_fill.py` (13), `_map.py` (13), `_fuzz.py` (5: 4 konfiguratsiya × 50 = **200 tasodifiy ketma-ketlik**, har qadamdan keyin `validate()` 0 xato + zona/hisoblagich invariantlari + qayta qurish barqarorligi; rad etilgan amal qoralamani o'zgartirmaydi), `_safety.py` (7: son/NaN/∞ ma'lumot, chuqur JSON, **10 000 detalli karta** ~5 s, parallel saqlash — 12 ta oqim `base` bilan: aynan bittasi o'tadi; `base`siz 8 ta oqim: butun qoralama; eskirgan qoralama 422). Yordamchi: `tests/cse_w13_util.py` (daraxt qurish, mustaqil tekshiruv).

## 5. Savollar (foydalanuvchiga)

1. «Торцовка листа» tahrirda nima uchun ishlatiladi (Q-8)? Biz: bitta kartaga ТД/ТШ/otstup o'zgartirish. Boshqa ma'no (masalan, torsovkani karta uchun o'chirib-yoqish) bo'lsa — bildiring.
2. Oddiy bosish ham (ro'yxatdan detal tanlangan bo'lsa) detalni qo'ysinmi, yoki faqat Shift+bosishdami (GibLabdagidek)? Hozir ikkalasi ham.
3. Blok kengaytirish (Shift+W) polosani siljitib kengaytiradi — xodimlar kutgan xulq shumi? Blok «ketma-ket nusxa» bo'lib polosada turgan (guruh tuguni yo'q) bo'lsa — faqat blokdan keyingi bo'sh joy ishlatiladi.
4. Tahrir oynasi boshqa oynada o'zgargan natijaga to'qnashsa (409) — «qayta oching» yetarlimi yoki izohlarni birlashtirib saqlash kerakmi?
5. Qo'lda saqlagach деловой qoldiqni omborga yozishni taklif qilish (kroydan keyingidek) — qoladimi?
