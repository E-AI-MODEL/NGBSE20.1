# NGBSE: één volledige kenniskloof getest tegen een gewone AI-chat

Datum: 6 november 2026 · Status: daadwerkelijk uitgevoerde proef, géén release

## Vraag

Heeft NGBSE meer te bieden dan een gewone AI-chat die een onderzoeksvraag
en dezelfde waarnemingen krijgt?

We hebben één afgebakende technische bewering getoetst:
**“Python 3.12 kan in geen enkele omgeving distutils importeren.”**

## Werkelijke onderzoekscyclus

De onderzoeksadapter gebruikt de bestaande BALLMS 50-functie `analyze()`.
Die identificeerde bij de start drie open punten: ontbrekend bewijs,
geen beschikbare bronnen en een expliciete open vraag.

Vervolgens voerde een aparte, op deze casus geschreven uitvoerder
drie werkelijke acties uit op GitHub Actions, Python 3.12.16:

| Actie | Uitvoering | Resultaat |
|---|---|---|
| A1 | `python -I -S -c "import distutils"` | Fout: `ModuleNotFoundError` |
| A2 | `python -I -c "import setuptools; import distutils; print(distutils.__file__)"` | Gelukt; bestand in `setuptools/_distutils` |
| A3 | Ophalen `https://docs.python.org/3.12/whatsnew/3.12.html` | HTTP 200, bronhash en twee relevante passages |

De uitvoer bevat een voor- en nameting, action-ID's, exacte commando's,
returncodes, stderr, bronhashes en een revisie van de conclusie.

**NGBSE's begrensde conclusie:** de absolute uitspraak is door A2 weerlegd
voor de geteste omgeving. Python 3.12 bevat `distutils` niet meer in de
standaardbibliotheek, maar het pakket `setuptools` kan een versie aanbieden.
Andere configuraties zijn niet getest.

Bewijs: [eerste echte onderzoeksrun](https://github.com/E-AI-MODEL/NGBSE20.1/actions/runs/42295045392)
en [eindrun met gelijke bewijsinformatie](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/42295728049).

## Vergelijking met een gewone AI-chat

De gewone chat kreeg eerst exact dezelfde vraag, zonder testresultaten.
Hij stelde een proef voor met meerdere Python-omgevingen en noemde de
mogelijkheid van een uitzondering. In de tweede beurt kreeg hij alle
ongewijzigde bewijsregistraties uit A1, A2 en A3, **inclusief de
uitgevoerde commando's**, maar niet NGBSE's conclusie.

- Model: `gpt-4.1-mini-2025-04-14`.
- Twee echte Responses-aanroepen, beide volledig voltooid.
- Kostenproxy in de baseline: **$0,018546** (geen geverifieerde factuur).
- De gewone chat trok dezelfde juiste conclusie, benoemde de grenzen van
  de twee condities en verwees naar A1, A2 en A3.
- De gewone chat stelde in zijn eerste antwoord een *breder*
  onderzoeksplan voor dan de uiteindelijk uitgevoerde proef. Hij voerde
  die acties zelf niet uit; hij kreeg de proefresultaten vervolgens
  aangeboden.

Bewijs: [gelijke-bewijsvergelijking](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/42295728049)
en het artifact `ngbse-vs-chat-full-evidence-20261106`.

## Waar NGBSE iets toevoegde

Een afzonderlijke, gecontroleerde onderzoeksuitvoerder **heeft
daadwerkelijk** twee Python-tests en een bronopvraag uitgevoerd. Hij
bewaar­de de exacte uitvoer, versiecontext, referenties en een
gestructureerde vergelijking vóór en na nieuw bewijs.

Dat is nuttige technische infrastructuur. Het is **niet** aangetoond
dat BALLMS 50 als redeneersysteem slimmer was dan de gewone chat.

De acties waren namelijk vooraf voor deze ene casus geprogrammeerd.
BALLMS 50 besloot niet zelfstandig *welke* actie moest worden uitgevoerd.
De externe `reconcile()`-functie trekt de beslissende conclusie, niet
de bestaande BALLMS 50-engine.

## Waar NGBSE onvoldoende was

De tweede BALLMS 50-analyse houdt nog twee hiaten open:
`missing_evidence` en `open_question`. De aparte uitvoerder kan een
absolute claim weerleggen, maar BALLMS 50 zelf markeert het betreffende
hiaat nog niet als beantwoord en kent geen gecontroleerde
claimherzieningscyclus. Het is onjuist om dit te presenteren als een
zelfstandig werkende, zelfcorrigerende onderzoeker.

Ook toetst deze proef slechts één technische bewering, in één
Python-installatie met twee importcondities. Er is geen onafhankelijke
blinde beoordeling van meerdere casussen en geen bewijs dat NGBSE
structureel beter onderzoekt dan een gewoon model met dezelfde tools.

## Besluitadvies

**Geen brede verdere ontwikkeling van BALLMS 50 als zelfstandige
intelligente onderzoeksagent op basis van dit resultaat.**

De interessante onderdelen zitten voorlopig in een kleinere set
controleerbare functies: een open vraag bewaren, een precies begrensde
onderzoeksactie uitvoeren, het bewijs registreren, een conclusie
herzien en aangeven wat nog onbekend is. De reeds gebouwde adapter
laat zien dat die uitvoering mogelijk is.

Voor nieuwe investering geldt één beslisregel: laat op meerdere echte,
vooraf vastgelegde dossiers zien dat deze werkwijze beter bewijs vindt
of aantoonbaar minder ongefundeerde conclusies trekt dan een gewone
AI-chat met dezelfde tools en hetzelfde budget. Zonder dat verschil
heeft de extra software onvoldoende onderbouwde meerwaarde.

Geen merge, geen productie-uitrol en geen verwerking van echte
leerling- of persoonsgegevens.
