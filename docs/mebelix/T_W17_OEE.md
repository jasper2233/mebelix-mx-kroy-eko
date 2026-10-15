# T. W17 — OEE va ishlab chiqarish analitikasi

Maqsad: mebel pil markazi (va boshqa stanoklar) uchun **OEE = A × P × Q** va to'xtash tahlili. Hisoblash modeli, hodisa qabul qilish API si va
ko'rsatkichlar paneli — bizda (MebeliX Kroy). **MES integratsiyasi (REST klientlari, mijoz portali, GibSaw) — korxona MES jamoasiniki**: MES
stanok hodisalarini shu hujjatdagi API ga yuboradi. Kod: `backend/app/services/oee_calc.py` (formulalar, bazasiz), `oee.py` (baza, qabul qilish,
hisob fasadi), `oee_demo.py`, `api_oee.py`; UI — `frontend/src/features/oee/*`.

## 1. Kim nimani beradi

| Ma'lumot | Manba |
|---|---|
| Kroy kartasi geometriyasi: kesish uzunligi (LT), kesimlar soni (CT), kartadagi detallar, paketdagi listlar | **Bizdan** — sex rejimida karta «bajarildi» deganda avtomatik; MES `project_number + op_id + map_index` yuborsa — server kartadan o'zi to'ldiradi |
| Ideal sikl (stanok profili: tezlik, kesim almashinuvi, list yuklash) | **Bizdan** (`/oee/machines`); MES xohlasa hodisada `ideal_cycle_s` bilan ustun qo'yadi |
| Smena kalendari, tanaffuslar, bayram kunlari, sabab ro'yxati | **Bizdan** (sozlanadi); sabab **kodlari** MES bilan kelishiladi |
| Haqiqiy boshlanish/tugash vaqti, to'xtashlar (sabab kodi bilan), brak | **MES dan** (yoki sexdagi «To'xtash» tugmasi / qo'lda kiritish) |
| Stanok kaliti (`machine`) | Kelishiladi: MES shu kalit bilan yuboradi; avval stanok `/oee/machines` da yaratiladi |

Hodisa kelmasa ham tizim ishlaydi: `run` faqat tugash vaqti bilan (sex rejimi shunday yozadi) — boshlanish avvalgi hodisadan hisoblanadi (§5).

## 2. Umumiy qoidalar

* **Vaqt — UTC.** Hamma `start`/`end` maydonlari soat poyasi bilan: `2026-10-02T08:15:30Z` yoki `2026-10-02T13:15:30+05:00`. Poyasiz (naive) vaqt
  **rad etiladi** (400). Javoblarda doim `...Z`. Bazada naive UTC.
* **Smena soatlari** — zavod mahalliy vaqtida (`oee_config.tz_offset_min`, standart **+300** = O'zbekiston, yozgi vaqt yo'q). `from`/`to` sanalari
  (`2026-09-20`) ham zavod kunlari: `[00:00 mahalliy, keyingi kun 00:00)`, `to` kuni ham kiradi.
* **Idempotentlik — `external_id`** (≤ 100 belgi, butun tizimda noyob): bir xil kalit bilan qayta yuborish dublikat yaratmaydi.
  Mavjud hodisa **to'liq yangilanadi** (PUT-semantika: yuborilmagan maydon bo'sh bo'ladi); o'zgarmasa — `unchanged`. Boshqa tur yoki stanokka
  tegishli `external_id` — 409. MES o'z prefiksini ishlating: `mes:<id>`.
* **Ochiq to'xtash:** `downtime` ni `end`siz yuboring (`open: true`); keyin shu `external_id` bilan `end` qo'shib qayta yuboring. Yopilmasa — keyingi
  to'xtash boshlanishi, ish qayta boshlangan joy yoki «hozir» (qaysi biri avval) yopadi.
* Chegaralar: ommaviy ≤ **500** hodisa; `run` ≤ 24 soat; `downtime` ≤ 31 kun; kelajakdagi vaqt (>1 kun) — xato; yil 2000…2100.
* Noma'lum maydon — xato (`reasn` kabi xatolar jim o'tmasin). Izoh uchun `note` maydonini ishlating.
* Auth: mavjud JWT (`Authorization: Bearer …`). Hodisa yozish — «ko'ruvchi»dan boshqa hamma rol; sozlamalar (stanok/smena/sabab/konfiguratsiya) —
  `admin` / `technologist` (rolsiz token — to'liq huquq); demo — faqat `admin`. O'qish — hamma.

## 3. Hodisa sxemasi

`POST /api/oee/events` — tana: bitta hodisa `{...}`, yoki ro'yxat `[...]`, yoki `{"events": [...]}`.

| Maydon | Tur | Qaysi turlarda | Izoh |
|---|---|---|---|
| `type` | `run` \| `downtime` \| `reject` | hammasi (majburiy) | |
| `machine` | matn | hammasi (majburiy) | stanok kaliti (`/oee/machines`) |
| `external_id` | matn ≤100 | ixtiyoriy | idempotentlik kaliti |
| `end` | vaqt | `run`, `reject` majburiy; `downtime` ixtiyoriy | `run`: karta/list tugagan vaqt. `reject`: `start` berilsa ham bo'ladi (bitta nuqta) |
| `start` | vaqt | `downtime` majburiy; `run` ixtiyoriy | `run` da bo'lmasa — avvalgi hodisadan hisoblanadi |
| `qty` | int ≥1 | `run`, `reject` | `run`: kesilgan **listlar** soni (standart 1); `reject`: brak soni (standart 1) |
| `reject_qty` | int ≥0 | `run` | shu hodisadagi brak (birligi — `unit`) |
| `unit` | `part` \| `sheet` | `run`, `reject` | **brak birligi** (standart `part` — detal); `run.qty` har doim list |
| `parts` | int | `run` | ishlab chiqarilgan detallar jami (ma'lum bo'lsa) |
| `parts_per_sheet` | int | `run`, `reject` | listdagi detallar (birlik konvertatsiyasi uchun) |
| `cut_length_m`, `cuts`, `sheets_per_pack` | son | `run` | **bitta list** uchun kesish uzunligi (m), kesimlar soni, paketdagi listlar (std 1) |
| `ideal_cycle_s` | son >0 | `run` | MES bergan **bitta list** ideal sikli (s) — geometriyadan ustun |
| `sheet_area_m2`, `parts_area_m2`, `remnant_area_m2` | son | `run` | **bitta list**: list maydoni, detallar maydoni, qolgan деловой qoldiq maydoni (m²) — material KPI uchun (§5); karta havolasi bo'lsa server to'ldiradi |
| `reason` | sabab kodi | `downtime` majburiy; `reject` ixtiyoriy | `/oee/reasons` (turi mos: to'xtash ↔ brak) |
| `project_number`, `project_id`, `op_id`, `map_index` | | `run` | kartaga havola; `project_number+op_id+map_index` bo'lsa va geometriya berilmasa — server to'ldiradi |
| `note`, `source` | matn | ixtiyoriy | `source`: `mes`, `workshop`, `manual`, `demo` … (standart `api`) |

**Javob (bitta hodisa):** `201` + `{status:"created", id, event}`; `200` + `status: "updated" | "unchanged"`; xato — `400` (`detail`), `external_id`
to'qnashuvi — `409`.
**Javob (ommaviy):** `{created, updated, unchanged, errors, results: [{index, status, id | error}]}`. To'g'ri elementlar yoziladi, xatolilari
`results[i].error` da; **hammasi** xato bo'lsa — `422`. Qayta yuborish xavfsiz (idempotent).

## 4. Misollar (curl)

```bash
H='-H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN"'
# 0) stanok (bir marta; kalit — MES yuboradigan `machine`); tezliklar — ideal sikl uchun
curl -X POST $BASE/api/oee/machines $H -d '{"key":"saw1","name":"Pil markazi 1","kind":"saw","pp_key":"scm_wincut",
     "cut_speed_mm_s":1000,"cut_change_s":5,"sheet_load_s":25}'

# 1) karta kesildi (boshlanish va tugash MES dan; geometriya kartadan avtomatik)
curl -X POST $BASE/api/oee/events $H -d '{"type":"run","machine":"saw1","external_id":"mes:run:8841",
     "start":"2026-10-02T08:12:00Z","end":"2026-10-02T08:19:40Z","qty":2,"parts":24,"parts_per_sheet":12,"reject_qty":1,
     "project_number":1230,"op_id":"00ef93199c0c","map_index":3}'

# 2) to'xtash (sabab kodi bilan); avval ochiq, keyin yopiladi
curl -X POST $BASE/api/oee/events $H -d '{"type":"downtime","machine":"saw1","external_id":"mes:dt:55","reason":"breakdown",
     "start":"2026-10-02T09:00:00Z"}'
curl -X POST $BASE/api/oee/events $H -d '{"type":"downtime","machine":"saw1","external_id":"mes:dt:55","reason":"breakdown",
     "start":"2026-10-02T09:00:00Z","end":"2026-10-02T09:35:00Z"}'                 # -> status: updated

# 3) keyinroq topilgan brak
curl -X POST $BASE/api/oee/events $H -d '{"type":"reject","machine":"saw1","end":"2026-10-02T11:05:00Z","qty":3,"unit":"part","reason":"chip"}'

# 4) ommaviy (≤ 500) — navbatni to'g'ridan-to'g'ri yuborish
curl -X POST $BASE/api/oee/events $H -d '{"events":[ {...}, {...} ]}'

# 5) natijalar
curl "$BASE/api/oee/summary?machine=saw1&period=today" $H
curl "$BASE/api/oee/series?period=last14&group_by=day" $H            # hour | shift | day | week
curl "$BASE/api/oee/downtime-pareto?from=2026-09-20&to=2026-10-02" $H
curl "$BASE/api/oee/export.csv?kind=events&period=last7" $H -o oee_events.csv     # events | series | pareto
```

Sex rejimi (planshet, `#/sex`): `POST /api/mes/scan/{qr}/done?machine=saw1` — karta «bajarildi» + avtomatik `run` hodisasi (stanok berilmasa —
yagona faol «saw» stanogi; aniqlanmasa hodisa yozilmaydi, skaner baribir ishlaydi); «To'xtash»: `POST /api/oee/downtime/start {machine, reason, note?}`,
`POST /api/oee/downtime/stop {machine}`, `GET /api/oee/downtime/open?machine=`.

Davr: `period` = `today | yesterday | last7 | last14 | last30 | this_week | this_month` yoki `from`/`to` (sana yoki soat poyasi bilan vaqt). Standart — `last7`.

## 5. Hisoblash modeli (konstantalar kodda: `oee_calc.py` va `oee.py` boshi; sozlanadiganlari — `oee_config`)

```
OEE = A × P × Q
A = ish vaqti / rejalashtirilgan vaqt
    rejalashtirilgan = smena − tanaffuslar − rejalashtirilgan to'xtashlar (sabab `planned=true`)
    ish vaqti        = rejalashtirilgan − rejalashtirilmagan to'xtashlar − `idle` (hodisasiz bo'shliq ≥ idle_gap_s)
P = ideal vaqt / ish vaqti, ≤ 100 %      ideal vaqt = Σ ideal sikl × list soni
Q = (ishlab chiqarilgan − brak) / ishlab chiqarilgan      (birlik: sheet | part — `unit` sozlamasi)
```

**Ideal sikl** (bitta list, `ideal_cycle()`): `(LT / tezlik + CT × kesim_almashinuvi) / paketdagi_listlar + list_yuklash`. Standart profil: **1000 mm/s**
(60 m/min), **5 s/kesim**, **25 s/list**. Hodisada ideal manbasi ustuvorligi: `ideal_cycle_s` > geometriya > stanokning `ideal_unit_s` (kromkalash va
boshqa kesishsiz stanoklar) > noma'lum (P ga kirmaydi, ogohlantirish `no_ideal`; ma'lumi bo'yicha P ish vaqtini proporsional kamaytirib hisoblanadi).
Misol: LT 12 m, 20 kesim → 12 + 100 + 25 = **137 s**.

**Vaqtni sinflash** (rejalashtirilgan vaqt ichida, ustuvorlik bilan):
1. rejalashtirilmagan `downtime` (kesishsa — **avval boshlangan** g'olib; bir soniya ikki sababga yozilmaydi); rejalashtirilgan to'xtash esa rejalashtirilgan
   vaqtdan chiqariladi (tanaffus bilan kesishsa ikki marta ayirilmaydi);
2. `run` oralig'i: boshlanishi bor — `[start, end]`; yo'q — `[end − min(avvalgi_hodisa_oxirigacha, run_cap_factor × ideal), end]`, smena boshigacha
   kesiladi; ideal ham yo'q — nuqta (davomiylik 0);
3. qolgan «bo'sh» bo'laklar: **< idle_gap_s** (standart **5 min**) — ish (karta almashtirish); **≥** — `idle` to'xtash (Paretoda «yozuvsiz bo'shliq»;
   `/oee/gaps` + «Назначить причину» orqali haqiqiy to'xtashga aylantiriladi).
Karta tugash vaqti `(a, b]` oraliqqa tegishli (17:00:00 da tugagan karta 08–17 smenasiniki). Smenadan tashqari ishlab chiqarish **OEE ga kirmaydi**
(`outside_shift` ogohlantirishi); `include_overtime=true` bo'lsa rejalashtirilgan vaqtga qo'shiladi. Qisman smenadan tashqaridagi hodisa vaqt ulushiga
mos prorata kreditlanadi.

**Chegaraviy holatlar:** rejalashtirilgan vaqt 0 (kalendar yo'q / bayram) → A, P, Q, OEE = `null` (xato emas; `no_calendar`); smena bor, hodisa yo'q → A = 0,
OEE = 0; hodisasi umuman yo'q stanok yig'indiga kirmaydi (`no_data`, «0 %» emas); P > 100 % → 100 % (`performance_raw` xomi, `p_capped`); ochiq to'xtash
yuqoridagi qoida bilan yopiladi (`open_downtime`); Q ∈ [0, 1]; bir nechta stanok — komponentlar yig'indisi (vaqt bo'yicha vaznli), o'rtacha foiz emas.
Bo'laklash (`group_by`): komponentlar bo'lak bo'yicha kesiladi — bo'laklar yig'indisi = butun davr; soat bo'yicha ≤ 31 kun.

**Rang/yorliq (doimiy, `BAND_LOW=0.60`, `BAND_HIGH=0.85`):** < 60 % qizil «Past», 60–85 % sariq «O'rtacha», ≥ 85 % yashil «Yuqori» (UI da rang + belgi + so'z).
**Material samaradorligi** (qoldiq/otxod %) — OEE ning bir qismi **emas**, alohida qo'shimcha KPI (`material` — `/oee/summary`, `/oee/dashboard`, har stanok uchun;
panelda «Материал» qatori): `fill = Σ detallar maydoni / Σ list maydoni` (F), `waste = (list − detallar − деловой qoldiq) / list` (qayta ishlatiladigan qoldiq otxod emas).
Oynada kesilgan (smenadan qat'i nazar), maydon ma'lumoti bor `run` hodisalari bo'yicha, `qty` vaznli; ma'lumot yo'q bo'lsa `fill/waste = null` (0 emas).

## 6. Sozlamalar (`/api/oee/config`, `oee_config` jadvali)

| Kalit | Standart | Ma'nosi |
|---|---|---|
| `tz_offset_min` | 300 | zavod vaqti = UTC + shu daqiqa |
| `idle_gap_s` | 300 | hodisasiz bo'shliq chegarasi (s) |
| `run_cap_factor` | 3.0 | boshlanishi noma'lum run: ish ≤ koeffitsient × ideal |
| `unit` | `sheet` | ishlab chiqarilgan birlik (list/karta yoki detal) |
| `include_overtime` | false | smenadan tashqari ish rejalashtirilgan vaqtga kirsinmi |

Boshlang'ich ma'lumot (birinchi murojaatda, bir marta): 15 sabab (10 to'xtash: sozlash, nosozlik, material kutish, operator yo'q, buyurtma yo'q, asbob almashtirish,
tozalash, **rejali xizmat (planned)**, **tanaffus (planned)**, boshqa; 5 brak: yorilish, o'lcham, material nuqsoni, shikast, boshqa) va namunaviy smena (Du–Sha 08:00–17:00,
tanaffus 12:00–13:00). Smena: haftalik shablon (hafta kunlari, mahalliy soat, tanaffuslar, amal qilish sanalari); `end ≤ start` — yarim tundan o'tadi; stanokka alohida
smena berilsa — faqat shular (umumiylar o'rniga); `kind: "off"` — dam olish/bayram (sana oralig'i).
`GET /api/oee/machines/{key}/suggest` — bog'langan postprotsessor stanogi sozlamasidan tezlik taklifi (SCM `vel_avanz` — birligi **m/min** deb taxmin qilinadi, `oee.SCM_FEED_IS_M_MIN`);
avtomatik qo'llanmaydi.

## 7. UI joylashuvi (qaror)

* chap panel **«MES» → «OEE»** (MES integratsiyasi yoqilganda, mavjud karkas paneldagi yangi punkt) va
* **«Настройки → Производство (OEE)»** — MES sozlamasi o'chiq bo'lsa ham ochiladi (OEE MES ga bog'liq emas: hodisalar sexdan va qo'lda ham keladi).
Ikkalasi bir xil sahifa va bir xil holat (davr/stanok tanlovi). Tablar: Обзор (4 ta ko'rsatkich, trend, Pareto, stanoklar va smenalar jadvali), События (ro'yxat, qo'lda
qo'shish/tahrir, sababsiz bo'shliqlar), Станки, Смены, Причины, Параметры. Sex rejimida (`#/sex`) stanok tanlovi va «Остановка» tugmasi (OEE stanoklari bo'lsa ko'rinadi).

## 8. Demo (faqat ko'rsatish/test)

`POST /api/oee/demo-seed?days=14` va `DELETE /api/oee/demo-seed` — faqat `MEBELIX_DEMO=1` muhitida va `admin` roli. 2 sintetik stanok (`demo-saw-1`, `demo-saw-2`) × 14 kun,
`source=demo`; haqiqiy hodisalarga tegmaydi. Bir xil `seed` — bir xil natija.

## 9. Ochiq savollar (hozirgi standart — konstanta/sozlama orqasida)

1. **Smenadan tashqari ishlash** OEE ga kirsinmi? Hozir — yo'q (`include_overtime=false`).
2. **«Buyurtma yo'q» (`no_work`)** rejalashtirilmagan to'xtash deb hisoblanadi (A ni tushiradi). Klassik OEE da bu «rejalashtirilmagan vaqt» (TEEP) — sabab sozlamasida «Плановая»ni yoqsangiz o'zgaradi.
3. **Idle chegarasi** 5 min — korxona uchun to'g'rimi? Karta almashtirish odatda qancha?
4. **Ideal tezliklar:** haqiqiy stanokning kesish tezligi, kesim almashinuvi va list yuklash vaqtlari (standart 1000 mm/s, 5 s, 25 s — taxmin); SCM `VelAvanz` birligi (m/min?).
5. **Ishlab chiqarilgan birlik:** list/karta (standart) yoki detal? Brak MES da detal sonida keladimi?
6. Sabab kodlari ro'yxati MES bilan kelishilsinmi (hozir 15 ta standart; MES o'zinikini `/oee/reasons` orqali qo'shadi)?
7. MES hodisalari oqimi: `external_id` formati va kechikib kelgan hodisalarni tuzatish tartibi.
8. PostgreSQL yo'li sinalmagan (SQLite da testlangan; jadvallar/indekslar standart SQLAlchemy).

## 10. Testlar

`backend/tests/test_oee_w17_calc.py` (formulalar qo'lda hisoblangan misollarda: A=0.9, P=0.8333, Q=0.9667, OEE=0.725; start-less hodisalar; chegaraviy holatlar),
`..._shifts.py` (kalendar, tanaffus, yarim tun, zona, bayram, guruhlash, Pareto), `..._api.py` (qabul qilish, idempotentlik, ommaviy, validatsiya, rol, CRUD, CSV, demo),
`..._workshop.py` (sex «bajarildi» → hodisa, To'xtash), `..._migration.py` (eski bazaga CREATE/ALTER).
