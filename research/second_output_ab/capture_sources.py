"""Freeze publicly accessible full-text paper evidence for a matched research test.

All arms see exactly the same published, visible paper excerpts. We do not
inspect hidden reasoning, claim the articles omitted unreported steps, or
substitute abstracts silently for unavailable full text.
"""
from __future__ import annotations

import hashlib
import json
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

PAPERS = {
    "B": {"pmcid": "PMC12232635", "doi": "10.1073/pnas.2422633122",
          "title": "Generative AI without guardrails can harm learning"},
    "K": {"pmcid": "PMC12179260", "doi": "10.1038/s41598-025-97652-6",
          "title": "AI tutoring outperforms in-class active learning"},
}
MAX_HTTP_BYTES = 4_000_000
MAX_SELECTED_CHARS = 62_000


def flatten(node):
    return re.sub(r"\s+", " ", " ".join(node.itertext())).strip()


def source_bundle(paper_id, *, fetch=None):
    if paper_id not in PAPERS:
        raise ValueError("unknown paper")
    data = PAPERS[paper_id]
    url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/{data['pmcid']}/fullTextXML"
    if fetch is None:
        def fetch(u):
            with urlopen(Request(u, headers={"User-Agent": "NGBSE-paired-research/0.1"}),
                         timeout=30) as response:
                if response.geturl() != u or response.status != 200:
                    raise ValueError("unexpected redirect or HTTP status")
                raw = response.read(MAX_HTTP_BYTES + 1)
                if len(raw) > MAX_HTTP_BYTES:
                    raise ValueError("response too large")
                return raw
    raw = fetch(url)
    if not isinstance(raw, bytes) or len(raw) > MAX_HTTP_BYTES:
        raise ValueError("invalid full text bytes")
    root = ET.fromstring(raw)
    body = root.find(".//body")
    abstract = root.find(".//abstract")
    if body is None or abstract is None:
        raise ValueError("both full body and abstract are required")
    parents = {child: parent for parent in root.iter() for child in parent}
    def location(node):
        names = []
        while node in parents:
            node = parents[node]
            if node.tag == "sec":
                head = node.find("./title")
                if head is not None:
                    names.append(flatten(head)[:80])
        return " > ".join(reversed(names)) or "Body"

    rows = []
    for i, p in enumerate(abstract.iter("p"), start=1):
        txt = flatten(p)
        if len(txt) > 40:
            rows.append({"id":f"{paper_id}-A{i:03d}","section":"Abstract","text":txt[:2000]})
    if not rows:
        txt=flatten(abstract)
        rows.append({"id":f"{paper_id}-A001","section":"Abstract","text":txt[:3500]})
    group = defaultdict(list)
    for i, p in enumerate(body.iter("p"), start=1):
        txt=flatten(p)
        if len(txt) < 35:
            continue
        sec=location(p)
        s=sec.casefold()
        kind=("results" if "result" in s or "finding" in s else
              "methods" if any(y in s for y in ("method", "design", "study", "setting", "intervention", "experiment")) else
              "discussion" if any(y in s for y in ("discuss", "limitation", "conclusion", "future")) else
              "other")
        group[kind].append({"id":f"{paper_id}-P{i:03d}","section":sec,"text":txt[:2100]})
    if sum(map(len, group.values())) < 12:
        raise ValueError("full text parsing yielded too few body paragraphs")
    budget=MAX_SELECTED_CHARS - sum(len(r["text"]) for r in rows)
    kinds=("methods","results","discussion","other")
    # Deterministic stratification, not cherry-picking findings after reading results.
    indices={kind:0 for kind in kinds}
    while budget > 200:
        progress=False
        for kind in kinds:
            if indices[kind] < len(group[kind]):
                row=group[kind][indices[kind]]
                indices[kind]+=1
                if len(row["text"]) <= budget:
                    rows.append(row);budget-=len(row["text"]);progress=True
        if not progress:
            break
    if len(rows) < 16:
        raise ValueError("source packet too sparse for meaningful research")
    return {
        "id":paper_id, "pmcid":data["pmcid"],"doi":data["doi"],
        "source_url":url,"publisher_title":data["title"],
        "xml_sha256":hashlib.sha256(raw).hexdigest(),
        "extraction_method":"abstract and deterministic balanced full-body paragraph sample",
        "body_paragraphs_extracted":sum(map(len,group.values())),
        "selected_paragraphs":len(rows),
        "source_character_budget":MAX_SELECTED_CHARS,
        "paragraphs":rows,
        "warning":"Visible published text only; raw data and hidden process not inspected",
    }


def main():
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    papers={x:source_bundle(x) for x in PAPERS}
    manifest={
        "created_utc":datetime.now(timezone.utc).isoformat(),
        "papers":papers,
        "cases":[
            {"id":"B-OPEN","paper":"B","type":"open",
             "task":"Beoordeel de zichtbare bewijskracht en vind zelfstandige nieuwe onderzoeksmogelijkheden. Behoud zowel positieve resultaten als niet-afgedekte claims."},
            {"id":"K-OPEN","paper":"K","type":"open",
             "task":"Beoordeel de zichtbare bewijskracht en vind zelfstandige nieuwe onderzoeksmogelijkheden. Behoud zowel positieve resultaten als niet-afgedekte claims."},
            {"id":"K-CONTROL","paper":"K","type":"negative_control",
             "task":"Toets uitsluitend de beperkte claim: dit onderzoek rapporteert hogere directe post-test scores bij de AI-tutorconditie dan bij klassikale actieve leervormen, binnen de onderzochte lessen. Zoek geen gebrek in een claim over langdurig leren die niet is gedaan."},
        ],
        "experiment_rule":"Identical public source paragraphs in both arms; no Proef 01 leads supplied",
    }
    (args.out/"sources.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({
        "status":"SOURCE_CAPTURED",
        "cases":len(manifest["cases"]),
        "papers":{p:{"paragraphs":x["selected_paragraphs"],
                      "xml_sha256":x["xml_sha256"]}
                  for p,x in papers.items()}
    },ensure_ascii=False),flush=True)


if __name__=="__main__":
    main()
