# Altendorf (ELMO) — formatli arra stanogi (`.saw`)

Generator: `backend/app/services/ppfmt/saw_altendorf.py` (kalit `elmo3`). Manba: onlayn tizim fayllari (2026-10-24, 10 karta,
236 kesim, `post prtsessorlar/ONLINE_2026-10-24/`). Dastur nomi — 4 raqam (onlaynda so'raladi, standart `0001`).

Fayl: zip ichida har karta `<dastur>.<NNNN>.saw` (ASCII, LF). Tuzilishi:
* sarlavha: `;… postprocessor for Altendorf`, `VER (1)`, `ID (" ";1)`, `CANVAS (15;35;540;420)`, 14 ta `LABEL` (displey maydonlari, doimiy);
* `ACUT (blok;№;Label-Identifikation-<id>;<id>;* A;B * A * t;detal;d1;d2;soni;<soni>x;tirgak;o'lcham;S;A;H;<disk>;U;G;tirgak2;qoldiq+100;U;G;S;0;U;A;M;<t>;U;A)`;
* `BLOCK (№;x1;y1;x2;y2;"en";;;"bo'y";1;1)` — 0: butun list (torsovkadan keyin), keyin bo'linadigan bo'laklar;
* `LINE (blok;№;x1;y1;x2;y2;1;1;1;1;<propil>;1)` — har arra yurishi.

Qoidalar (onlayn fayl bilan tekshirilgan):
* koordinata (0,0) — chap-yuqori torsovka + propildan keyin; list = L − (torsovka + propil), W − (…);
* A — bo'lakning qat'iy o'lchami, B — kesishdan oldingi uzunlik, qoldiq = B − o'lcham; keyingi B = B − (o'lcham + propil);
* detal: `d1;d2` = detalning o'z l;w; blok: X;Y o'lchami (kesim o'qi bo'ylab + propil);
* bloklar stek tartibida (oxirgi yaratilgan — birinchi); ketma-ket bir xil detal — bitta ACUT («Nx»), LINE har biri uchun;
* oxirgi chiqindi kesilmaydi;
* `H;49` — «Высота пильного диска» sozlamasi.

Tirgak: «P» (bo'ylama) — o'lcham «Продольный упор» oralig'ida (2…1600) va o'lcham ≤ «Соотношение высота-ширина» (4) × A; aks holda
«L». Onlayn bilan 212/236 mos; 24 holatda (ko'pincha blokdagi oxirgi kesim) onlayn «L» tanlagan — ❓ qoidasi ochiq.
