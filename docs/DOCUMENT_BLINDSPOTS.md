# NGBSE: Blindspot-analyse van teksten en onderzoek

NGBSE begon met **Gap as a feature**: ontbrekende informatie kan iets vertellen over wat we nog niet weten. De bestaande OSINT-route blijft intact. Met `analyze-document` kan dezelfde gedachte ook worden gebruikt voor artikelen, onderzoeksverslagen, beleidsstukken en AI-antwoorden.

## Werken zonder externe diensten

Het eerste werkende pad leest een gestructureerd JSON-bestand met een onderzoeksvraag, bronpassages, te onderzoeken beweringen en mogelijke gaten. Er zijn geen API-sleutels nodig.

```bash
ngbse20 analyze-document --input examples/research_text_packet.json --out out/research_result.json
```

Het resultaat bevat een verslag per bewering, verwijzingen naar exacte bronpassages, eventuele ontbrekende of onvindbare verwijzingen, mogelijke claimgrenzen en voorgestelde onderzoeksvragen. De uitvoer is gestructureerde JSON, zodat een webomgeving of rapportgenerator deze later kan gebruiken.

Een bronquote telt alleen mee als de exacte passage in de aangeleverde brontekst voorkomt. **Daarmee is niet aangetoond dat de passage de conclusie ondersteunt.** De status `quote_anchored_not_verified` geeft dat expliciet aan. Zonder bron volgt `no_references`, niet `false`. Een ontbrekende verwijzing bewijst niet dat de uitspraak onjuist is.

## Procesblokken

| Stap | Uitvoering | Wat het niet beweert |
|---|---|---|
| Collect | Lees de bronnen en controleer hun identiteit | Geen automatische zoek- of bronverificatie |
| Enrich | Leg beweringen, claimtype en opgegeven passages vast | Geen automatische waarheidsclaim |
| Blindspot | Herken ontbrekende of onvindbare referenties, mogelijke claimoverschrijding en opgegeven mogelijke gaten | Geen bewezen afwezigheid |
| Verify | Controleer of exact genoemde passages voorkomen in exact genoemde documenten | Geen bewijs dat de passage inhoudelijk klopt of de claim ondersteunt |
| Reflect | Genereer gerichte toetsvragen, eventueel via BALLM | Geen bewezen nieuwe ontdekking |
| Report | Lever de beweringen, controles, vragen en status van elke stap | Geen overkoepelend betrouwbaarheidscijfer |

Een sterk causale of leerclaim bij uitsluitend observationeel materiaal krijgt een mogelijke `claim_boundary`. Dit is een **waarschuwing om de gevolgtrekking te toetsen**, geen geautomatiseerde methodologische beoordeling.

## BALLM optioneel inschakelen

Voor extra verkenning kan BALLM kandidaat-gaten voorstellen via de bestaande NGBSE-providerinterface:

```bash
ngbse20 analyze-document --input examples/research_text_packet.json --out out/with_ballm.json --ballm
```

Hiervoor is een daadwerkelijk ingestelde LLM-provider nodig. Het model krijgt maximaal acht bronfragmenten (maximaal 2.000 tekens per bron) en vijftien beweringen. Het moet maximaal drie ontbrekende relaties, alternatieve verklaringen of onderzoeksvragen als JSON voorstellen. De resultaten blijven **onbevestigde voorstellen**. Door het model verzonnen bronnen of citaten worden niet geaccepteerd als bewijs.

De bestaande `LLMClient` kan bij netwerkstoringen een fallbacktekst teruggeven. Deze nieuwe route behandelt die tekst niet als een geslaagde analyse: de uitvoer krijgt `status=partial` met een foutmelding. De CLI meldt een foutcode en bewaart de gedeeltelijke resultaten. Een provider kan extra kosten veroorzaken; de standaardroute doet geen netwerkverzoeken.

## Gebruik als Python-module

```python
import json
from ngbse20.research import analyze_document, BALLMDocumentProposer

packet = json.load(open("examples/research_text_packet.json", encoding="utf-8"))
result = analyze_document(packet)  # geen netwerk of taalmodel nodig

# Optioneel: injecteer een bestaande provider die .call(...) aanbiedt.
# result = analyze_document(packet, proposer=BALLMDocumentProposer(provider))
```

Een andere applicatie kan ook een eigen `proposer(question, sources, claims)` aanleveren. Zo blijven de brontoets en de vrije verkenning gescheiden. Een voorstel hoeft geen bronclaim te worden.

## Vervolg en beperkingen

Deze eerste uitbreiding vervangt de oude OSINT-pipeline niet. De huidige invoer vraagt om expliciet aangeleverde beweringen; volledig automatische extractie van claims en zelfstandig zoeken naar betrouwbare bronnen zijn **nog niet ingebouwd**. De optionele BALLM-call is er voor generatieve verkenning van ontbrekende mogelijkheden, niet om de broncontrole over te slaan.

Voor een kwaliteitsvergelijking zijn geblindeerde controles op nieuwe teksten nodig: zijn de gevonden gaten echt afwezig, zijn de vragen specifiek en relevant, en hoeveel schijnbare gaten ontstaan? Sla de originalen, voorstellen en reviewers apart op. De hier geleverde tests controleren het softwarecontract, niet de onderzoekskwaliteit.

Dit pad gebruikt eigen code in `ngbse20/research/document_blindspots.py` en leunt niet op de herimplementatie van EAIwork. Bij latere integratie moet rekening worden gehouden met de commerciële licentie van de bestaande NGBSE-repository.
