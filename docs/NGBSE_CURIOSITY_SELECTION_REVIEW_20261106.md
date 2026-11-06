# NGBSE 20.1: vraagselectie na de echte modelproef

**Datum:** 6 november 2026. **Status:** proef op aparte branch, niet gemerged.

## Werkelijke aanleiding

De zes fictieve onderzoeksdossiers van
[NGBSE onderzoeks-PR #66](https://github.com/E-AI-MODEL/NGBSE20.1/pull/66)
zijn eerder met echte `gpt-4.1-mini`-aanroepen getest. De historische
generator kreeg zes antwoorden met elk drie genummerde modelvragen.

[Parserreparatie PR #67](https://github.com/E-AI-MODEL/NGBSE20.1/pull/67)
herkent die vragen nu, maar de bestaande selectie nam per definitie
de eerste tien voorstellen. Veel dekkingvragen konden hierdoor
vragen uit andere families verdringen.

## Nieuw, zonder wijziging van het oude returntype

- De gewone `generate_curiosity_questions()` blijft een lijst met
  maximaal tien vragen teruggeven. Het model wordt nog maar één keer
  aangeroepen.
- Bij meer dan tien verschillende vragen selecteert de engine
  om beurten één voorstel per familie. Binnen dezelfde familie
  sorteert het algoritme de meegegeven categorie `curiosity_level`
  vóór latere kandidaten. Die categorie is geen gevalideerde
  maat voor vraagkwaliteit.
- Exacte duplicaten, hoofdletter- en spatieverschillen worden
  geweerd. Dit is **geen** semantische duplicaatdetectie.
- `generate_curiosity_questions_with_trace()` levert zowel de
  geselecteerde vragen als de uitgesloten kandidaten met reden:
  `duplicate_question`, `empty_or_invalid_question` of
  `question_budget`.
- Zijn er hoogstens tien unieke vragen, dan blijft de oorspronkelijke
  volgorde bestaan.
- Zonder gerapporteerde signalen genereert de engine niet langer
  automatisch vragen over falende beveiligingsmaatregelen of
  gebrekkige data. Een onafhankelijke modelvraag kan nog wel
  worden opgenomen.

## Gemeten op dezelfde zes bestaande modelantwoorden

[Oorspronkelijke parserreplay](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/42290392109):
[gewijzigde selectie, zonder nieuwe API-aanroepen](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/42292919933).

| Meetpunt | Alleen parserreparatie | Nieuwe selectie |
| --- | ---: | ---: |
| Echte modelvragen herkend | 18/18 | 18/18 |
| Modelvragen binnen de eerste zes | 13/18 | 14/18 |
| Modelvragen binnen maximaal tien | 18/18 | 17/18 |
| Algemene fallbackvragen zonder feitelijk signaal (R2 + R4) | 8 | 0 |

De verandering is beperkt. Vooral in dossier R6 komt één
modelvraag eerder aan bod. Daar staat tegenover dat nog één
modelvraag buiten de uiteindelijke lijst van tien valt,
omdat er meer ruimte wordt gegeven aan andere vraagfamilies.

Deze cijfers meten **selectie**, niet welke vraag het meeste
onderzoek oplevert. We kennen de toegevoegde waarde van de
gemiste en gekozen vragen nog niet.

## Technische controle

[GitHub Actions-run](https://github.com/E-AI-MODEL/NGBSE20.1/actions/runs/42292818466)
is geslaagd op Python 3.11 en 3.12: 27 tests per versie.
Die omvatten behoud van de bestaande lijstinterface, parser,
deduplicatie, verdeling bij hoge aantallen, foutafhandeling,
negatieve gevallen en de bestaande BALLM-tests.

## Wat nog niet is opgelost

- De oude modelprompt ontvangt vooral samenvattingsvelden
  in plaats van bronteksten. Vraagkwaliteit blijft daardoor
  beperkt door de informatie die het model krijgt.
- De basisaanroep toont nog maximaal tien vragen zonder
  afzonderlijk instelbaar budget; bij een scherm dat er zes
  toont, worden nog steeds de eerste zes gebruikt.
- De spreiding voorkomt dominantie door één categorie, maar
  optimaliseert niet de inhoudelijke opbrengst.
- BALLMS 50 heeft een andere selectieroute. Deze wijziging
  verandert die route niet.
- De onafhankelijkheid van bronherkomsten in BALLMS 50
  wordt nog niet inhoudelijk gecontroleerd.
- Een geblindeerde menselijke beoordeling en daadwerkelijke
  vervolgonderzoeken zijn nodig vóór een kwaliteitsclaim.

**Besluit:** mechanische reparatie is controleerbaar, maar
de vraagkwaliteit van NGBSE is nog niet bewezen. Productiecode
op main is ongewijzigd.
