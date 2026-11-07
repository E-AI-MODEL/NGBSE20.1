# NGBSE Proef 02: is de tweede opbrengst werkelijk extra?

**Status:** exploratieve A/B-proef, niet gemerged of gepubliceerd. Geen conclusies vóór inzage van beide echte uitvoerarmen.

## Vraag

Kan een onderzoeksaanpak vanuit **gap as a feature** méér brongebonden, toetsbare en zelfstandige onderzoeksmogelijkheden vinden dan een even grondige gewone peer-reviewopdracht, bij dezelfde modelversie en bronnen?

Niet: kan NGBSE meer vragen laten genereren? Niet: levert een vragenlijst automatisch nieuwe kennis?

## Input en gelijkheid

- Studie B: Bastani e.a., *Generative AI without guardrails can harm learning*, DOI 10.1073/pnas.2422633122.
- Studie K: Kestin e.a., *AI tutoring outperforms in-class active learning*, DOI 10.1038/s41598-025-97652-6.
- Negatieve controle K: alleen de afgebakende directe natoetsscorevergelijking, die positief wordt ondersteund. Het ontbreken van retentiemetingen mag die **beperkte** claim niet kunstmatig ontkrachten.
- Beide armen krijgen dezelfde bronpassages binnen een case, dezelfde taak, twee rondes en een gelijke outputlimiet en modelversie (`gpt-4.1`).
- Arm O: sterke kritische reviewer die breed mogelijke alternatieven, gaten en onderzoekspaden zoekt.
- Arm N: NGBSE, met de expliciete opdracht niet-gebruikte mogelijkheden als zelfstandige opbrengst te bewaren, de draagkracht van conclusies te onderzoeken en vondsten recursief te verdiepen.
- Iedere case/arm loopt in een eigen modelconversatie, zonder voorafgaande resultaten van Proef 01.
- De uitvoervolgorde is vooraf met seed 20261107 gehusseld; er zijn maximaal 12 echte modelaanroepen, nooit automatische retries.
- Een aangeroepen LLM is niet het product NGBSE; deze proef vergelijkt de **werkwijze als onderzoeksinstructie** met een andere onderzoeksinstructie.

## Eerlijke bronafbakening

De eerste opzet probeerde XML-volle teksten via Europe PMC te ophalen. Een test vanuit GitHub Actions gaf een time-out. Als de liveproef het XML alsnog ophaalt, legt de parser de originele XML-hash en maximaal 62.000 tekens per publicatie als per-sectie gespreid bronpakket vast. Dat is **geen** onverkorte volledige paper in het modelcontextvenster.

Er is een tweede opzet beschikbaar met 42 handmatig vastgelegde, herleidbare maar geparafraseerde bronkaarten. Deze tweede opzet is apart en mag niet als een identieke herhaling van de eerste worden behandeld. Er zijn geen ruwe leerlingdata, verborgen modelredeneringen of aanvullende bijlagen ingelezen.

## Beoordeling vooraf

Elke kandidaat wordt afzonderlijk bekeken. Geen enkele totaalscore die meer output vanzelf beloont.

| Vraag | Wat telt positief? | Wat telt negatief? |
| --- | --- | --- |
| Nieuw naast het gegeven eindresultaat? | Werkelijk andere toets, relevant alternatief of nieuw zelfstandig onderzoekspad | Al letterlijk door de bron of eerdere kandidaat beschreven, oppervlakkige parafrase |
| Steunt de bron deze observatie? | Specifieke, passende passage en duidelijke claimgrens | Verkeerde vindplaats, speculatie als vaststelling, verzonnen ontbrekende methodiek |
| Kan de vondst zelfstandig onderzocht worden? | Een toets die verklaringen van elkaar onderscheidt | Algemene oproep tot 'meer onderzoek' |
| Verandert de vondst mogelijk een besluit? | Nieuwe keuze voor meting, onderzoeksopzet of theoretische verklaring | Irrelevant bezwaar voor de onderzochte claim |
| Verwerkt de route tegenbewijs? | Neemt aantrekkelijke maar onhoudbare gevolgtrekkingen gemotiveerd terug | Vult de prullenbak met schijnfouten |
| Houdt de route bewezen positieve effecten overeind? | Begrensde positieve conclusie intact | Onterecht volledig wegschrijven van een gerandomiseerd effect |

De negatieve controle is een expliciete rem op overdreven gapproductie. Beide armen mogen daar terecht besluiten dat er voor **de beperkte onderzoeksvraag** geen wezenlijk gat is.

## Wat telt als een echte voorsprong?

Een overtuigende NGBSE-voorsprong vraagt herhaaldelijk meer **unieke, brongebonden, beslisrelevante en onderscheidend toetsbare** vondsten, zonder een toename van onhoudbare fouten. Een route die vooral meer tekst of indrukwekkender labels maakt, wint niet.

Een geval of twee kan geen algemene effectclaim dragen. Laat de bestaande proeven uit Proef 01 buiten de beoordeling. Een eigen interne beoordeling is niet onafhankelijk of blind; die moet ook zo worden genoemd.

## Statusscheiding

Uitgevoerde modelaanroepen, complete antwoorden, beoordeelde vondsten en bewezen nieuwe kennis blijven afzonderlijke statussen. Een groene workflow bewijst alleen dat de code en de aanroepen werkten.

**Verander of merge geen productcode naar aanleiding van deze proef.**
