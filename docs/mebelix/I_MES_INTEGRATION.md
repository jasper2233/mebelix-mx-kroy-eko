# I. MES integratsiyasi (siz o'zingiz moslaysiz — bu yerda interfeys va oqimlar)

GibLab'da ombor bilan almashinuv (1C) uchta amal orqali ishlaydi: **qoldiqlarni yuklash**,
**ishlatilganlarni hisobot qilish**, **yangi qoldiqlarni saqlash**. MebeliX xuddi shu mantiqni
REST orqali MES bilan qiladi.

## I1. Katalog (materiallar, narxlar)

`POST /api/catalog/sync` — MES → MebeliX (upsert). Element:
```json
{"id":"EG.H1215.ST22.18","parent_id":"egger-18","kind":"sheet","code":"EG.H1215.ST22.18",
 "name":"ЛДСП Ясень Кассино коричневый","unit":"m2","price":450000,"stock":37,
 "thickness":18,"length":2800,"width":2070,"grain":true,"image_url":null,"params":{}}
```
`kind`: folder (daraxt tuguni) | sheet | linear (profil) | edge (kromka) | surface | simple (furnitura).
UI «Товары» oynasi shu daraxtni ko'rsatadi (ishlab chiqaruvchi → qalinlik → materiallar).
Tanlash: `POST /api/projects/{pid}/operations/{oid}/material/{item_id}`.

## I2. Qoldiqlar ombori

```
MES ──POST /api/stock/remnants──▶ MebeliX       (ombordagi qoldiqlar: mes_id, material_code, L, W, qty, kind)
Kroychi: «Листы и остатки» → «ombordan yuklash»
   POST /api/projects/{pid}/operations/{oid}/remnants/load   → material kodi bo'yicha available qoldiqlar
                                                               listlar jadvaliga qo'shiladi (rezerv)
Kroy → natija (qoldiqlar birinchi ishlatiladi, kichigidan)
   POST /api/projects/{pid}/operations/{oid}/remnants/save   → ishlatilgan: used; ishlatilmagan: available;
                                                               yangi delovoy qoldiqlar omborga (mijoz olganlari ayirib)
MebeliX ──webhook remnants.saved──▶ MES          (MES o'z omborini yangilaydi)
```
Ma'lumot tarkibi (GibLab 1C protokolidagi kabi): *qoldiq ID, uzunlik, en, soni, [izoh]*; saqlashda —
*loyihadagi ID, ombor ID, list/qoldiq belgisi, delovoy belgisi, uzunlik, en, boshlang'ich soni, ishlatilgan soni, loyiha nomi*.

## I3. Buyurtma va holatlar

* `Project.mes_order_ref` — MES buyurtmasi ID si (loyiha yaratilganda yoki keyin bog'lanadi).
* Holatlar: 0 Не заказан → 1 Заказан → 2 Утвержден → 3 Готов.
* «Заказать»: `POST /api/projects/{pid}/order {executor, status}` → webhook `project.ordered`.
* MES tomonidan holat o'zgartirish: `PATCH /api/projects/{pid} {"status": 2}`.

## I4. Auth

MES SSO (JWT, `Authorization: Bearer`). Foydalanuvchi → `Project.owner`. Rollar: kroychi (tahrir),
texnolog (sozlamalar, postprotsessor), ko'ruvchi (faqat o'qish). v2 backend'da auth yo'q — Claude Code
middleware qo'shadi (dependency `current_user`).

## I5. Ishlab chiqarish uchun chiqish fayllari

* PDF hisobot va kroy kartalari (sex uchun).
* Etiketkalar (detal va qoldiq) — shtrixkod bilan; MES skanerlari shu kod orqali detalni kuzatadi
  (kesildi → kromkalandi → CNC → yig'ish).
* Postprotsessor — arra stanogi formati (qaysi stanok — siz aytasiz; namunaviy fayl bering).
* `GET /api/projects/{pid}/warehouse` — omborga talabnoma (MES da material chiqarish hujjati).

## I6. Integratsiya testlari (Claude Code yozadi)

1. Katalog sync → CS da material tanlash → narx va list o'lchami to'g'ri.
2. Qoldiq yuklash → kroy qoldiqni birinchi ishlatadi → save → holatlar to'g'ri, yangi qoldiqlar omborda.
3. Order → webhook yuborildi (mock server).
