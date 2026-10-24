# (CN) Нестинговый раскрой — ishlov markazlari (NCStudio, KDT GCode, WoodWOP, TPA, BiesseWorks)

Generator: `ppfmt/cn_nest.py` (guruh `nest`, kalitlar `cn_ncstudio`, `cn_kdt_gcode`, `cn_woodwop`, `cn_tpa`, `cn_biesseworks`).
Manba: onlayn tizim (2026-10-24): sinov loyihasida CN operatsiya, 2 variant («Выступ снизу» 0 / 0.5; 1 / 2 list). Tekshiruv:
`tools/bench/pp_online_cn.py` — onlayn yo'llardan 15/15 fayl bayt-ma-bayt.

Har karta — `F<n>.<ext>`, har doim zip. Yo'llar — asbob markazi siniq chiziqlari (list koordinatalari, chap-yuqoridan).
Chuqurlik = qalinlik + «Выступ снизу».

| Format | Xususiyatlar |
|---|---|
| NCStudio `.NC` | `G0 X Y` → `Z-<chuq> F<Z tezlik>` → `G1` faqat o'zgargan koordinata; ishdagi birinchi G1 da Z ham; `G0 Z<otvod>`; ` M04 S` (bo'shliq bilan); `M05`, `M30` |
| KDT GCode `.NC` | boshlash/tugatish bloklari (sozlama); `M6 T`, `M04 S`, `G43 H`; Y = y − list eni; kirish `G1 Z−выступ`; chiqish `G0 Z(t+20)`; `M5` |
| WoodWOP `.mpr` | `[H`, `[001`, `<100 \WerkStck\`; har yo'l `]k` (KP + KL) va `<105 \Konturfraesen\` (EA/EE, TNO, ZA = −выступ); oxirida `!` |
| TPA `.TCN` | EDICAD sarlavha; `W#89` (boshlanish, `#3=−chuq`), `W#2201` (chiziq); `W#1100` matn makrosi (onlayndagidek); SIDE#1…6 |
| BiesseWorks `.bpp` | `ROUT` (P raqami fayllar bo'ylab davom etadi), `START_POINT`, `LINE_EP`, `ENDPATH`; qator raqami 15, +11, +11, +10…, +12, +6 |

Farq: onlayn tizim qo'shni detallar orasidagi umumiy chiziqni bir marta kesadi; MX har detal konturini alohida aylanadi.
Panhans, Excitech — onlayn CN ro'yxatida yo'q.
