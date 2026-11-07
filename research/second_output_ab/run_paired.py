"""Matched two-arm research-only pilot. No NGBSE product code is changed.

Six independent conversations: 3 cases x 2 arms; each takes two model turns.
Source snapshots, prior turns, model settings, calls and failures are retained.
The 'NGBSE' arm is a *research instruction*, not the historical NGBSE engine.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import random
from typing import Any

MODEL="gpt-4.1"
MAX_OUTPUT=3400
MAX_CALLS=12
MAX_RESERVED_USD=2.60
# Deliberately conservative budget reservations; not billed costs.
INPUT_PER_M=3.0
OUTPUT_PER_M=12.0
BASE=(
    "Je onderzoekt gepubliceerde wetenschappelijke teksten met zorg voor "
    "positieve én negatieve bevindingen. De input bestaat uit dezelfde "
    "genummerde, uit de volledige paper geëxtraheerde bronpassages. "
    "Verwijs naar bron-ID's, onderscheid observatie van hypothese, "
    "en zeg nooit dat auteurs een stap níét deden wanneer die slechts "
    "niet zichtbaar is in de aangeleverde tekst. "
    "Een bronpassage bewijst niet vanzelf de interpretatie. "
    "Maak geen verborgen AI-denkproces of ruwe onderzoeksdata op basis van "
    "een paper. Meer vragen betekent niet meer waarde. "
    "Spreek natuurlijk Nederlands. Gebruik tot 3400 outputtokens per beurt."
)
ARM={
 "ordinary":(
    "Je bent een uitstekende onafhankelijke peer reviewer die breed en diep "
    "onderzoekt. Zoek onopgemerkte methodische vragen, tegenvoorbeelden, "
    "verborgen aannames, ontbrekende vergelijkingen, niet-dragende conclusies "
    "en waardevolle nieuwe hypothesen. Wees creatief maar streng. "
    "Werk met meerdere verklaringen en maak gedurfde ideeën expliciet toetsbaar. "
    "Vermijd generieke bezwaren en erken waar het bewijs een uitspraak wél draagt."
 ),
 "ngbse":(
    "Je werkt vanuit de NGBSE-hypothese: het antwoord is de eerste opbrengst, "
    "alle tijdens zichtbaar kenniswerk blootgelegde hiaten, twijfels, "
    "onaangeboorde verklaringen, ongebruikte alternatieven en niet-dragende "
    "conclusies kunnen een tweede zelfstandige opbrengst vormen. "
    "Zoek maximaal breed en diep, laat vondsten nieuwe onderzoeksrichtingen "
    "openen en bewaar ook verworpen hypotheses mét reden. "
    "Onderzoek expliciet welke processtappen een conclusie kunnen dragen, "
    "en welke stap zou ontbreken om een sterkere claim te rechtvaardigen. "
    "Noem nooit een mogelijk gat een bewezen fout, en behoud geldige positieve resultaten."
 )
}
FORMAT=(
    "Schrijf eerst de sterkste verdedigbare, beknopte uitkomst van het artikel "
    "voor deze onderzoeksvraag. Daarna bevindingen met labels [F1], [F2] enz. "
    "Vermeld per bevinding: vaststelling of mogelijkheid; precieze bron-ID's; "
    "wat werkelijk ontbreekt of schuurt; waarom het wetenschappelijk interessant "
    "kan zijn; en een onderscheidende mogelijke toets. "
    "Gebruik alleen relevante bevindingen, geen verplicht aantal. "
    "Sluit af met minimaal één expliciet onderbouwde uitspraak die de bron "
    "wel kan dragen, en één mogelijke interpretatie die je verwerpt als ongegrond."
)
ROUND_TWO=(
    "Verken nu een tweede, onafhankelijke zoekronde op DEZELFDE BRONNEN, "
    "zonder externe websites te raadplegen. Doorzoek je eerdere bevindingen: "
    "welke ontbreken, welke blijken dubbel, welke heeft het artikel zelf al "
    "ondervangen, welke zijn niet echt brongebonden? "
    "Werk minstens twee mogelijke nieuwe zijroutes uit, maar verzin geen nieuwe "
    "feiten. Trek één aantrekkelijke ongefundeerde kritiek expliciet in. "
    "Geef na afloop een compacte beschouwing van de draagkracht van de onderzochte "
    "conclusies. Een goed onderbouwde smalle claim mag volledig overeind blijven. "
    "Gebruik weer de beschikbare bron-ID's. Vermeld wat niet is gemeten."
)


def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True).encode()).hexdigest()


def reserve(messages):
    chars=sum(len(m["content"]) for m in messages)
    if chars>250_000:
        raise ValueError("Source and conversation exceed allowed input size")
    return 1.2*((chars/2.0)*INPUT_PER_M+MAX_OUTPUT*OUTPUT_PER_M)/1_000_000


def unpack_facts(entry, paper):
    # This is the SAME source string for each arm; no prior Proef01 findings.
    return json.dumps({
        "case_id":entry["id"],
        "task":entry["task"],
        "visible_evidence":paper["paragraphs"],
        "source_doi":paper["doi"],
        "source_url":paper["source_url"],
        "extraction":paper["extraction_method"],
        "note":"Only visible publication text. No independent raw dataset or hidden author process.",
    },ensure_ascii=False)


def run(sources_path, out):
    if out.exists():
        raise RuntimeError("NO_REPLAY: output folder already exists; do not reissue possibly paid calls")
    raw=sources_path.read_text(encoding="utf-8")
    sources=json.loads(raw)
    if len(sources["cases"])!=3 or set(sources["papers"])!={"B","K"}:
        raise ValueError("Unexpected frozen source set")
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("NO_MODEL_KEY: zero calls sent")
    from openai import OpenAI
    client=OpenAI(timeout=110,max_retries=0)
    out.mkdir(parents=True)
    records=out/"model_receipts.jsonl"
    combos=[(c,a) for c in sources["cases"] for a in ARM]
    random.Random(20261107).shuffle(combos)
    budget=0.0
    used=0
    complete=0
    result=[]
    for entry,arm in combos:
        paper=sources["papers"][entry["paper"]]
        system=BASE+"\n\n"+ARM[arm]
        first=(
            "Onderzoek de onderstaande bronpassages kritisch en uitvoerig.\n"+
            unpack_facts(entry,paper)+"\n\n"+FORMAT
        )
        messages=[{"role":"developer","content":system},{"role":"user","content":first}]
        answers=[]
        receipts=[]
        failure=None
        for step in (1,2):
            if step==2:
                messages.append({"role":"assistant","content":answers[0]})
                messages.append({"role":"user","content":ROUND_TWO})
            need=reserve(messages)
            if used>=MAX_CALLS or budget+need>MAX_RESERVED_USD:
                failure="BUDGET_LIMIT"
                break
            budget+=need
            used+=1
            meta={
                "case":entry["id"],"arm":arm,"round":step,
                "requested_model":MODEL, "max_output_tokens":MAX_OUTPUT,
                "source_xml_sha256":paper["xml_sha256"],
                "source_packet_sha256":digest(paper["paragraphs"]),
                "prompt_sha256":digest(messages),
                "messages":messages,
            }
            with records.open("a",encoding="utf-8") as f:
                f.write(json.dumps({"kind":"request_start",**meta},ensure_ascii=False)+"\n")
            try:
                response=client.responses.create(
                    model=MODEL,input=messages,max_output_tokens=MAX_OUTPUT,
                    temperature=0.35,store=False,
                )
                text=response.output_text or ""
                receipt={"kind":"response",**meta,"model_returned":response.model,
                         "response_id":response.id,"status":response.status,
                         "usage":response.usage.model_dump() if response.usage else {},
                         "answer":text}
                with records.open("a",encoding="utf-8") as f:
                    f.write(json.dumps(receipt,ensure_ascii=False)+"\n")
                if response.status!="completed" or not text.strip():
                    failure="INCOMPLETE_MODEL_RESPONSE"
                    break
                answers.append(text)
                receipts.append({"round":step,"status":"completed","response_id":response.id,
                                 "model":response.model,"usage":receipt["usage"]})
                print("COMPLETED",entry["id"],arm,"round",step,
                      "chars",len(text),flush=True)
            except Exception as exc:
                failure=type(exc).__name__
                with records.open("a",encoding="utf-8") as f:
                    f.write(json.dumps({"kind":"request_error",**meta,
                                        "error_type":type(exc).__name__,
                                        "no_retry":True},ensure_ascii=False)+"\n")
                break
        result.append({"case":entry["id"],"arm":arm,"status":failure or "completed",
                       "rounds":answers,"receipts":receipts})
        if not failure:
            complete+=1
        else:
            print("STOP",entry["id"],arm,failure,flush=True)
            break
    (out/"paired_outputs.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    summary={
        "source_snapshot_sha256":hashlib.sha256(raw.encode()).hexdigest(),
        "cases":3,"arms":2,"calls_planned":MAX_CALLS,
        "calls_attempted":used,"completed_pairs":complete,
        "reserved_cost_usd":round(budget,6),"max_reserved_usd":MAX_RESERVED_USD,
        "study_type":"exploratory paired pilot; no blind human adjudication",
        "stronger_claim_not_established":"NGBSE method better than ordinary deep review",
        "all_arms_same_source":True,
        "same_model_and_output_token_cap":True,
        "hidden_reasoning_observed":False,
    }
    (out/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n")
    print("FINAL_SUMMARY",json.dumps(summary,ensure_ascii=False),flush=True)
    if complete!=6:
        raise RuntimeError("Partial paired run; no winner may be announced")


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--sources",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    run(args.sources,args.out)
