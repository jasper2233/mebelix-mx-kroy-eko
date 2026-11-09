# MX Kroy yangilanishi — 2026-11-09 (server dasturchilari uchun)

**Nima o'zgardi:** faqat frontend (brauzer qismi). Baza, API va migratsiyalar o'zgarmagan, baza qayta tiklanmaydi.

| | |
| --- | --- |
| Kod | `MebeliX_Kroy` `master` va `mebelix-mx-kroy-eko` `eko-integratsiya` — shu fayl qo'shilgan commit |
| Yangilash | odatdagidek: kodni olish → `frontend` build (`npm ci && npm run build`) → konteynerni qayta ishga tushirish |
| Xodimlarga | yangilangach brauzerda **F5** (sahifani yangilash) |

## O'zgarishlar (xodim videolari, 2026-11-09)

1. **«Операции» jadvali:** operatsiya ↑ / ↓ bilan ko'chirilganda (Ctrl+↑ / Ctrl+↓ yoki tugmalar) kursor ko'chirilgan qator bilan
   birga yuradi. Avval kursor eski joyda qolib, keyingi bosish boshqa operatsiyani ko'chirardi.
2. **«Детали» jadvali (CS / CL / CN):** katakka TAB, Shift+TAB yoki strelka bilan o'tilganda matni belgilangan bo'ladi:
   * yozilsa — matn almashadi;
   * ← / → — matn ichiga kirib tahrirlash (eski matn saqlanadi);
   * Ctrl+C — katak matni nusxalanadi, Ctrl+V — fokusdagi katakka qo'yiladi (F2 siz).
   * tahrir paytida ↑ / ↓ — qiymat saqlanib, yuqori / pastki qatorga o'tiladi.
3. **Xuddi shu matn rejimi** «Операции», «Изделия», «Листы» (CS / CL / CN) va (O) jadvallarida ham (onlayn tizim bilan jonli
   solishtirildi). «Операции» da Ctrl+C — katak matni; o'ng tugma menyusidagi «Копировать» — butun qator (avvalgidek).
4. **Bitta o'zgargan odat:** matnli katakda → endi matn ichiga kiradi; qo'shni katakka — TAB.

## Tekshirish

* e2e: `frontend/e2e/video_1109_keys.spec.ts` + to'liq to'plam.
* Brauzerda: loyiha → «Операции» da qatorni Ctrl+↑ bilan 2 marta ko'tarish — o'sha qator ko'tariladi; «Детали» da nomga →, «#», Enter.
