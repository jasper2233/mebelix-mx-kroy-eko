# MES ↔ MebeliX Kroy: qoldiqlar ombori shartnomasi, v1 (2026-10-24)

## Maqsad va bo'linish

Korxona egasining qarori:
- Ombor ma'lumotlari **MES bazasida** saqlanadi.
- MebeliX Kroy (MX) o'z vazifasini, ya'ni kroyni bajaradi.
- MX da faqat quyidagilar bo'ladi:
  - qoldiqni bazaga **yuborish qoidasi** (foiz);
  - bazadan **topib qo'shish qoidasi**;
  - shular bo'yicha umumiy sozlamalar («Настройки → Правила остатков»).

| Kim | Nima qiladi |
|---|---|
| MX | Kroy qiladi. Kroydagi har bir qoldiqni foiz bilan baholaydi: olib qolinadimi yoki mijozga beriladimi. Bazadan mos qoldiq qidiradi (material sarfini kamaytiradiganini). Texnolog tasdiqlagach qoldiqni band qiladi va kroyga qo'shadi. Kroydan keyin MES ga kirim hujjatini yuboradi: olib qolinadigan qoldiqlar, mijozga beriladigan bo'laklar va buyurtmada ishlatilgan (sotilgan) ombor qoldiqlari. |
| MES | Qoldiqlar registrini yuritadi (o'lcham, material, qalinlik, holat, partiya, narx). «List arradan chiqdi» holatini kuzatadi. Kirim-chiqim jurnalini, mijozdan olib qolish narxini (m² narxi pastroq — saqlash xarajati), sotish hisob-kitobini va 1C ni yuritadi. |

## Biznes qoidalari (foydalanuvchi javoblari)

1. **Foiz** = qoldiq maydoni (list chetigacha, xom o'lcham) / shu materialning butun list maydoni × 100.
   - Foiz material turi bo'yicha beriladi (LDSP, LMDF, AKRIL, HDF …).
   - Kerak bo'lsa, aniq material uchun ham beriladi, va material qoidasi tur qoidasidan ustun turadi.
   - Faqat foiz hal qiladi (minimal tomon sharti yo'q).
2. Qoldiq ≥ foiz bo'lsa, korxona uni **olib qoladi** (omborga). Kichigi **mijozga beriladi**: hisobotda ko'rinadi, omborga yozilmaydi.
3. Olib qolingan qoldiq faqat **shu list arradan chiqqach** «mavjud» bo'ladi. MES bu signalni **har bir list (kroy kartasi)** uchun beradi. Undan oldin qoldiq «kutilmoqda» holatida ko'rinadi, lekin boshqa buyurtmaga berilmaydi.
4. Ombor qoldig'i mijozga **butunligicha** sotiladi va bazadan chiqariladi. Narx = qoldiq m² / list m² × list narxi.
   - Misol: list 5 m², qoldiq 2 m², mijozga 1.5 m² kerak. Bunda 2 m² sotiladi.
5. Mijozdan olib qolingan qoldiqning m² narxi pastroq. Uni MES hisoblaydi va ko'rsatadi. MX esa aniq ma'lumotni beradi: o'lcham, m², foiz, material, buyurtma, karta.
6. Material nomlari katta-kichik harf va bo'shliqlarsiz solishtiriladi: «LDSP KASHMIR SHAGREN» = «ldsp  kashmir shagren».
   - Material turi MES kodidagi guruhdan olinadi (`M-LD-…` → LDSP, `M-HD-…` → HDF), aks holda nomning birinchi so'zidan.

## MX → MES API (MES dasturchilari qiladi)

MX sozlamasi: «Правила остатков → Источник склада: База MES», manzil `mes_url` (masalan `https://mes.example.uz/api/v1/kroy`).
- Token: `Authorization: Bearer <MES_API_TOKEN>`. U bo'lmasa, `MES_WEBHOOK_TOKEN` ishlatiladi; ikkalasi ham MX serverining muhit o'zgaruvchilari.
- Javob vaqti chegarasi `MES_API_TIMEOUT` (standart 10 s).
- MES javob bermasa, MX xodimga 503 qaytaradi: «MES ombori bilan aloqa yo'q».

### 1. Qoldiqlarni qidirish
`GET {mes_url}/remnants?material=<nom>&code=<kod>&type=<LDSP>&thickness=16&status=available&linear=false`
`GET {mes_url}/remnants?ids=101,102`

Javob:
```json
{"items": [{"id": 101, "material_code": "LDSP KASHMIR SHAGREN", "material_name": "LDSP KASHMIR SHAGREN", "type": "LDSP",
            "length": 2500, "width": 650, "thickness": 16, "qty": 1, "qty_pending": 0, "status": "available",
            "sheet_area_m2": 5.0325, "reserved_project": null, "reserved_number": null, "note": "№4421 …",
            "source_number": 4421, "source_map": 2, "linear": false, "created_at": "2026-10-24T10:00:00"}]}
```
- `status` qiymatlari: `available` · `reserved` · `pending` (arradan chiqmagan) · `empty`.
- MX faqat `qty > 0` bo'lgan qoldiqlarni taklif qiladi.
- Material bo'yicha moslash (nom yoki kod, normallashtirilgan) MES tomonida bajariladi. MX ham natijani qayta filtrlaydi.

### 2. Band qilish (rezerv)
`POST {mes_url}/remnants/reservations`
```json
{"order": {"project_id": "5d797a939170", "number": 1000050, "name": "Shkaf", "mes_order_ref": null, "customer": ""},
 "ids": [101], "mode": "add"}
```
`mode` qiymatlari:
- `add` — texnolog qoldiqni kroyga qo'shdi;
- `remove` — ro'yxatdan olib tashlandi;
- `set` — MX loyihani saqlaganda yuboradi: buyurtmaning band qoldiqlari aynan shu ro'yxatga teng bo'ladi.

Boshqa buyurtmada band bo'lsa, javob `409` va quyidagi tana:
```json
{"conflicts": [{"id": 101, "order_number": 1000049}]}
```

### 3. Kroydan keyingi kirim / chiqim hujjati
`POST {mes_url}/remnants/intake`

Bu hujjat qachon yuboriladi:
- MX texnolog «Деловые остатки → склад» tugmasini bosganda;
- yoki «записывать автоматически» sozlamasi yoqilgan bo'lsa, kroydan keyin darhol.

```json
{"order": {...},
 "op": {"id": "20fbe24c7e8c", "name": "ldsp kashmir shagrin", "code": "", "type": "LDSP", "thickness": 16, "linear": false},
 "sheet_area_m2": 5.0325, "keep_percent": 30, "rule_source": "type", "sheet_price": 650000, "m2_price": 129160.5,
 "pieces": [{"map": 6, "length": 2534, "width": 1256, "qty": 1, "copies": 1, "percent": 63.2}],
 "client_pieces": [{"length": 1830, "width": 380, "qty": 1, "percent": 13.8}],
 "consumed": [{"id": 101, "qty": 1, "length": 2500, "width": 650, "area_m2": 1.625, "sale_price": 209885.8}]}
```
- `pieces` — olib qolinadigan qoldiqlar, har bir kroy kartasi bo'yicha alohida.
  - MES ularni `pending` qilib yaratadi.
  - Shu karta listi arradan chiqqanda `available` qiladi. Har nusxa (`copies`) uchun ulush hisoblanadi.
- `client_pieces` — mijozga beriladigan bo'laklar (faqat ma'lumot uchun).
- `consumed` — buyurtmada ishlatilgan ombor qoldiqlari. Ular mijozga sotiladi va bazadan chiqariladi.

Javob:
```json
{"intake_id": "IN-2026-0001", "ids": [205]}
```
MX `intake_id` ni natijada saqlaydi.

### 4. Bekor qilish
`POST {mes_url}/remnants/intake/{intake_id}/cancel`

Kroy natijasi o'zgarsa yoki o'chirilsa, MX shu so'rovni yuboradi. MES quyidagilarni bajaradi:
- kirimni bekor qiladi (hali ishlatilmagan qoldiqlar o'chiriladi);
- chiqimni qaytaradi.

## MES → MX (mavjud)

- **«List arradan chiqdi»** — mavjud yo'llar:
  - `POST /api/mes/scan/{kod}/done?count=1` (karta QR kodi skanerlanganda);
  - `PATCH /api/projects/{pid}/operations/{oid}/maps/{n}` `{"done_count": k}`.
  - MX `map.done` webhook voqeasini ham yuboradi.
  - Lokal ombor rejimida MX shu signal bilan o'z qoldiqlarini «mavjud» qiladi.
- **Lokal ombor rejimida sinxronlash** (MES ga o'tishdan oldin):
  - `GET /api/mes/remnants?since_id=N` — qoldiqlar holati va jurnal (N dan keyingi harakatlar).
  - `POST /api/mes/remnants/resend` — navbatdagi voqealarni qayta yuborish.
  - Webhook voqeasi `remnant.move` (`MES_WEBHOOK_URL`): `{event, company_id, move: {...}, remnant: {...}}`.
    - Harakatlar tartib bilan yuboriladi. MES qabul qilmasa, navbatda qoladi: server qayta ishga tushsa ham yo'qolmaydi.
  - Harakat turlari:

    | Tur | Ma'nosi |
    |---|---|
    | `kutish` | olib qolindi, arradan chiqishini kutmoqda |
    | `kirim` | omborga kirdi (mavjud) |
    | `chiqim` | buyurtmaga sotildi |
    | `qaytish` | chiqim bekor qilindi, qoldiq qaytdi |
    | `bekor` | kirim bekor qilindi |
    | `rezerv` | band qilindi |
    | `rezerv_bekor` | band bekor qilindi |
    | `mijozga` | foizdan kichik bo'lak mijozga berildi |
    | `qolda` | qo'lda qo'shildi, o'zgartirildi yoki o'chirildi |

## MX tomonida (qilingan)

- Qoidalar: `backend/app/services/remnant_rules.py`.
- Ombor manbasi va MES mijozi: `remnant_store.py`.
- Lokal ombor, holat va jurnal: `warehouse.py`; MES ga yuborish navbati: `remnant_outbox.py`.
- Sozlamalar sahifasi: `frontend/src/features/settings/RemnantRules.tsx`.
- CS belgisi «Использовать остатки со склада»: `CSCutParams.use_warehouse`.
- Taklif oynasi: `features/cs/RemnantOffer.tsx` (foiz, tejash m², mijozga narxi).
- Hisobot «Остатки»: qo'shimcha «%» va «На склад / Клиенту» ustunlari.
- Testlar: `tests/test_remnant_rules.py`, e2e `remnant_rules.spec.ts`.
