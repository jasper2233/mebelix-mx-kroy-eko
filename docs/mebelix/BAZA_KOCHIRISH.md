# MX Kroy bazasi — lokal serverdan kroy.mebelix.uz ga ko'chirish

**Diqqat: bu faylda real mijozlar ma'lumoti bor.** Faqat yopiq (private) joyda saqlansin, ochiq repoga / chatga yuborilmasin.

| | |
| --- | --- |
| Qayerda | GitHub Release `baza-2026-11-05` (yopiq repo: `mebelix-mx-kroy-eko` va `MebeliX_Kroy`) |
| Fayl | `mebelix_pg_20261105_110527.dump` (≈ 48 MB) |
| Olingan vaqti | 2026-11-05 11:05 (Toshkent vaqti), xodimlar serveri ishlab turgan holatda |
| SHA-256 | `720107E4E5AFACE4FCDEB7CE5D1A7538266DE50C1AE16F0C6DE6511485EB8FDB` |
| Format | `pg_dump -Fc -Z 6` (custom), PostgreSQL **16.6** |
| Baza egasi (role) | `mebelix` (barcha jadvallar, RLS siyosatlari `mx_tenant`) |
| Kod versiyasi | `MebeliX_Kroy` `master` — `7adf294` (shu kod bilan mos) |
| Tarkib | 104 loyiha, foydalanuvchilar (parollar xeshlangan), sozlamalar, qoldiqlar ombori, tarix |

## Tiklash (server tomonida, MX konteyneri bazasiga)

```bash
# 1) PostgreSQL 16 (yoki yangiroq). Rol va baza:
psql -U postgres -c "CREATE ROLE mebelix LOGIN PASSWORD '<yangi parol>';"
psql -U postgres -c "CREATE DATABASE mebelix OWNER mebelix;"
# 2) Tiklash (egasi saqlanadi — RLS siyosatlari shu rolga bog'langan):
pg_restore -U postgres -d mebelix --no-acl -j 2 mebelix_pg_20261105_110527.dump
# 3) MX .env: MEBELIX_DB_URL=postgresql+psycopg://mebelix:<parol>@<host>:5432/mebelix
#    Backend ishga tushganda migratsiyalar o'zi qo'llanadi.
```

Tekshirish: `select count(*) from projects;` (≥ 104), MX ga kirib loyiha 1000107 «1275» ochilishi.

## Muhim

* **MES bazasiga tiklanmasin** — MX ning o'z konteyneri / o'z bazasi (`kroy-deploy.md` §5).
* Bu — 11:05 holati (korxona qarori, 2026-11-05): server yangilangach xodimlar shu baza bilan `kroy.mebelix.uz` da
  ishlashni davom ettiradi; 11:05 dan keyin lokal serverga kiritilgan ma'lumotlar serverga **qo'lda** kiritiladi.
* Ko'chirilgach xodimlar faqat `kroy.mebelix.uz` da ishlaydi, lokal server o'chiriladi (ma'lumot ikki joyda ajralib ketmasin).
* Hozir `kroy.mebelix.uz` dagi loyihalar (masalan «1281», № 1000005) shu tiklashda **almashtiriladi** —
  kerak bo'lsa avval ulardan eksport (`.project`) olinsin.
