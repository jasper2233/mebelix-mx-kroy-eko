# Felder F4Classic (`.txt`, har karta — bitta fayl)

Manba: bitta namuna (3 karta, 2026-10-04). Generator: `backend/app/services/ppfmt/felder_f4classic.py`.

Paket: `<loyiha>_<material>_NNN.txt` (nom — lotin, transliteratsiya), kodlash cp1251, qator oxiri CRLF.
Etiketka fayllari (`<detal>.ZPL`) chiqarilmaydi — faqat kesim dasturi.

## Sarlavha (16 qator)
```
PR_VERSIONE = 12
PR_NOME = <fayl nomi kengaytmasiz>
PR_DESC =
PR_CLI = <loyiha nomi>
PR_MATER = <material>
PR_COMM =
PR_NORD =
PR_DIMX = <list o'lchami 0-daraja kesimlar o'qi bo'ylab>
PR_DIMY = <ikkinchi o'lcham>
PR_RIFX = <torsovka + propil>      (namunada 5 = 2 + 3)
PR_RIFY = <torsovka + propil>
PR_SPESS = <qalinlik>
PR_NPANN = <karta nusxalari>
PR_NPCAR = 1
PR_TIPO = 0
PR_TAGLI =
```
`PR_DIMX` — birinchi kesimlar (0-daraja) taqsimlanadigan o'q: polosalar eni bo'yicha kesilsa 1830 / 2750, uzunlik bo'yicha
(bosh kesim) bo'lsa 2750 / 1830.

## Kesim daraxti
* Konteyner: `<daraja>, <o'lcham>`
* Detal: `<daraja>, <o'lcham>, <R<n> yoki bo'sh joy>,  , <detal>[:<detal>…]` — ketma-ket bir xil detallar bitta qatorda
  (`1, 410, R3,  , 22:22:22`); bitta detal — `1, 2500,  ,  , 10`.
* Daraja 0 dan; bolalar — ota-onadan keyingi qatorlarda (pre-order). Chiqindi va qoldiq yozilmaydi.
* Bir xil konteynerlar birlashtirilmaydi (namunada `2, 100` + `3, 350` ikki marta alohida).

## Ochiq
`PR_NPCAR`, `PR_TIPO` ma'nosi (namunada 1 / 0); konteyner takrori (`R<n>`) qo'llanadimi — namunada uchramagan.
