# NGBSE: drie varianten op dezelfde onderzoeksdossiers

**Stand 6 november 2026:** de eerste Promptfoo-test (12/12) controleert
technische eigenschappen. Dit experiment vraagt iets anders: wat leveren de
vragen op, en welke onderzoekspunten worden gemist?

## Opzet

- Zes fictieve, bevroren dossiers in `cases.json`.
- Drie varianten, elk met maximaal zes vervolgvragen:
  1. **Gewone prompt.** Het model krijgt het hele dossier en de vraag om
     toetsbare vervolgvragen te formuleren.
  2. **Historische NGBSE BALLM.** De bestaande
     `CuriosityGenerationEngine.generate_curiosity_questions` krijgt de
     geannoteerde `legacy`-featurevelden. Alleen zijn ingebouwde
     LLM-functie gebruikt dezelfde modelprovider.
  3. **BALLMS 50.** De echte `analyze`-functie verwerkt het dossier.
     De `proposer`-adapter laat hetzelfde model vragen voorstellen bij
     bestaande open onderzoekspunten. De bestaande regels en de selectie
     blijven intact.
- Model: `gpt-4.1-mini`, 0.4 temperatuur, 850 outputtokens als maximum.
  De oudere NGBSE-interface vraagt zelf 300 outputtokens.
- Er zijn hoogstens 18 modelaanroepen. Geen automatische herhaling.
  Boven een conservatief vooraf gereserveerd bedrag van $0,50 wordt
  een nieuwe aanvraag geweigerd. De bedragberekening is een
  begrensde schatting, geen facturatiegarantie.
- Willekeurige, vastgelegde uitvoervolgorde en geblindeerde
  beoordelingsrijen. Alle prompts, modelnamen, responses en tokenverbruik
  worden opgeslagen. Geen persoonsgegevens.

## Wat de drie varianten niet volledig gelijk maakt

De historische generator ontvangt alleen zijn historische featurevelden
en niet het volledige bronmateriaal. Dat hoort bij die bestaande
implementatie en is niet achteraf te repareren in deze proef. Een lagere
kwaliteit kan dus mede aan het beperkt aangeboden materiaal liggen.
Dit experiment vergelijkt **systemen zoals ze nu werken**, niet
uitsluitend de kwaliteit van hun vraagselectie bij identieke input.

BALLMS 50 geeft automatisch geformuleerde vragen altijd een eigen
hoog gewicht; modelvoorstellen staan later in de selectieronde. Deze
uitvoering laat zien of modelvoorstellen buiten het vraagbudget vallen.
Dat zegt op zichzelf niet of die voorstellen beter waren.

## Waarom negatieve gevallen?

R4 bevat twee afzonderlijk opgegeven bronherkomsten die dezelfde
waarneming ondersteunen. Hier mag het systeem niet automatisch een
bronhiaat melden. De opgegeven `origin_id` is uiteraard nog geen
onafhankelijk geverifieerde herkomst. Andere gevallen hebben dubbele
herkomst, ontbrekende bron, tegenstrijdige beweringen, mislukte
zoekacties of veel onbewezen claims.

## Beoordeling

De eerste Promptfoo-controles lezen uitsluitend **echte opgeslagen
modeluitvoer** en testen of antwoorden bestaan, niet gedupliceerd zijn
en binnen de vraaglimiet vallen. Een groene test bewijst geen
onderzoekskwaliteit.

`blind_review.csv` bevat vervolgens per anoniem antwoord ruimte voor:
- concreetheid en aansluiting op het dossier (0-2);
- een werkelijk onderscheidende onderzoekstoets (0-2);
- ongefundeerde premissen (aantal);
- herhaalde of overlappende vragen (aantal);
- bruikbaarheid voor vervolgonderzoek (0-2).

Beoordeel antwoorden zonder de variant te zien. Pas na de beoordeling
wordt `PRIVATE_MAPPING.json` gebruikt om de armnamen te ontsluiten.
Er is bewust geen kunstmatige totaalscore: bronfouten, de kwaliteit
van vragen en technische tracering zijn afzonderlijke uitkomsten.
We meten in deze eerste proef nog geen daadwerkelijke bronzoekacties
of de opbrengst van een vervolgonderzoek.

## Uitvoering en veiligheidsgrenzen

Eerst lokaal/CI zonder model:
```sh
python research/ngbse_quality/run_three_arm.py --preflight
```

Daarna via een geïsoleerde GitHub Actions-proef met een reeds
ingestelde, beschermde API-sleutel uit de onderzoeksomgeving.
Geen sleutel wordt in deze repository opgeslagen. De uitgevoerde
SHA van NGBSE wordt in die workflow vastgepind.

```sh
python research/ngbse_quality/run_three_arm.py \
  --output research-artifacts/ngbse-quality-v1
export NGBSE_QUALITY_ANSWERS_FILE="$PWD/research-artifacts/ngbse-quality-v1/answers.json"
npx --yes promptfoo@0.125.1 eval \
  --config research/ngbse_quality/promptfooconfig.yaml \
  --output research-artifacts/ngbse-quality-v1/promptfoo-results.json \
  --no-cache
```

De live-proef stopt expliciet bij ontbrekende sleutel,
providerfout, ontbrekend antwoord of kostenlimiet; geen stilzwijgende
overstap naar een andere provider. De gegevens worden niet als
geverifieerd onderzoek gepresenteerd.

**Releasebesluit:** geen wijziging aan productcode. NGBSE
en BALLMS 50 blijven op de oorspronkelijke branches.
