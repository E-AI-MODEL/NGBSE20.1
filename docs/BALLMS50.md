# NGBSE BALLMS 50: onderzoeksversie

Dit is een **nieuwe, geïsoleerde onderzoeksroute** in de bestaande NGBSE-repository. De oudere NGBSE- en BALLM-code blijft ongewijzigd. De naam BALLMS 50 duidt voorlopig een onderzoeksversie aan, geen release of bewezen verbetering.

## Wat deze eerste versie doet

BALLMS 50 leest een JSON-onderzoeksdossier met bronfragmenten, beweringen, aangeleverde bronverwijzingen, eerder uitgevoerde zoekpogingen en open vragen.

De engine registreert:

- Ontbrekende bronverwijzingen en verwijzingen die niet letterlijk overeenkomen met de aangeleverde bron.
- Mogelijk gebrek aan onafhankelijke bronbevestiging. Het aantal verschillende herkomsten wordt gebaseerd op `origin_id` zoals aangeleverd; die onafhankelijkheid is **niet geverifieerd**.
- Ontbrekende brontypen die de onderzoeker expliciet heeft opgegeven.
- Gerapporteerde tegenspraken. De engine beoordeelt zelf niet of twee uitspraken elkaar werkelijk tegenspreken.
- Zoekacties zonder resultaten of met fouten. Een lege zoekuitkomst is **geen bewijs van afwezigheid**.
- Nog onbeantwoorde vragen.

Ieder onderzoekspunt krijgt een stabiele identifier. De engine maakt daar vragen bij en selecteert ze per type, zodat één type niet vanzelf alle plaatsen bezet. Kandidaten die buiten het budget vallen blijven in de uitvoer staan.

Het dossier bevat **bronvingerafdrukken**, de status van bronverwijzingen, vragen, afgewezen kandidaten en een trace. De engine voert nog geen nieuwe zoekopdrachten uit. Een eventueel aangeleverd zoekresultaat heet `reported` en nooit `verified_execution`.

## Uitvoeren

Vanaf de repositorybasis, met Python 3.11 of nieuwer:

```bash
PYTHONPATH=src python -m ngbse20.ballms50 examples/ballms50_case.json --out /tmp/ballms50-out.json
PYTHONPATH=src pytest -q tests/test_ballms50.py
```

Voor de eerste proef is geen API-sleutel nodig. De uitvoer bevat `analysis_status` voor de analyse, `investigation_status` voor werkelijke vervolgacties en `trace` voor de fasen. Die statussen mogen niet tot één succesvlag worden samengevoegd.

De `analyze(case, question_budget=12, proposer=None)`-functie accepteert optioneel een geïnjecteerde vraaggenerator. Deze mag extra vragen **voorstellen**, met verwijzing naar bestaande gap-ID's. Een falende generator levert `analysis_status=partial`; de gewone vragen blijven beschikbaar. Er is bewust nog geen modelprovider in deze route aangesloten.

## Invoercontract

- `sources`: objecten met uniek `id`, `text`, eventueel `type`, `origin_id`.
- `claims`: objecten met `id`, `text`, eventueel `references` (`source_id`, `start`, `end`, `quote`) en `contradicts`.
- `required_source_types`: **door de onderzoeker gevraagde** brontypen, geen automatisch opgelegde norm.
- `search_attempts`: `id`, `query`, `status` uit `complete`, `no_results`, `error`, `skipped`.
- `unknowns`: `id`, `question`, optioneel `reason`.
- `probe_results`: uitsluitend terugmeldingen over geselecteerde vraag-ID's; geen bewijs van technisch uitgevoerde acties.

Offsets verwijzen naar Python-tekstposities, niet automatisch naar PDF-posities. Een exact overeenkomende bronpassage betekent niet dat een bewering inhoudelijk wordt ondersteund. `semantic_support` en `truth_status` blijven `NOT_EVALUATED`.

## Lessons learned uit andere repositories

De Superagent-technische kennisinventaris is gebruikt als vertrekpunt. Voor deze ontwikkeling zijn actuele implementaties van vijf relevante projecten opnieuw gelezen. De volledige inventaris van andere repositories is **geen bewijs** dat iedere bron inhoudelijk is gecontroleerd of elke techniek hier moet worden overgenomen.

| Herkomst | Concrete les | Status in BALLMS 50 |
|---|---|---|
| [Oude NGBSE](https://github.com/E-AI-MODEL/NGBSE/blob/main/ngbse/blindspot/generator.py) | Ontbrekende resultaten en bronhiaten als onderzoekspunt registreren, niet stil overslaan | Ingevoerd |
| [BALLM 20.1](https://github.com/E-AI-MODEL/NGBSE20.1/blob/main/src/ngbse20/ballm/curiosity_generator.py) | Meerdere vraagtypen behouden, maar vaste volgorde met top-10-afkap niet herhalen | Ingevoerd via gespreide selectie en zichtbare afwijzingen |
| [EAIwork](https://github.com/E-AI-MODEL/EAIwork-/blob/main/packages/evidence/src/observe.ts) | Bronhandle, exacte tekst en feitelijke betekenis uit elkaar houden | Ingevoerd voor bronpassages; semantische beoordeling nog niet |
| [ShadowSeed Pro](https://github.com/E-AI-MODEL/shadowseed-pro/blob/main/src/shadowseed/recurrence_clustering.py) | Eén bron die tweemaal wordt aangeleverd is geen onafhankelijke bevestiging | Ingevoerd voor opgegeven `origin_id`; bronherkomst nog niet geverifieerd |
| [ShadowSeed Agent Lab](https://github.com/E-AI-MODEL/shadowseed-agent-lab/blob/main/shadowseed_agent_lab/harness.py) | Kandidaten, toegestaan gebruik en uitvoering van vervolgonderzoek onderscheiden | Vragen zijn alleen voorstellen; agentlus later |
| [EAT_me](https://github.com/E-AI-MODEL/EAT_me/blob/main/eatme/evaluator.py) | Eerst observeren, later pas ingrijpen | Alleen observatie; geen automatische vervolgstappen |
| [eainesy](https://github.com/E-AI-MODEL/eainesy/blob/main/src/lib/eainesy/verification-gate.ts) | Een technische controle bewijst niet de juistheid van de betekenis | Ingevoerd als gescheiden statussen; formele verificatie niet overgenomen |
| [PiM](https://github.com/E-AI-MODEL/project-pim/blob/main/src/lib/pim/egressGuard.ts) | Controleer de concrete uitvoer vóór een externe actie | Nog niet van toepassing op deze offline module; vereist vóór toekomstige export/egress |
| [Door010](https://github.com/E-AI-MODEL/door010/blob/main/packages/orchestration/src/execution-tools.ts) | Voorgesteld, bevestigd, in wachtrij en daadwerkelijk uitgevoerd zijn verschillende gebeurtenissen | Eerste scheiding ingevoerd; outbox en externe uitvoering later |
| [EAI-lab](https://github.com/E-AI-MODEL/EAI-lab-/blob/main/src/eai_lab/event_store.py) | Simulatie en echte gebeurtenissen technisch scheiden | Demo- en terugmeldgegevens zijn alleen ingevoerd materiaal; duurzame eventstore later |

## Wat nog niet is gebouwd

- Automatische documentextractie uit PDF, Word en websites; de huidige invoer is een JSON-dossier met aangeleverde tekst.
- Gerichte zoekacties met uitvoerregistratie, bronherkomstcontrole en een begrensde tweede onderzoeksronde.
- Een echte LLM-provider, brongebonden vraaggeneratie en vergelijking tegen een gewone prompt.
- Semantische beoordeling van bronsteun of feitelijke tegenspraak.
- Persistente opslag, bevoegdheidsbeheer, een gebruikersinterface en een release.

**Onderzoekshypothese:** brongebonden vragen uit concrete hiaten kunnen tot nuttiger vervolgonderzoek leiden dan vragen uit alleen een algemene samenvatting. Dit is geen gemeten resultaat. De volgende proef gebruikt dezelfde dossiers en een vooraf vastgelegde beoordelingsmethode, met aparte telling van technische fouten en inhoudelijk nuttige vragen.

## Testbewijs

De engine is lokaal geïmporteerd en getest met Python en pytest, zonder netwerk. De eerste 15 gerichte tests slagen. Dat zijn deterministische contract- en regressietests, geen blinde kwaliteitsvergelijking of bewijs dat echte zoekacties werken. GitHub CI wordt afzonderlijk beoordeeld.

NGBSE 20.1 blijft het bestaande pakket. In deze onderzoeksbranch wordt niets automatisch gemerged of gepubliceerd.
