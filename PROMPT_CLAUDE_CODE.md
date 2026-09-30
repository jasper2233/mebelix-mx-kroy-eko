# PROMPT — Claude Code uchun: «MebeliX Kroy» ni qurish

> Ushbu faylni to'liq Claude Code ga bering (loyiha ildizida `CLAUDE.md` sifatida ham saqlash mumkin).
> Yonida: `backend/` (tayyor FastAPI yadrosi), `UI_SPEC.md` (ekranlar tavsifi), `screens/` (33 ta rasm).

---

## Rol va maqsad

Sen tajribali full-stack dasturchisan. Mebel ishlab chiqarish korxonasi uchun **MebeliX Kroy** —
listli materiallarni (LDSP, MDF, XDF) kesish optimizatsiyasi web-ilovasini qurasan.
Korxona xodimlari hozir GibLab dan foydalanadi, shuning uchun **interfeys joylashuvi, ustunlar
tartibi, tablar, tugmalar va klaviatura yorliqlari GibLab dagidek bo'lishi kerak** (`UI_SPEC.md`
va `screens/` — asosiy manba). Ilova keyinchalik korxonaning MES tizimiga ulanadi.

## Qat'iy cheklovlar (mualliflik huquqi)

1. GibLab kodini, JS/CSS fayllarini, ikonkalarini, logosini, nomini, yordam matnlarini, fayl
   formatlarini **nusxalama va yuklab olma**. Hamma narsa noldan yoziladi.
2. Ikonkalar — faqat ochiq litsenziyali to'plam (`lucide-react` yoki `@tabler/icons-react`).
3. Ranglar/shrift — o'zimizniki (MebeliX palitrasi), lekin **joylashuv va ish oqimi** bir xil.
4. Hech qayerda «GibLab» so'zi UI da bo'lmasin. Ilova nomi: **MebeliX Kroy**.

## Texnologiyalar

* **Backend:** Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2 (SQLite → PostgreSQL),
  `backend/` papkasidagi tayyor kod asosida. Uni buzma — kengaytir. Testlar `pytest`.
* **Frontend:** React 18 + TypeScript + Vite, holat — Zustand, server so'rovlari — TanStack Query,
  jadvallar — **AG Grid Community** (Excel kabi tahrir, klaviatura, ustun o'lchami, Ctrl+V paste),
  kroy kartasi — SVG (keyinchalik tahrir uchun `react-konva`), i18n — `i18next` (uz, ru).
* **Hisobot:** backend HTML → PDF (`weasyprint`) yoki brauzerda chop.
* Docker Compose: `api`, `web`, `db` (postgres).

## Arxitektura

```
mebelix-kroy/
  backend/app/
    models.py          # Project, Operation(CS/EL/GR/XNC), Part, StockSheet, CuttingResult ...
    db.py              # jadvallar: folders, projects(JSON), project_history, catalog_items,
                       #            settings_profiles, remnants
    main.py            # REST API (/api/...)
    services/
      optimizer.py     # gilyotina kroy algoritmi (tayyor, testlangan)
      sizes.py         # 4 xil o'lcham: detal / prifugovka / zagotovka / pilniy
      calc.py          # kroyni ishga tushirish, narx, kromka sarfi, omborga talabnoma
      xnc.py           # XNC dastur statistikasi va narxi (xavfsiz ifoda hisoblagich)
      render.py        # SVG karta, HTML hisobot
      importers.py     # Excel/CSV import (ustunlar xaritasi)
  frontend/src/
    app/Layout.tsx             # chap akkordeon + sarlavha + splitter
    features/projects/         # Проекты ro'yxati, papkalar
    features/project/          # sarlavha, Операции/Изделия jadvallari
    features/cs/               # Параметры, Детали, Листы и остатки, Раскрой
    features/el/, xnc/, print/, settings/
    shared/grid/               # AG Grid o'rami + klaviatura yorliqlari
    shared/hotkeys.ts          # UI_SPEC §10 dagi barcha yorliqlar
    i18n/uz.json, ru.json
```

## Bosqichlar (har bosqich oxirida ishlaydigan holat + test)

### 1-bosqich — Karkas va loyihalar
* Docker, backendni ishga tushir, `pytest` yashil bo'lsin.
* Layout (UI_SPEC §0): chap akkordeon, sarlavha maydonlari, yuqori/pastki panel splitter.
* Проекты ro'yxati (§1): papkalar, ochish (dbl-click / Ctrl+Space), qo'shish, nusxa, o'chirish,
  qayta nomlash, ko'chirish. Holat (Не заказан / Заказан / Утвержден / Готов).

### 2-bosqich — Operatsiyalar va detallar
* «Операции» jadvali (§3) — ustunlar, toolbar, operatsiya turi oynasi, Ctrl+K/Del/Ctrl+↑↓.
* «Изделия» jadvali (§4). Mahsulot soni → detallar ОК qayta hisoblanishi.
* CS «Параметры» (§5.1) — **barcha** maydonlar, standart qiymatlar jadvaldagidek;
  «standart sifatida saqlash» → `settings_profiles`.
* CS «Детали» (§5.2) — asosiy ish joyi: tezkor kiritish (Enter/Tab, oxirgi qatordan keyin
  yangi qator), Excel dan Ctrl+V, kromka katagida EL dropdown, tekstura checkbox, jonli
  «Площадь / Кол-во», tooltip (4 o'lcham), Свойства oynasi, Групповые действия, ustun
  sozlamalari profillari (standart profil: `№ | детал номи | Д-на | Ш-на | Сони | Ткт | ОВ | ОН | ОЛ | ОП | Код | ID | ОК`).
* O'lcham kiritish rejimi (заготовки / детали с кромкой / после прифуговки).
* Undo/Redo (Ctrl+Z/Y) — backend `project_history`.

### 3-bosqich — Kroy
* «Листы и остатки» (§5.3), ombordagi qoldiqlarni `remnants` jadvalidan qo'shish.
* «Раскрой» (§5.4): Раскроить → `POST /optimize`; status qatori (№, S, C, Cp, LT, F);
  karta SVG (detal to'q sariq, chiqindi kulrang, qoldiq ko'k, raqam + o'lchamlar);
  miniatyuralar; Таблица команд; Home/↑/↓/End; Удаление раскроя; До кроить.
* Kroydan keyin деловой остаток larni `remnants` ga yozish (tasdiq bilan).
* Kroy sifati: `optimizer.py` ni yaxshilash mumkin, lekin testlar o'tishi va natija
  yomonlashmasligi shart (benchmark: `tests/test_kroy.py` dagi loyiha — 2 list, 1-list ≥ 91 %).

### 4-bosqich — Kromka, hisobot
* EL Параметры/Детали (§6), formula testlari mavjud.
* Печать отчета (§8): profil, sozlamalar, PDF — sarlavha, omborga talabnoma, CS detallar/listlar,
  kroy kartalari (header ko'rsatkichlari sozlanadi, QR-kod har kartada), EL jadvali.
* Detal etiketkalari (QR: loyiha №, detal ID, o'lcham, kromka) — MES skaneri uchun.

### 5-bosqich — Kroyni qo'lda tahrirlash va XNC
* Редактирование раскроя (§5.4): drag&drop, Shift/Alt/Ctrl/o'ng tugma qoidalari, undo.
* XNC (§7): parametrlar, dastur daraxti (JSON), narx; grafik redaktor keyinroq.
* Postprotsessor: bizning arra stanogimiz formati (formatni men beraman).

### 6-bosqich — MES integratsiyasi (men o'zim moslayman, sen interfeys qoldir)
* `POST /api/catalog/sync` — materiallar/narxlar MES dan.
* `Project.mes_order_ref` — MES buyurtmasi bilan bog'lash; holat o'zgarsa webhook
  (`MES_WEBHOOK_URL` env).
* Auth: MES SSO (JWT) — `Authorization: Bearer`, hozircha stub.

## Biznes qoidalari (buzilmasin)

* O'lchamlar mm, maydon m², uzunlik hisobotda m. Valyuta — loyiha sarlavhasidan (UZS).
* Kromka tomonlari: **ОВ/ОН — uzunlik bo'yicha**, **ОЛ/ОП — en bo'yicha**.
* `ОК = Сони × mahsulot soni`. `ИК` — kroyga kirgan, `Ост` — kirmay qolgan.
* Pilniy o'lcham = zagotovka + pripusklar; zagotovka = detal − kromka qalinligi + prifugovka.
* Tekstura (Ткт) yoqilgan va «Учет текстуры» ✓ bo'lsa detal aylantirilmaydi.
* Torsovka va propil kroyda hisobga olinadi; `trim_includes_kerf` false bo'lsa propil qo'shiladi.
* Qoldiq = деловой: katta tomon ≥ side1, kichik ≥ side2, maydon ≥ min_area; aks holda chiqindi.
* Kromka sarfi: `material = Σ(tomon + 2×остаток по краям) × (1+отход%)`,
  `ish = Σ max(tomon, мин. оклеиваемая длина)`.
* Material narxi listlar bo'yicha (yaxlitlash qoidasi bilan) yoki maydon bo'yicha;
  operatsiya narxi: kesish uzunligi / perimetr / detal maydoni / material maydoni × narx.

## Sifat talablari

* Har API uchun pytest; frontendda asosiy oqim uchun Playwright e2e:
  loyiha yaratish → CS qo'shish → 14 detal kiritish (test ma'lumoti) → kromka → Раскроить →
  hisobot PDF.
* 500 detalgacha kroy ≤ 5 s.
* Barcha matnlar i18n orqali; standart til — rus yorliqlari + o'zbekcha ustun nomlari
  (xodimlar odatlangan holat), sozlamada to'liq o'zbekcha.
* Har bosqichdan keyin: nima qilinganini, qanday ishga tushirishni va keyingi bosqichni qisqa yoz.

## Birinchi buyruq

`backend/` ni o'qib chiq, `pip install -r requirements.txt && pytest` ni ishga tushir, so'ng
1-bosqichdan boshla. Noaniq joy bo'lsa — `UI_SPEC.md` va `screens/` dagi mos rasmga qara.
