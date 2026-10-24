# MX Kroy — ko'p abonentli (SaaS) tuzilish: 5 000 → 100 000+ korxona

Foydalanuvchi qarori (2026-10-22): «mx kroyni 5000 ming abanentga moslash kerak, keyinchalik bu ko'rsatgich 100 balki 1000 ga
oshadi balki undan ham ortiq bo'lishi mumkin»; **abonent = alohida korxona** (o'z xodimlari, loyihalari, ombori, materiallari,
sozlamalari; boshqa korxona ma'lumotini hech qachon ko'rmaydi; bizning ishxona — shulardan biri); PostgreSQL — shu kompyuterga
(keyin katta serverga ko'chiriladi); parollar siyosati — onlayn sotuvdan oldin.

## Hozirgi holat (audit 2026-10-22)
- Korxona tushunchasi yo'q: loyihalar, papkalar, ombor (qoldiqlar), katalog, sozlamalar, OEE — hammasi umumiy.
- Foydalanuvchilar — `MEBELIX_USERS` muhit o'zgaruvchisida, parol ochiq matnda; bazada foydalanuvchilar jadvali yo'q.
- Loyiha qulfi (`store._lock`), MES qulfi, CN nesting ishlari — faqat bitta jarayon ichida; bir nechta jarayonda yo'qolgan yangilanish.
- Kroy so'rovning ichida (4–17 s), PDF — so'rov ichida Chrome; navbat yo'q.
- Loyiha raqami, OEE kalitlari — umumiy noyob; ro'yxat har loyihaning to'liq JSON ini o'qiydi; tarix — 100 ta to'liq nusxa.

## Tamoyillar
1. **Ajratish ikki qatlamda:** ilova (token → korxona) + PostgreSQL Row-Level Security (har jadvalda `company_id`, siyosat
   `company_id = current_setting('app.cid')`). Ilovada filtr esdan chiqsa ham baza boshqa korxona qatorini bermaydi.
2. **Holatsiz ilova jarayonlari:** istalgan jarayon istalgan so'rovni bajaradi; qulflar, ishlar, navbat — bazada.
3. **Og'ir ishlar — alohida ishchilarda** (kroy, nesting, PDF): veb-jarayon bandmas, navbat bilan.
4. **Bosqichma-bosqich, ma'lumot yo'qolmasdan:** har bosqich SQLite va PostgreSQL da testdan o'tadi; ko'chirishdan oldin zaxira,
   ko'chirgandan keyin sonlar solishtiriladi.

## Bosqichlar
**1-bosqich (poydevor, hozir):**
- PostgreSQL 16 (portativ, `D:\cloude giblab jasur\pgsql` + `pgdata`, faqat localhost); JSON → JSONB.
- `companies`, `users` jadvallari (parol — PBKDF2-SHA256 xesh); mavjud ma'lumot → 1-korxona (bizning ishxona);
  `MEBELIX_USERS` dagi loginlar 1-korxona foydalanuvchilari sifatida ishlashda davom etadi.
- Hamma ma'lumot jadvallarida `company_id` + RLS; noyob kalitlar korxona ichida (loyiha raqami har korxonada 1000001 dan).
- Token ichida korxona (`cid`); har tranzaksiya boshida `app.cid` o'rnatiladi.
- Jarayonlararo qulflar — PostgreSQL advisory lock (loyiha, MES buyurtma, sxema migratsiyasi).
- SQLite → PostgreSQL ko'chirish skripti (sonlar va mazmun tekshiruvi), xodimlar serveri PostgreSQL ga, bir nechta jarayon.
**2-bosqich:** ishlar navbati bazada (kroy / nesting / PDF alohida ishchi jarayonlarda), loyihalar ro'yxati sahifalab (JSON siz),
tarix siqilgan (zlib) yoki farqlar bilan, sozlamalar keshi jarayonlararo bekor qilinadi.
**3-bosqich (onlayn sotuvdan oldin):** ro'yxatdan o'tish / korxona yaratish, korxona admini xodimlarini boshqaradi, parol siyosati,
ta'riflar va cheklovlar (foydalanuvchi soni, saqlash hajmi), audit jurnali, zaxira va tiklash tartibi.
**4-bosqich (100 000+):** PgBouncer, o'qish nusxalari (replica), katta korxonalarni alohida bazaga (shard) ko'chirish — `company_id`
asosida; fayllar / rasmlar — obyekt omboriga (S3 tipidagi).

## Bajarilgan (2026-10-22, 1-bosqich)
- PostgreSQL 16.6 portativ (`D:\cloude giblab jasur\pgsql`, ma'lumot `pgdata`, ICU `und` — kirill / o'zbek harflari `lower()`
  bilan to'g'ri), parollar `pg_secrets.env` (repoda emas). Baza `mebelix`, testlar `mebelix_test` (`MEBELIX_TEST_DB_URL`).
- `app/tenant.py` (korxona konteksti), `db.py`: `companies`, `users`, har ma'lumot jadvalida `company_id`, korxona ichida noyob kalitlar
  (loyiha raqami, OEE), JSONB, RLS siyosati `mx_tenant` (FORCE), `init_db` advisory lock bilan; tranzaksiya boshida `app.cid`/`app.sys`.
- `auth.py`: bazadagi foydalanuvchilar (PBKDF2-SHA256), token `cid`, o'chirilgan korxona kira olmaydi; middleware so'rovni korxonaga bog'laydi.
- `store._lock` — jarayon ichida RLock + PostgreSQL advisory lock (eng tashqi kirishda); MES qabul qilish va start-up seed ham shu bilan.
- Korxona bo'yicha keshlar (`xnc_tools`, `el_symbols`, `xnc_stats`), CN nesting fon oqimi korxona kontekstida.
- Vositalar: `tools/migrate_sqlite_to_pg.py` (son + mazmun tekshiruvi), `tools/tenant_admin.py`, `tools/backup_db.py` (PG: `pg_dump` superuser).
- Testlar: PostgreSQL 2245 o'tdi, SQLite 2243 o'tdi, e2e 47/47; `test_tenancy.py` (ajratish, RLS, parallel tahrir).
  4 jarayonli server sinovi: bir loyihaga 40 parallel qo'shish — yo'qotishsiz; 2 korxona bir vaqtda 30 tadan loyiha — har biri 1000001…1000030.
- Xodimlar serveri ko'chirildi: 54 loyiha, 1449 tarix, sozlamalar, ombor — son va mazmun bir xil; `uvicorn --workers 4`;
  5 login bazada (1-korxona). Eski SQLite fayli — arxiv.
- CN nesting fon ishlari holati `jobs` jadvalida (RLS): holat / to'xtatish istalgan jarayondan; 4 jarayonli sinov — 404 yo'q,
  band (409) va to'xtatish jarayonlararo ishlaydi. PostgreSQL test bazasi har yugurishda toza sxema (`tests/conftest.py`).
- 2-bosqich — quyida.
## Bajarilgan (2026-10-22, 2-bosqich)
- **Hisoblar navbati** (`services/compute.py`, `app/worker.py`): kroy (CS / CL / CN), «Раскроить все», variantlar, PDF hisobot va
  CN fon ishlari `jobs` jadvaliga yoziladi (`MEBELIX_COMPUTE=queue`), alohida ishchi jarayonlar (`python -m app.worker -n 6`)
  bajaradi; PostgreSQL da `SKIP LOCKED` bilan olinadi, `NOTIFY mx_jobs` bilan darhol uyg'onadi, har 5 s yurak urishi. API o'zgarmagan
  (so'rov natija bilan qaytadi; xato — o'sha kod va matn). Ishchi 3 s ichida olmasa (`MEBELIX_COMPUTE_CLAIM_WAIT`) veb-jarayon
  vazifani qaytarib olib o'zi bajaradi — ishchilar to'xtasa ham server ishlaydi. Korxona (RLS) va til ishchiga o'tadi.
  Bosh jarayon qulagan ishchini qayta ishga tushiradi; bitta kompyuterda bitta (advisory lock), PID — `backend/worker.pid`.
- **Loyihalar ro'yxati** faqat ro'yxat ustunlarini o'qiydi (loyiha JSON i emas); `limit` / `offset` + `X-Total-Count`.
- **Tarix siqilgan:** yangi versiyalar `project_history.zdata` (zlib JSON), eskilari start-up da fonda siqiladi
  (`store.pack_history_backlog`). Ish bazasi: 1640 versiya, mazmuni bir xil (nusxada sha256 solishtirildi), tarix 82 → 31 MB.
- **Sozlama keshi jarayonlararo:** sozlama yozilganda `NOTIFY mx_settings` — boshqa jarayonlar asboblar jadvali / kromka belgilari
  keshini darhol tozalaydi (`services/notify.py`; avval TTL 2–3 s gacha eski qolardi).
- **Katalog kaliti — (korxona, id):** `catalog_items`, `catalog_images`; MES dan bir xil id turli korxonalarda bo'lishi mumkin
  (`db.ckey`, eski bazada start-up migratsiyasi `_composite_pk`).
- Sessiya darajasidagi advisory lock lar olingach tranzaksiya yopiladi (ochiq «idle in transaction» VACUUM ni to'sardi).
- Yuklama sinovi (ish bazasi nusxasi, 12 ta katta kroy bir vaqtda, 4 veb-jarayon): eski usul jami **168 list**, navbat + 6 ishchi
  **164 list** (bir jarayonda bir nechta kroy CPU ni bo'lishib, vaqt byudjetida kamroq variant sinardi); ro'yxat / loyiha ochish
  kechikishi o'zgarmagan (median ~30 ms). Testlar: `tests/test_scale_phase2.py`.
- Hali ochiq: korxonalar orasida adolatli navbat (bitta korxona hamma ishchilarni band qilmasin — 3-bosqich ta'riflari bilan),
  frontend loyihalar ro'yxatida sahifalash (hozir papka bo'yicha to'liq ro'yxat yetarli).
