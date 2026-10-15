# T. W18 — (CL) W11 bo'shliqlari: «Свойства», etiketka, «Варианты», «До кроить», «Групповые действия»

Sana: 2026-10-02 · Asos: `T_W11_CL.md` §2 (qaror 14: «До кроить» va «Варианты» CL da yo'q edi), `T_W12_SP_PROGRAMMA.md` (GroupActions SP qoldirilgan).
Hamma yangilik mavjud W11 arxitekturasiga qo'shilgan; CL kroy algoritmi (default `OBJECTIVE = "material"`) o'zgarmadi.

## 1. Nima qilindi
| Band | Backend | Frontend |
|---|---|---|
| **Detal «Свойства»** (Ctrl+Space, ikki marta bosish «№», tugma) | `main.py::parts_batch_update` / `group_update`: CL da `width` / `grain` e'tiborsiz (eni — polosa eni, `Part.width = 0`) | `features/cl/ClPartProps.tsx` (CS `PartProperties` namunasida; chizma, bog'liq operatsiyalar, mahsulot/nom/tavsif/kod, soni, o'lchamlar jadvali faqat uzunlik ◁ ▷, (EL) 4 tomon, (SP) lits/orqa); `ClParts.tsx` |
| **Etiketka** | `label_vars.py`: manba operatsiyalari CS **va CL** (`LABEL_SOURCE_TYPES`); CL detalida `part.width`/`part.saw_width`/`part.dims` = polosa eni, `material.thickness` = `cl.thickness`; yangi **`strip.*`** o'zgaruvchilari (`index`, `total`, `copies`, `length`, `width`, `parts`, `fill`, `offcut`, `business`); `api_extra.py::mes_scan` CL detalida eni/qalinlikni to'g'ri qaytaradi | `LabelsPanel.tsx`: «Материал» ro'yxatida CL operatsiyalari ham |
| **«Варианты»** | `cl_calc.cl_variants` + `POST …/variants` CL uchun: `material` (kam material), `consumption` (kam sarf = material − деловой), `cuts` (kam kesim, LT), `max` («Максимальное» sifatda kam material; `cl.quality = max` bo'lsa tushiriladi); `cl_optimizer.optimize_linear(objective=…)`, `OBJECTIVES`; natijasi bir xil variantlarda `same_as` | `features/cl/ClVariants.tsx` (+ `cl.css`), `ClCut.tsx` tugma `btn-cl-variants`; tanlanganini qo'llash — `PUT …/result` (CLE bilan bir xil `validate_cl`) |
| **«До кроить»** | `cl_calc.run_linear(only_remaining=True)` → `_run_remaining`: `left_qty > 0` detallar qolgan polosalarga (ishlatilgani ayriladi, cheksiz — qoladi) optimallanadi, yangi kartalar eskilariga qo'shiladi, butun natija `cl_editor.rebuild` bilan qayta quriladi (karta/Д№ raqamlari, jami ko'rsatkichlar, tekshiruv; eski izoh/bajarilgan/torsovka saqlanadi, `manual` o'zgarmaydi); `POST …/optimize?only_remaining=true` | `ClCut.tsx`: `btn-cl-rest` (CS dagi kabi: kroy bor va «sig'magan» bor bo'lsagina faol) |
| **GroupActions: SP, CL** | `group_update`: `surface_face_op` / `surface_back_op` faqat mavjud SP (aks holda 400), nom/tavsif/kod/SP bog'lash kroyni eskirtirmaydi (qolgan maydonlar — avvalgidek) | `PartDialogs.tsx::GroupActions`: (SP) lits/orqa qatorlari; boshqa CS/CL operatsiyasiga ko'chirish qatori (`move-to`); CL operatsiyasida eni/tekstura/(GR) yashiriladi; `ClParts.tsx`: Ctrl+B va tugma `cl-parts-group` |

## 2. Qarorlar (bitta joyda o'zgaradi)
| Qaror | Joy |
|---|---|
| Variantlar to'plami va tartibi: `material, consumption, cuts, max` | `cl_calc.VARIANT_KEYS` |
| «cuts» maqsadi: (hammasi joylansin, **kam kesim**, kam material, ko'p деловой, kam xil karta …) | `cl_optimizer._score` (`objective="cuts"`) |
| Variant rejimida nomzodlar to'plami kengayadi (yaxshilanmagan SHP/FFD ham baholanadi) — faqat `objective` berilganda; oddiy «Раскроить» o'zgarmaydi (determinizm testlari o'tadi) | `cl_optimizer.optimize_linear` |
| «Eng yaxshisi» (dialogda oldindan tanlangan): hamma joylansin → kam material → ko'p деловой → kam karta → kam kesim | `ClVariants.bestVariant` |
| «До кроить»: qoldiq (Д№) raqamlari butun natijada qayta tartiblanadi; natija `manual` deb belgilanmaydi; yangi polosa qo'shilmasa hech narsa qo'shilmaydi (sig'magan detallar qoladi + «polosa yetmadi» ogohlantirishi) | `cl_calc._run_remaining` |
| `strip.offcut` — kartadagi **oxirgi** otxod/qoldiq uzunligi (net, mm); `strip.business` — shu bo'lak деловой mi | `label_vars.EnvBuilder._map` |
| CL «Свойства» da `width`/`grain` hech qachon serverga yuborilmaydi va server ham e'tiborsiz qoldiradi | `ClPartProps.NOT_SENT`, `main.py` |

## 3. Qilinmadi va nega
- **CL ga xos etiketka shabloni (tayyor)**: faqat o'zgaruvchilar qo'shildi; vizual redaktor — W15 (boshqa agent). CL etiketkasi hozir LB operatsiyasi orqali (manbasi CS **yoki** CL).
- **Eski qat'iy etiketka** (`/projects/{id}/labels`, `labels.py::labels_html`) va A4 da 4/6 karta miniatyurasi (`map_sheets_html`) — CS-only qoldi (1D karta SVG alohida: `cl_render`).
- **MES kroy variantlarini avtomatik tanlash** yo'q — tanlov xodimda.
- «Excel import ustun profili (CL)» — yetakchi (Excel bloki) qiladi.

## 4. Ochiq savollar
1. **Variantlar to'plami**: GibLab (SketchCut) da CL variantlari bormi/qanday? Hozir «kam material / kam sarf / kam kesim / maksimal sifat» — kerakli maqsadlar boshqacha bo'lsa `VARIANT_KEYS` / `_score` da almashtiriladi.
2. **«До кроить» ma'nosi CL da**: hozir «mavjud kartalar o'zgarmaydi, qolgan detallar qolgan polosalarga». GibLabda ro'yxatdagi qoldiq-polosa (omborga yozilgan) ham «qolgan» hisoblanadimi? (Hozir: ro'yxatdagi hamma polosalar, ishlatilgani ayrilgan holda.)
3. `strip.offcut` etiketkada qaysi otxod (net `W` yoki xom `R + T`)? Hozir net (`Offcut.length`).
4. Eski (qat'iy) etiketka va A4 karta miniatyurasi CL uchun kerakmi?

## 5. Testlar
`backend/tests/test_w18_cl.py` (17): detal xossalari (batch-update, CL himoyasi, nom kroyni eskirtirmaydi), GroupActions backend (SP validatsiya/olib tashlash, eskirtmaslik, CS→CL ko'chish SP saqlanadi), etiketka (`strip` guruhi, LB operatsiyasi CL detal/otxod soni, `EnvBuilder` qiymatlari, ifodalar, MES skaner), variantlar (to'plam, tartib/ishlash, `same_as`, qo'llash va `validate_cl`, `quality=max`, CS xulqi o'zgarmadi), optimizator `objective` (determinizm, hamma maqsad `validate_cl` dan o'tadi), «До кроить» (kartalar saqlanadi, raqamlash, ИК/Ост, bo'sh/to'liq holat, polosa yo'q holat, birlik testi).
