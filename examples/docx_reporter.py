from datetime import datetime, timezone
from typing import Any

from ..logging import get_logger

LOGGER = get_logger(__name__)

try:
    from docx import Document
    from docx.shared import Pt
    _DOCX_AVAILABLE = True
except ImportError:
    _DOCX_AVAILABLE = False
    Document, Pt = None, None

def write_report(
    path: str,
    brief: dict[str, Any],
    blindspots: dict[str, Any],
    forecast: dict[str, Any],
    scenarios: dict[str, Any] | None = None,
    ballm_meta_layer: dict[str, Any] | None = None,
    stix_summary: dict[str, Any] | None = None,
    next_seeds: list[dict[str, Any]] | None = None,
) -> None:
    if not _DOCX_AVAILABLE:
        LOGGER.warning("python-docx not installed, skipping .docx report generation.")
        return

    doc = Document()
    doc.add_heading("NGBSE 20.2.0-GA - Intelligence Brief", 0)
    doc.add_paragraph(f"Generated: {datetime.now(timezone.utc).isoformat()}")

    doc.add_heading("BLUF (Bottom Line Up Front)", 1)
    doc.add_paragraph(brief.get("BLUF", "No summary available."))

    doc.add_heading("Top Risks", 1)
    for r in brief.get("TopRisks", []):
        doc.add_paragraph(f"- {r.get('asset')}: risk {r.get('risk')}", style='List Bullet')

    doc.add_heading("Recommended Actions", 1)
    for a in brief.get("Actions", []):
        doc.add_paragraph(f"- {a}", style='List Bullet')

    doc.add_heading("Blindspot Analysis", 1)
    doc.add_paragraph(f"Coverage Ratios: {blindspots.get('coverage', {}).get('ratios', {})}")
    doc.add_paragraph(f"Recency Spike: {blindspots.get('recency', {}).get('spike', False)}")
    doc.add_paragraph(f"Confidence Gap (risky assets): {blindspots.get('confidence', {}).get('risky_assets', [])}")

    # Epistemic Dashboard (BALLM)
    if ballm_meta_layer:
        doc.add_heading("Epistemic Dashboard", 1)
        ehs = float(ballm_meta_layer.get("epistemic_humility_score", 0.0) or 0.0)
        if ehs >= 0.8:
            status = "🟢 High Confidence"
        elif ehs >= 0.6:
            status = "🟡 Moderate Confidence"
        else:
            status = "🔴 Low Confidence"
        table = doc.add_table(rows=3, cols=2)
        table.style = 'Table Grid'
        table.cell(0, 0).text = "Metric"
        table.cell(0, 1).text = "Value"
        table.cell(1, 0).text = "Epistemic Humility Score"
        table.cell(1, 1).text = f"{ehs:.2f} - {status}"
        ep_conf = float(ballm_meta_layer.get("epistemic_confidence", 0.0) or 0.0)
        table.cell(2, 0).text = "Analysis Confidence"
        table.cell(2, 1).text = f"{ep_conf:.2f}"

        # Key Curiosity Questions
        questions = ballm_meta_layer.get("curiosity_questions", []) or []
        if questions:
            doc.add_heading("Key Curiosity Questions", 1)
            # Prefer high curiosity first
            priority_map = {"high": 3, "medium": 2, "low": 1}
            sorted_q = sorted(
                questions,
                key=lambda q: priority_map.get(str(q.get("curiosity_level", "")).lower(), 0),
                reverse=True,
            )[:3]
            for idx, q in enumerate(sorted_q, start=1):
                doc.add_paragraph(
                    f"{idx}. {q.get('question', 'N/A')} (level: {q.get('curiosity_level', 'n/a')})",
                    style='List Number'
                )

        # Blindspot LLM interpretation (if available)
        interp = ballm_meta_layer.get("blindspot_interpretation")
        if interp:
            doc.add_heading("LLM Interpretation of Blindspots", 2)
            doc.add_paragraph(str(interp))

    doc.add_heading("Forecast & Scenarios", 1)
    if forecast:
        for asset, fvals in forecast.items():
            doc.add_paragraph(f"- {asset}: last={round(fvals.get('last_score',0),3)} → projected_next={round(fvals.get('projected_next',0),3)}", style='List Bullet')
    else:
        doc.add_paragraph("No historical series available yet.")

    if scenarios:
        doc.add_heading("Scenarios (90-day Horizon)", 2)
        for theme, data in scenarios.items():
            prob = round(100 * data.get("probability_90_days", 0.0), 1)
            summary = (data.get("semantic_summary") or "No LLM summary.").strip()
            doc.add_paragraph(f"{theme.replace('_', ' ')} (p≈{prob}%): {summary}")

    # Operational Intelligence Summary (STIX)
    if stix_summary:
        doc.add_heading("Operational Intelligence Summary", 1)
        totals = stix_summary.get("summary_stats", {})
        if totals:
            doc.add_paragraph(
                f"Indicators: {totals.get('indicators', 0)}, "
                f"Threat Actors: {totals.get('threat_actors', 0)}, "
                f"Vulnerabilities: {totals.get('vulnerabilities', 0)}"
            )
        top_inds = stix_summary.get("top_indicators", [])
        if top_inds:
            doc.add_heading("Top Indicators", 2)
            for it in top_inds[:5]:
                t = it.get('type', 'indicator')
                v = it.get('value') or it.get('pattern', 'n/a')
                doc.add_paragraph(f"- {t}: {v}", style='List Bullet')
        actors = stix_summary.get("threat_actors", [])
        if actors:
            doc.add_heading("Threat Actors", 2)
            for a in actors[:3]:
                doc.add_paragraph(f"- {a}", style='List Bullet')
        vulns = stix_summary.get("vulnerabilities", [])
        if vulns:
            doc.add_heading("Vulnerabilities", 2)
            for v in vulns[:5]:
                if isinstance(v, dict):
                    doc.add_paragraph(f"- {v.get('name', 'unknown')} ({v.get('severity','n/a')})", style='List Bullet')
                else:
                    doc.add_paragraph(f"- {v}", style='List Bullet')

    # Next Steps (Proposed Seeds)
    if next_seeds:
        doc.add_heading("Recommended Next Steps", 1)
        # Prioritize by 'priority' descending if present
        def _prio(s: Any) -> float:
            try:
                return float(s.get('priority', 0) or 0)
            except Exception:
                return 0.0
        for s in sorted(next_seeds, key=_prio, reverse=True)[:5]:
            label = s.get('type', 'seed')
            value = s.get('value') or s.get('query') or s.get('id', 'n/a')
            pr = s.get('priority', 'n/a')
            rationale = s.get('rationale', '')
            doc.add_paragraph(f"- {label}: {value} (priority: {pr})", style='List Bullet')
            if rationale:
                doc.add_paragraph(f"  rationale: {rationale}")

    doc.add_heading("Analyst Review & Sign-off", 1)
    doc.add_paragraph("\nAnalyst Name: ________________________\nDate of Review: ______________________\nConclusion: [Agree] [Disagree]\nSignature: ___________________________")

    doc.save(path)
