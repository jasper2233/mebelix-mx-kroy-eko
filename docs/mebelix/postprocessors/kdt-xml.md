# KDT XML — `.zip` → `<loyiha>_<material>.xml` + `<id>.emf` (PNG etiketkalar) postprotsessori

Holat: **to'liq** (kesish rejasi). 7/7 buyurtmada (G57 bilan solishtiriladigan) XML **ichki `id` raqamlari va `O<n>` qoldiq raqamidan tashqari bayt-ma-bayt** qayta yasaldi (3161 — to'liq bayt-ma-bayt, `id` lar bilan). Qolgan 3 buyurtma (3152, 3158, 3160) da tuzilma, geometriya va sonlar tekshirildi. Etiketka rasmlari (`.emf` nomli PNG) faqat tavsiflangan.

Manba: `post prtsessorlar/PILNIY APPARAT/KDT XML/*.zip` (10 ta: 3151–3161, 3154 yo'q).
Mos loyiha: `giblab project/3 Eldor/<NNNN> <mijoz>/<NNNN>_<mijoz>.project` (pastki chiziqli variant).

---

## 1. Fayllar

| Xususiyat | Qiymat |
|---|---|
| Tashqi fayl | `<loyiha nomi>_<material, bo'shliqlar→_>.zip`, masalan `3161_mijoz_LDSP_PIKARD.zip` |
| Zip ichida (papkasiz) | 1) `<zip nomi>.xml` — kesish rejasi; 2) har bir detal-qator uchun `<detal id>.emf` — **aslida PNG** (imzo `89 50 4E 47`), 464×484 px, 1-bit oq-qora etiketka rasmi. Tartib: xml, keyin rasmlar CS operatsiyasidagi detal tartibida (3151: `42.emf, 44.emf, 43.emf, …`) |
| Zip | deflate, flag `0x0808` |
| Soni | buyurtmaga 1 zip — faqat **birinchi CS operatsiyasi** (birinchi material) |
| XML kodlash | `UTF-8` (BOM yo'q), deklaratsiya `<?xml version="1.0" encoding="UTF-8"?>`; namunalarda faqat ASCII (detal nomlari XML ga yozilmaydi) |
| Qator oxiri | `LF`; har element alohida qatorda, chekinishsiz; **oxirgi `</project>` dan keyin yangi qator yo'q**; har `</panelN>` dan keyin bitta bo'sh qator |
| Sonlar | mm, o'nlik nuqta bilan, ortiqcha nolsiz (`2750`, `2.5`, `2264.5`) |

## 2. XML tuzilmasi

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project>
<panel1 l=".." w=".." material=".." [mcode=".."] code=".." thickness=".." saw=".." num="..">
<no.1 l=".." w=".." trim=".." x="0" y="0" layer="1" id="0">
<part cut=".." type="2|1|3" id=".." code=".." />
…
</no.1>
<no.2 …> … </no.2>
…
</panel1>
                                     ← bo'sh qator
<panel2 …> … </panel2>
…
<parts>
<part code=".." l=".." w=".." sq=".." uc=".." rc="0" />
…
</parts>
</project>
```
Teg nomlari raqamli (`panel1`, `no.17`) — standart XML sxemasi emas, lekin yaxshi shakllangan XML.

### 2.1 `<panelK>` — karta (raskroy sxemasi), K = 1..kartalar soni
| Atribut | Ma'no | Manba / misol |
|---|---|---|
| `l` | kartaning 1-daraja kesimlari bo'ylab o'lchami (polosalar shu o'q bo'yicha ketma-ket) | G57 `DIMY`; 2750 yoki 1830 |
| `w` | ko'ndalang o'lcham (polosa uzunligi) | G57 `DIMX` |
| `material` | `sheet/@name` (bo'shliqlar saqlanadi: `LDSP  PIKARD`) | |
| `mcode` | `sheet/@code` — **faqat list kodi bo'lsa** (3158: `115010`, 3161: `110052`; qolganlarida atribut yo'q) | |
| `code` | CS operatsiyasidagi list-part id | 3161: `12`, 3151: `79` |
| `thickness` | `sheet/@t` | 16 |
| `saw` | `swSawthick` | 3 (3159: 6) |
| `num` | shu sxema bo'yicha listlar soni («kitob») | 1 yoki 2; Σ = `cMaterialCount` (10/10 mos) |

### 2.2 `<no.N>` — bo'lak (tugun)
| Atribut | Ma'no |
|---|---|
| `N` | fayl bo'yicha uzluksiz raqam (kartalar orasida ham davom etadi) |
| `l` | bo'lakning kesim chizig'i bo'ylab uzunligi (= ota bo'lakning `w`) |
| `w` | bo'lakning kesib olingan o'lchami (= otadagi `part/@cut`) |
| `trim` | birinchi farzand kesimidan oldingi siljish (pastga qarang) |
| `x`, `y` | bo'lakning chap-past burchagi (karta koordinatasida, mm) |
| `layer` | 1 — butun karta, 2 — polosa, 3, 4, 5, 6 — keyingi darajalar |
| `id` | ichki identifikator (ota `part/@id` bilan bog'lanadi); ildiz `0` |

### 2.3 `<part>` — tugun ichidagi kesimlar (farzandlar), kesish tartibida
| Atribut | Ma'no |
|---|---|
| `cut` | kesib olinadigan bo'lak o'lchami (mm) |
| `type` | `2` — bo'lak, keyin yana kesiladi; `1` — tayyor detal; `3` — ishbop qoldiq (faqat `layer=1` da, oxirgi) |
| `id` | farzand tugunining `id` si |
| `code` | `type=1`: **loyiha detal `@id`**; `type=2`: bo'sh; `type=3`: `O<n>` |

Har bir `<part>` uchun alohida `<no.>` tugun bor (tayyor detal va qoldiq uchun ham — `trim="0"`, ichi bo'sh).

### 2.4 `<parts>` — detallar ro'yxati
`<part code="{detal id}" l="{l}" w="{w}" sq="{count}" uc="{count}" rc="0" />` — CS operatsiyasidagi tartibda, keyin qoldiq bo'lsa `<part code="O<n>" l=".." w=".." sq="1" uc="1" rc="0" />` (l — list uzunligi (2750) o'qi bo'yicha o'lcham, w — eni bo'yicha; 3151: `l="1595" w="1830"`, 3155: `l="2750" w="1105"`).
`sq` = loyiha `count`, `uc` = `sq` (ishlatilgan), `rc` = 0 (qolgan) — 10/10 faylda shunday.

## 3. Kesish rejasi qanday kodlangan

### 3.1 Daraxt va geometriya (barcha 44 karta, 0 xato)
* `layer` toq (1, 3, 5) tugunning farzandlari **Y** bo'ylab, juft (2, 4, 6) — **X** bo'ylab joylashadi.
* Birinchi farzand ota boshidan `trim` ga siljigan; har keyingisi `oldingi + cut + saw`.
* Farzand tugun: `l = ota.w`, `w = cut`; `x,y` — yuqoridagi qoida bo'yicha.
* `trim` qiymati (qat'iy qoida):
  * `layer` 1 va 2, farzandi bor → `cTrimL + saw` (namunada 5; kerf 6 da 8);
  * `layer ≥ 3`, farzandi bor → **2.5** (kerfdan qat'i nazar; 3159 da ham 2.5);
  * farzandsiz (detal, qoldiq) → 0.
* G57 dan farqi: `layer ≥ 3` bo'laklarda kesish 2,5 mm siljib boshlanadi (G57 FDS da siljishsiz) — ya'ni stanok bo'lak ichidagi ortiqcha joyni ikki tomonga bo'ladi deb taxmin qilinadi.
* Takrorlar (`QTARIP`) **yoyilgan**: G57 dagi `T5 498 ×2` bu yerda ikkita `<part cut="498" type="1" …>`.
* `layer` 6 gacha (G57 `TIPOTG=6` → `layer 5` dagi farzand) — 5-6 darajali daraxtlar to'liq saqlanadi.

### 3.2 Tugunlar tartibi (`no.N`)
Stek asosidagi chuqurlik bo'yicha o'tish: ildizni chiqar → farzandlarini to'g'ri tartibda stekka qo'y → stekdan oxirgisini ol. Natijada har tugundan keyin uning **oxirgi** farzandi keladi (3161: `no.1` ildiz, `no.2` = 3-polosa (100), `no.3` = uning detali, `no.4` = 2-polosa (352), `no.5` = shu polosaning oxirgi 300 lik bo'lagi…). `<part>` lar esa tugun ichida to'g'ri (kesish) tartibida.

### 3.3 `id` lar
Ichki hisoblagich (masalan 849962474…): to'g'ri pre-order tartibda har `<part>` ga +2; har 1-daraja (polosa) qo'shimcha +2 sarflaydi; yangi kartaga o'tishda +4 yoki +6 (qoida aniqlanmadi). Boshlang'ich qiymat har faylda boshqa. Stanok uchun faqat **noyoblik va ota-bola bog'lanishi** muhim deb hisoblaymiz (6-bo'lim, savol 2).

### 3.4 Ishbop qoldiq (`type="3"`)
Oxirgi polosadan keyin qolgan joy `rem = l − trim − Σ(cut + saw)` va `rem ≥ cMinDimRegWaste2` (500) bo'lsa (ko'ndalang o'lcham ≥ `cMinDimRegWaste1` = 1000), ildizga oxirgi farzand sifatida `<part cut="{rem}" type="3" code="O<n>"/>` qo'shiladi (+ bo'sh `<no.>` tugun, `layer=2`, `trim=0`). 7/7 qoldiqli faylda aynan shunday (3151: 1595; 3155: 1105; 3156: 893; 3157: 1548; 3158: 561; 3159: 1605; 3160: 1304); qoldiqsiz kartalarda `rem` 2..156 mm. O'lcham **trim qilinmagan** (loyihadagi business waste esa 5/10 mm kichik: 1595×1830 → 1590×1820). `n` raqami (O1, O30, O36, O13, O60, …) qoidasi noma'lum.

### 3.5 Etiketka rasmlari (`<id>.emf`, PNG)
Har detal-qator uchun bitta rasm (dona soniga emas). Tarkibi (3161 misolida, anonim):
* yuqorida shtrix-kod va `NC1: <XNC operatsiya kodi>V` (masalan `NC1: 316101_01_006V`) — faqat detalda XNC (parmalash) bo'lsa;
* `P: <buyurtma raqami> <mijoz>`, `M: <material>`, `Pd: <mahsulot nomi>`, `N: <detal nomi>` (kirill o'z holicha), `Sz: l x w x t`, `Nm: <CS operatsiyadagi tartib raqami> (<mahsulot tartibi>:<detalning mahsulot ichidagi tartibi>)` (3155 detal 37: `Nm:13 (1:32)` — operatsiyada 13-, 1-mahsulotda 32-qator), `K: <soni>`, `D` (parmalash belgisi), sana-vaqt (eksport vaqti);
* to'rt tomonda kromka nomi (`(A)1-19 Sasna` — EL operatsiyasi belgisi + kromka materiali) faqat kromkali tomonlarda; yon tomonlarda o'lcham raqamlari.
Rasm o'lchami 464×484, 1 bit. Stanok uni faqat chop etish uchun ishlatadi deb taxmin qilinadi.

## 4. Loyiha → fayl moslashuvi (tekshirilgan misollar)

| Loyiha | XML | Misol (anonim) |
|---|---|---|
| CS operatsiya, list | `panelK/@material, mcode, code, thickness, saw` | 3161: `material="LDSP  PIKARD" mcode="110052" code="12" thickness="16" saw="3"` |
| sxema listlari | `panelK/@num` | 3156: 1-karta `num="2"`, jami 8 = `cMaterialCount` |
| detal `@id` | `part[type=1]/@code`, `parts/part/@code`, rasm nomi | 3161: `01_006 Fasad` (id 7) → `code="7"`, `7.emf` |
| detal `@l,@w,@count` | `parts/part/@l,w,sq,uc` | 3155: `<part code="37" l="777" w="270" sq="8" uc="8" rc="0" />` |
| joylashuvlar soni | Σ(`type=1` barglar × `num`) = `sq` | 10/10 faylda 100 % (jami 503 barg) |
| `cTrimL + saw` | `trim` (layer 1–2) | 5; 3159: 8 |
| business waste | `type="3"`, `O<n>` | 3155: `<part cut="1105" type="3" … code="O1" />`, `<part code="O1" l="2750" w="1105" …/>` |

## 5. Minimal misol (sintetik, anonim)

List `LDSP OQ` 2750×1830×16 (list id 50), kerf 3, trim 2; detal 1: 1000×500 ×2, detal 2: 600×400 ×1. Bitta karta (`l=2750 w=1830`): polosa 1000 → 500, 500 (detal 1), 400 → 600 (detal 2); qolgan 1742 mm — qoldiq.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project>
<panel1 l="2750" w="1830" material="LDSP OQ" code="50" thickness="16" saw="3" num="1">
<no.1 l="2750" w="1830" trim="5" x="0" y="0" layer="1" id="0">
<part cut="1000" type="2" id="100" code="" />
<part cut="1742" type="3" id="112" code="O1" />
</no.1>
<no.2 l="1830" w="1742" trim="0" x="0" y="1008" layer="2" id="112">
</no.2>
<no.3 l="1830" w="1000" trim="5" x="0" y="5" layer="2" id="100">
<part cut="500" type="1" id="104" code="1" />
<part cut="500" type="1" id="106" code="1" />
<part cut="400" type="2" id="108" code="" />
</no.3>
<no.4 l="1000" w="400" trim="2.5" x="1011" y="5" layer="3" id="108">
<part cut="600" type="1" id="110" code="2" />
</no.4>
<no.5 l="400" w="600" trim="0" x="1011" y="7.5" layer="4" id="110">
</no.5>
<no.6 l="1000" w="500" trim="0" x="508" y="5" layer="3" id="106">
</no.6>
<no.7 l="1000" w="500" trim="0" x="5" y="5" layer="3" id="104">
</no.7>
</panel1>

<parts>
<part code="1" l="1000" w="500" sq="2" uc="2" rc="0" />
<part code="2" l="600" w="400" sq="1" uc="1" rc="0" />
<part code="O1" l="1742" w="1830" sq="1" uc="1" rc="0" />
</parts>
</project>
```
(+ zip ichida `1.emf`, `2.emf` etiketka rasmlari.)

## 6. Noaniq joylar va savollar

1. Faqat birinchi material eksport qilinadi — har material uchun alohida zip kerakmi?
2. `id` lar: stanok ularni faqat bog'lanish uchun ishlatadimi (bizning hisoblagich: istalgan noyob butun son)? Kartalar orasidagi +4/+6 sakrash qoidasi noma'lum.
3. `O<n>` qoldiq raqami (O1, O13, O30, O36, O60) qayerdan? Bizda `O1, O2, …` ketma-ket yozsak bo'ladimi? Qoldiq etiketkasi kerakmi?
4. `layer ≥ 3` da `trim="2.5"` — bu stanok sozlamasi (yarim kerf emas: kerf 6 da ham 2.5)mi? Uni loyihadagi qaysi parametrdan olish kerak?
5. Qoldiq mezoni: `rem ≥ 500` va eni ≥ 1000 (`cMinDimRegWaste2/1`) deb taxmin qilindi — 156 mm qoldiq yozilmagan, 561 mm yozilgan. Chegaraviy holat (500–1000 oralig'i, eni < 1000) namunasi yo'q.
6. Etiketka rasmlari (`.emf` nomli PNG): stanok aynan PNG ni kutadimi yoki haqiqiy EMF ham bo'ladimi? Etiketka maketi (464×484, maydonlar) majburiymi yoki o'zimiz loyihalashimiz mumkinmi? Shtrix-kod turi (Code128?) va mazmuni (`NC1: <XNC kodi>V` — `V` nima?).
7. Etiketka maydonlari (`Nm`, `K`, `D`, sana) stanokda o'qiladimi yoki faqat inson uchunmi? `D` belgisi faqat parmalash borligini bildiradimi?
8. Kasr o'lchamlar formati (`346.5`) — nuqta bilan deb kutilmoqda (`2.5`, `2264.5` uchragan).
