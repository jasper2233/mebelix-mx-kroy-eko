# Holz-Her NC-HOPS — `.hop` postprotsessori

> Manba: korxonaning o'z namunalari — `post prtsessorlar/ONLINE_2026-10-04/yangi_formatlar/holzher_nchops.zip` (**36 fayl**,
> bitta loyihaning 36 XNC operatsiyasi) va o'sha loyiha (`loyiha.project`). Faqat chiqish fayllari va loyiha o'qildi; kod
> noldan yozilgan. Buyruqlar ma'nosi bo'yicha internet tadqiqoti — `WEB_missing_formats.md` 9-bo'lim (u yerda nemischa
> nomlar: `Bohrung`, `HorzB`, `WZB`; namunada inglizcha: `DRILLING`, `HORD`, `TOOLD`).
>
> **Holat:** teshik (yuz, 4 qirra), freza konturi (chiziq + markazli yoy), orqa tomon (yuz teshigi) — tushunilgan.
> Generator `backend/app/services/ppfmt/holzher_nchops.py`; tekshiruv `tools/bench/pp_online_check_ima_hops.py`:
> **«namunadagidek» rejimda 36/36 bayt-ma-bayt**, standart rejimda 34/36 (2 faylda ikki `HORD` qatorining tartibi —
> 4-bo'limga qarang).

---

## 1. Fayl

| Xususiyat | Qiymat |
|---|---|
| Fayl | bitta XNC operatsiyasi = bitta `<XNC kodi>.hop`; takror kod — `<kod> (1).hop` |
| Tuzilishi | `;KALIT=qiymat` sarlavha → `VARS` → `START` → buyruqlar (har biri alohida qatorda) |
| Qator oxiri | CRLF, oxirgi qatordan keyin ham |
| Kodlash | namunada faqat ASCII (faylda detal nomi umuman yo'q); generator cp1251 |
| Sonlar | nuqta, ortiqcha nollarsiz, XNC dagi aniqlik saqlanadi (`95.6865`, `130.309`); generator 4 kasrgacha |
| Koordinatalar | X — XNC dagidek; **Y teskari: `DY − y`** (koordinata boshi pastki-chap burchak); chuqurlik **manfiy** |
| Orqa tomon | X ag'darilgan (`DX − x`), keyin o'sha qoidalar |

## 2. Sarlavha (hamma faylda bir xil, faqat o'lchamlar o'zgaradi)

```
;KOMMENTAR=
;DX=0.000
;DY=0.000
;DZ=0
;DIALOGDLL=Dialoge.Dll
;DIALOGPROC=StandardFormAnzeigen
;AUTOSCRIPTSTART=1
;BUTTONBILD=
;DIMENSION_UNIT=0
VARS
   DX := 336;*VAR*Dimension X
   DY := 100;*VAR*Dimension Y
   DZ := 16;*VAR*Dimension Z
START
FinishedPart (DX,DY,DZ,0,0,0,0,0,'',0,0,0)
CALL HH_Park ( VAL PARK:=3,X:=0,Y:=0)
```

Sarlavhadagi `;DX / ;DY / ;DZ` — doim nol; haqiqiy o'lchamlar `VARS` da. Detal nomi, soni, kromka — faylda yo'q.

## 3. Buyruqlar (XNC dasturi tartibida)

### 3.1 Teshiklar

```
TOOLD (501,_VE,_V,_VA,_SD,_ANF,'')                    parmalash asbobi — birinchi teshikdan oldin bir marta
HORD (x,y,z,d,-chuqurlik,10,0,<burilish>,0,2,0,0)     qirra teshigi
DRILLING (x,y,d,-chuqurlik,10,0,0,1,0,0,0,0)          yuz teshigi
```

| XNC buyrug'i | `HORD` x, y | burilish (parma yo'nalishi) |
|---|---|---|
| DrillLeft (x = 0) | `0, DY − y` | `0` (+X) |
| DrillRight (x = DX) | `DX, DY − y` | `180` |
| DrillTop (XNC y = 0 → fayl Y = DY) | `x, DY` | `270` — 4-bo'limga qarang |
| DrillBottom (XNC y = DY → fayl Y = 0) | `x, 0` | `90` |

`HORD` 3-parametr — balandlik `z`; `DRILLING` 5-parametr `10` — namunada hamma diametrda (3 … 35 mm) bir xil.

### 3.2 Freza konturi

```
TOOLM (8,_VE,_V,_VA,_SD,0,'')                                         freza raqami — asboblar jadvalidan
SP (x,y,-chuqurlik,<C>,0,_ANF,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)     kontur boshi (23 parametr)
G01 (x,y,-chuqurlik,0,0,0)                                             chiziq
G03C (x,y,-chuqurlik,cx,cy,0,0,0,0)                                   markazli yoy: XNC dir="true" → G03C, aks holda G02C
EP (0,_ANF,0)                                                          kontur oxiri
```

`SP` 4-parametr — radius korreksiyasi (XNC `C`; namunada `1`). Kontur nuqtalari XNC tartibida, Y va markaz Y teskari.

## 4. Namunadan farq (ataylab)

Namunada `DrillTop` (XNC y = 0 qirrasi) teshigi `HORD (x,0,…,90,…)`, `DrillBottom` — `HORD (x,DY,…,270,…)` yozilgan, ya'ni
bu ikki buyruqda Y teskari qilinmagan, holbuki yuz teshiklari, chap / o'ng qirra teshiklari va freza `DY − y` bilan yozilgan.
Nosimmetrik detalda teshik qarama-qarshi qirraga tushadi. Namunadagi detallarda yuqori va pastki teshiklar simmetrik
(bir xil x, diametr, chuqurlik), shuning uchun farq faqat ikki qatorning tartibida ko'rinadi.

Generator standart holatda **geometriya bo'yicha to'g'ri** yozadi (DrillTop → `Y = DY`, 270°);
`holzher_nchops.TB_AS_SAMPLE = True` — namunadagi kabi (tekshiruv skripti ikkala rejimni ko'rsatadi).

## 5. Asboblar («Инструменты» jadvali)

* Freza: `mill:front:<d>` — **raqam majburiy** (butun son ≥ 0). Bo'sh, `-1` yoki son bo'lmasa — xato (namuna dasturi ham
  raqamsiz fayl chiqarmaydi). `TOOLM (<raqam>,…)`.
* Parmalar: namunada hammasi «ko'rsatilmagan» (−1) edi → `TOOLD (501,…)` (501 — parmalash kallagi, parma diametr bo'yicha
  tanlanadi). Jadvalda parma raqami berilsa generator shu raqam bilan `TOOLD` yozadi va raqam o'zgarganda qayta chaqiradi
  (`drill:<tekislik>:<d>`, o'tuvchi yuz teshigi uchun avval `through:front:<d>`) — bu **faraz**, namunada yo'q.

## 6. Ochiq savollar (namunada yo'q)

1. DrillTop / DrillBottom Y yo'nalishi (4-bo'lim) — stanokda bitta nosimmetrik detal bilan tekshirish kerak.
2. Paz (Groove) — namuna yo'q; generator xato beradi (jim o'tkazib yuborilmaydi). Internetda `_nuten_frei_V5` /
   `_saege_*` makroslari uchraydi, lekin namuna dasturi nimani yozishi noma'lum.
3. O'tuvchi yuz teshigi: `DRILLING` 5-parametri (internet manbasida 10 — oddiy, 20 — o'tuvchi, 30 — d > 10; namunada d = 15 va 35
   da ham 10) — generator doim 10.
4. `HORD` `z` bazasi (yuqoridan / pastdan) — namunada hammasi qalinlik o'rtasida.
5. Parma raqami berilganda `TOOLD` qanday yoziladi (5-bo'lim); `501` barcha stanoklarda birmi.
6. `SP` dagi korreksiya kodlari (C = 0 / 2) va Y teskari bo'lgani uchun tomon almashadimi; kirish / chiqish parametrlari.
7. Chuqurligi qalinlikdan kichik freza, 180° dan katta yoy / to'liq aylana.
8. Teshik va freza aralash dasturda tartib va `TOOLD` / `TOOLM` qayta chaqirilishi (generator: dastur tartibi, asbob o'zgarganda).
9. Orqa tomondagi qirra teshigi va freza (X ag'darilgan — faraz).
10. Sarlavhada `;WZGV`, `;MASCHINE`, `;EXEVERSION` yo'q (internet namunalarida bor) — stanok talab qiladimi.
