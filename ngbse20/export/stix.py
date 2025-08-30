from typing import List, Dict, Any
from datetime import datetime, timezone
import uuid

def _ts(ts):
    if isinstance(ts, str):
        try:
            return datetime.fromisoformat(ts.replace('Z','+00:00')).isoformat()
        except Exception:
            return datetime.now(timezone.utc).isoformat()
    if isinstance(ts, datetime):
        return ts.isoformat()
    return datetime.now(timezone.utc).isoformat()

def _id(ns: str) -> str:
    return f"{ns}--{uuid.uuid4()}"

def to_stix(findings: List[Dict[str,Any]], traces: List[Dict[str,Any]]|None=None) -> Dict[str,Any]:
    traces = traces or []
    creator = {
        "type":"identity","spec_version":"2.1","id":_id("identity"),
        "name":"NGBSE 20.1","identity_class":"organization"
    }
    bundle = {"type":"bundle","spec_version":"2.1","id":_id("bundle"),"objects":[creator]}
    report = {
        "type":"report","spec_version":"2.1","id":_id("report"),
        "name":"NGBSE 20.1 Findings","published":datetime.now(timezone.utc).isoformat(),
        "created_by_ref":creator["id"],"object_refs":[]
    }
    bundle["objects"].append(report)

    for f in findings:
        url = f.get("url") or f.get("source",{}).get("url")
        ts = _ts(f.get("timestamp"))
        score = f.get("score", 0)
        od_id, sco_url = None, None
        if url:
            sco_url = {"type":"url","value":url,"id":_id("url")}
            bundle["objects"].append(sco_url)
            od = {
                "type":"observed-data","spec_version":"2.1","id":_id("observed-data"),
                "created":ts,"modified":ts,"created_by_ref":creator["id"],
                "first_observed":ts,"last_observed":ts,"number_observed":1,
                "object_refs":[sco_url["id"]]
            }
            od_id = od["id"]
            bundle["objects"].append(od)

        ind = {
            "type":"indicator","spec_version":"2.1","id":_id("indicator"),
            "created":ts,"modified":ts,"created_by_ref":creator["id"],
            "name": f.get("title","NGBSE finding"),
            "pattern_type":"stix",
            "pattern": f"[url:value = '{url}']" if url else "[artifact:mime_type = 'text/plain']",
            "valid_from": ts,
            "x_ngbse_meta": {
                "score": score,
                "score_breakdown": f.get("score_breakdown",{}),
                "seed_id": f.get("seed_id"),
                "hash": f.get("hash"),
                "trace_refs": [t.get("id") for t in traces]
            }
        }
        bundle["objects"].append(ind)
        report["object_refs"].append(ind["id"])
        if od_id:
            rel = {
                "type":"relationship","spec_version":"2.1","id":_id("relationship"),
                "relationship_type":"based-on",
                "source_ref":ind["id"],"target_ref":od_id,
                "created_by_ref":creator["id"]
            }
            bundle["objects"].append(rel)
            report["object_refs"].append(od_id)
            report["object_refs"].append(rel["id"])

        note = {
            "type":"note","spec_version":"2.1","id":_id("note"),
            "created":ts,"modified":ts,"created_by_ref":creator["id"],
            "abstract":"NGBSE meta-layer",
            "content": (f.get("meta",{}).get("blindspots") or f.get("summary","")),
            "object_refs":[ind["id"]],
            "x_ngbse_meta": {
                "provenance": f.get("provenance",{}),
                "rules_fired": f.get("meta",{}).get("rules_fired",[]),
                "trace_refs": [t.get("id") for t in traces]
            }
        }
        bundle["objects"].append(note)
        report["object_refs"].append(note["id"])

    return bundle
