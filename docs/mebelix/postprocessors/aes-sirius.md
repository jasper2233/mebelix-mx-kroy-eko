# AES Sirius (G-kod) postprotsessori — parmalash stanogi

Holat: **qisman — faqat x=0 / x=dx qirra teshiklari**. Yagona namuna (336×100×16 detal, chap va o'ng qirrada bittadan
Ø4.5 teshik) bilan **1/1 fayl bayt-ma-bayt bir xil**. Yuz teshigi, y=0 / y=dy qirra teshigi, paz va freza uchun namuna
yo'q — generator ular uchun **xato beradi** (G-kod o'ylab topilmaydi).

Generator: `backend/app/services/ppfmt/aes_sirius.py` (kalit `aes_sirius`). Tekshiruv:
`tools/bench/pp_online_check_mw_gcode_aes.py`; testlar: `backend/tests/test_ppfmt_mw_gcode_aes.py`.
Manba namuna: `post prtsessorlar/ONLINE_2026-10-04/yangi_formatlar/aes_sirius_one.zip` (repoga kirmaydi).
Internet tadqiqoti (`WEB_missing_formats.md` 10-bo'lim): dialekt tavsifi topilmagan.

## 1. Fayl

| Xususiyat | Qiymat |
|---|---|
| Nomi | `<XNC kodi>` — kengaytmasiz |
| Kodlash / qator oxiri | ASCII, `CRLF` (oxirgi `M02` dan keyin ham) |
| Koordinatalar | kamida bitta kasr raqam (`30.0`, `-20.0`, `120.5`); `R` parametrlari — ortiqcha nollarsiz |

## 2. Tuzilish

```
{           336              }     ← izoh-rasm (ichki eni 28): uzunlik (11 probeldan keyin)
{     ++++++++++++++++   1   }     ← en — raqamlari ustun bo'ylab (1, 0, 0 = 100); birinchi qator «+», keyingilari «#»
{     ################   0   }
{     ################   0   }
{   O                        }     ← koordinata boshi belgisi
{                            }
(R170=336) { LENGTH
(R169=100) { WIDTH
(R173=168) { PUSHER POSITION       ← uzunlik / 2
L M7
M12
<teshiklar>
M85
M88
L GFINPRO.ISC
M02
```

Har qirra teshigi:

```
M85
M87
M06T<n>                 ← asbob raqami («Инструменты»)
M16
G0 Z30.0
G0 X<x0> Y<y>           ← x0: qirradan 20 mm tashqarida (−20 yoki uzunlik + 20)
M<n>                    ← asbob raqami bilan bir xil son (namunada T9 → M9, T7 → M7)
G0 Z-<z>
G1 X<x1> F2000          ← x1: chuqurlik (X = 0 tomoni) yoki uzunlik − chuqurlik
G0 X<x0>
G0 Z30.0
```

Namunada birinchi teshik X = 0 tomonida `T9` (jadvalda «o'ng Ø4.5»), ikkinchisi X = uzunlik tomonida `T7` («chap Ø4.5»)
bilan parmalangan, XNC dasturida esa avval `DrillLeft`, keyin `DrillRight`. Generator buni **X = uzunlik − x** deb oladi
(`MIRROR_X`): avval XNC o'ng qirrasi teshiklari (stanokda X = 0), keyin chap qirra; asbob — teshikning XNC tomoni bo'yicha
(`drill:left:<d>` / `drill:right:<d>`), MW310 dagi kabi. Orqa tomon dasturi yana X bo'yicha ag'dariladi.

## 3. Ochiq savollar

1. **X yo'nalishi**: namuna simmetrik (ikkala teshik y = 50, bir xil diametr / chuqurlik). «X = uzunlik − x, asbob o'z
   tomoni bo'yicha» o'rniga «X = x, asbob qarama-qarshi tomon qatoridan, dastur tartibida» ham xuddi shu faylni beradi.
   Nosimmetrik namuna yoki stanokda sinov kerak.
2. `M<n>` haqiqatan asbob raqamimi (yoki tomonga bog'liq o'zgarmas `M9` / `M7`)? Sarlavhadagi `L M7` doim shundaymi?
3. `G0 Z-<z>`: z yuqori yuzadanmi yoki pastdan (namunada z = qalinlik / 2).
4. **Qisqichlar**: namunaviy tizim ayrim detallarni «Обработка задевает прижимы!» deb rad etgan — qoida noma'lum
   (qisqich o'rni / eni, `R173` bilan bog'liqligi). Generatorda bunday tekshiruv yo'q — stanokda sinash shart.
5. Yuz teshiklari, y=0 / y=dy qirra teshiklari, paz, freza — namuna yo'q (hozir xato beriladi).
6. Rasmdagi uzunlikning joylashuvi (4 xonali son), eni 3 xonali bo'lmagan detal (qatorlar soni) — faraz; izoh, stanokka
   ta'sir qilmaydi.
7. Bir tomonda bir nechta teshik tartibi (hozir dastur tartibida), har teshikda `M85 M87 M06 M16` takrorlanishi.
