# Masterwood MW310 — `.prg` postprotsessori (ishlov markazi)

Holat: **teshiklar (yuz + 4 qirra) va freza konturi**. Onlayn parallel sinov namunalari (bitta loyiha, 36 dastur) bilan
**36/36 fayl bayt-ma-bayt bir xil**. Paz (arra) namunada yo'q — chiqmaydi (xato beriladi).

Generator: `backend/app/services/ppfmt/masterwood_mw310.py` (kalit `mw310`). Tekshiruv:
`tools/bench/pp_online_check_mw_gcode_aes.py`; testlar: `backend/tests/test_ppfmt_mw_gcode_aes.py`.
Manba namunalar: `post prtsessorlar/ONLINE_2026-10-04/yangi_formatlar/mw310.zip` (repoga kirmaydi), loyiha — o'sha papkadagi
`loyiha.project`. Internet tadqiqoti: `WEB_missing_formats.md` 7-bo'lim (G-kodlar ro'yxati namunaga mos: `G100`, `G172`,
`G101`–`G103`, `G40`–`G42`).

## 1. Fayl

| Xususiyat | Qiymat |
|---|---|
| Nomi | `<XNC kodi>.prg`; bir xil kodlar — `kod (1).prg`, `kod (2).prg` |
| Bitta faylda | bitta XNC operatsiyasi |
| Kodlash / qator oxiri | ASCII, `CRLF` (oxirgi `%` dan keyin ham) |
| Sonlar | ortiqcha nollarsiz, 4 kasrgacha (`292.3135`, `12.5`, `34`) |

## 2. Tuzilish

```
%
|1                 ← nom (namunada bo'sh)
|2 0
|3 1
|4 <uzunlik dx>
|5 <qalinlik dz>
|6 <en dy>
|7 0 0 0 0
|8 0
|9 … |14           ← bo'sh qatorlar
:1
<amallar — XNC dasturi tartibida>
%
```

## 3. Amallar

Koordinatalar XNC dagidek (boshlanish chap-yuqori, X o'ngga, Y pastga); orqa tomon dasturi X bo'yicha ag'dariladi
(`X = dx − x`, namunada yuz teshigida tasdiqlangan).

| XNC | Qator | Izoh |
|---|---|---|
| `DrillFront` | `G100 X<x> Y<y> Z<chuqurlik> T<n>` | |
| `DrillLeft` (x=0) | `G182 X<chuqurlik> Y<dy − y> Z<z> T<n>` | Y teskari (nosimmetrik namunada tasdiqlangan) |
| `DrillRight` (x=dx) | `G183 X<chuqurlik> Y<dy − y> Z<z> T<n>` | |
| `DrillTop` (y=0) | `G184 X<x> Y<chuqurlik> Z<z> T<n>` | namunada x = dx/2 |
| `DrillBottom` (y=dy) | `G185 X<x> Y<chuqurlik> Z<z> T<n>` | |

Freza konturi (`MillStart` + `MillLine` / `MillArcCenter`):

```
G172 X<x0> Y<y0> Z<chuqurlik> S20 E10 T<n>
G42                                  ← C=1 (asbob o'ngda); C=2 → G41; C=0 → qator yo'q
G101 X<x0> Y<y0> Z<chuqurlik>
G102 X<x>  Y<y> I<cx> J<cy>          ← yoy, XNC dir="true"; dir="false" → G103; markaz absolyut; Y oldidan ikki probel
G101 X<x>  Y<y>                      ← chiziq
G40
G101 X<oxirgi x> Y<oxirgi y>         ← oxirgi nuqta takror (bitta probel)
```

## 4. Asbob raqamlari

Har amalda `T<n>` majburiy — «Настройки → Постпроцессоры → stanok → Инструменты» jadvalidan (`ppfmt/tooling.py`):
`drill:<tekislik>:<d>` (front / left / right / top / bottom), o'tuvchi yuz teshigi (chuqurlik ≥ qalinlik) —
`through:front:<d>` (bo'sh bo'lsa `drill:front:<d>`), freza — `mill:front:<d>`. Raqam ko'rsatilmagan bo'lsa generator xato
beradi (namunaviy tizim ham shunday rad etadi). Orqa tomon dasturida qirra tekisligi ag'darilgandan keyingi tomoni bo'yicha.

## 5. Ochiq savollar

1. `G184` / `G185` da X = x mi yoki dx − x mi (namunada teshik qirra o'rtasida) — `EDGE_X_FROM_RIGHT` konstantasi.
2. Qirra teshigida `Z` — yuqori yuzadanmi (z) yoki pastdanmi (dz − z): namunada z = dz/2.
3. `G172` dagi `S20 E10` nimani bildiradi (tezlik / kirish?) va stanok sozlamasidan olinishi kerakmi.
4. Korreksiyasiz kontur (C=0), orqa tomondagi qirra teshigi va freza — namunada yo'q, faraz bilan yozilgan.
5. Paz (`Groove`): `G180` / `G181` parametrlari noma'lum — namuna kerak.
6. `|1` (nom) va `|9`…`|14` qatorlari doim bo'shmi.
