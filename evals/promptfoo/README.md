# Promptfoo-proef: NGBSE, BALLMS 50, Shadowseed en Blindspot

## Werkelijk uitgevoerd

Op 6 november 2026 is **Promptfoo 0.125.1** uitgevoerd in GitHub Actions.
De provider `research_provider.py` importeert de **echte** Pythonmodules
en levert JSON-uitvoer aan twaalf controleerbare Promptfoo-assertions.

- [GitHub Actions-run 42287311199](https://github.com/E-AI-MODEL/NGBSE20.1/actions/runs/42287311199)
- [Ruwe Promptfoo-resultaten](https://github.com/E-AI-MODEL/NGBSE20.1/actions/runs/42287311199/artifacts/13537218867)
- Resultaat: **12 passed, 0 failed, 0 errors**
- NGBSE/BALLMS 50: 6 gevallen; Shadowseed: 6 gevallen.
- Node 24, Python 3.11; Shadowseed exact op `d9bb562f3df81d5bf1f4bc1389a8ca7e9605e6cd`.
- De NGBSE-branch met BALLMS 50 is `research/ballms50-foundation-20261106`; deze proef staat in een aparte concept-PR.
- Geen live modelaanroepen. De oude NGBSE-generator kreeg een vaste synthetische
  LLM-respons, zodat de selectie zonder providerwissel reproduceerbaar is.
- Geen wijzigingen aan productcode, Gate of Shadowseed-opslag.

## Wat betekent 12/12?

De tests controleren dat de huidige code zich gedraagt zoals de test verwacht.
Ze meten **geen** onderzoeksmeerwaarde, wetenschappelijke juistheid, onafhankelijk
oordeel of live modelprestatie. Een bewust bevestigde fout kan een geslaagde
karakteriseringstest opleveren.

### Aangetoond bij NGBSE

In het drukke vaste geval genereerde de oude vraaggenerator **19 kandidaten**,
waaronder de gesimuleerde LLM-vraag. De uitvoer bevatte alleen **de eerste tien**
en liet de LLM-vraag weg. In het rustige geval waren er vijf kandidaten en
werd de LLM-vraag wel geselecteerd. Dit is een concreet selectieprobleem,
geen bewijs dat die LLM-vraag inhoudelijk beter was.

BALLMS 50 houdt dubbele opgegeven bronherkomst apart van twee onafhankelijke
bewijzen, verwart een citaatovereenkomst niet met inhoudelijke ondersteuning
en behoudt het spoor van vragen die buiten het ingestelde budget vallen.
De opgaven zijn synthetisch.

### Aangetoond bij Shadowseed

De echte `_authority_signal_key` behandelt dezelfde externe `source_ref`
via SSOT en retrieval als één ondersteuningsidentiteit; herhaling gebruikt
een eigen type. Ongeverifieerde of tegengestelde signalen leveren geen
ondersteunende externe sleutel op.

De echte `decay_traces` halveerde een trace na 16 verstreken
beurtequivalenten, liet nul tijd ongemoeid en wees negatieve tijd af.
Hier is de lifecycle met een kleine in-memory testmanager aangeroepen.
Dit is **geen** end-to-end-test van opslag, Gate-policy of gebruiksbeslissingen.
De test bewijst ook geen beter vervolgonderzoek door Shadowseed.

## EAI Blindspot: voorbereid, niet uitgevoerd

`blindspot-cases.json` bevat acht synthetische gevalstudies met vooraf
vastgelegde grenzen voor de beoordeling. Ze behandelen onder meer:
prestatie versus leren, retentie, transfer, geciteerde maar niet dragende
bronnen, ontbrekend bewijs, positieve directe resultaten, feitelijke
docentcontrole en claims dat een model volledig vooroordelenvrij is.

**De EAI Blindspot ChatGPT-skill is niet als uitvoerbare provider
beschikbaar in deze GitHub Actions-run.** Een lokale imitatie van de
EAI-beoordelaar zou geen geldige test van de werkelijke skill zijn.
De acht gevallen worden daarom niet bij de twaalf uitgevoerde tests opgeteld.
Voor een geldige volgende proef moet dezelfde skillversie daadwerkelijk
worden aangeroepen en moeten de resultaten worden bewaard voor een
onafhankelijke beoordeling. Een standaard modelprompt met vergelijkbare
instructies is geen gelijkwaardige vervanging.

## Zelf herhalen

Op een omgeving met Node 24 en Python 3.11:

```sh
python -m pip install -e .
git clone https://github.com/E-AI-MODEL/shadowseed-pro.git shadowseed-promptfoo
git -C shadowseed-promptfoo checkout d9bb562f3df81d5bf1f4bc1389a8ca7e9605e6cd
python -m pip install -e ./shadowseed-promptfoo
export SHADOWSEED_SOURCE_DIR="$PWD/shadowseed-promptfoo"
export PROMPTFOO_DISABLE_TELEMETRY=1
export PROMPTFOO_DISABLE_UPDATE=1
npx --yes promptfoo@0.125.1 eval --config evals/promptfoo/promptfooconfig.yaml --no-cache
```

De vastgepinde commit en de testgegevens zorgen ervoor dat regressies
onder vergelijkbare voorwaarden terug te vinden zijn. Modelkwaliteit kan
pas worden vergeleken met meerdere echte modellen, identieke context,
blinde beoordelingen en een afgesproken beoordelingsmaatstaf.
