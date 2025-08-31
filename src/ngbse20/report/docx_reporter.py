from datetime import datetime
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
) -> None:
    if not _DOCX_AVAILABLE:
        LOGGER.warning("python-docx not installed, skipping .docx report generation.")
        return

    doc = Document()
    doc.add_heading("NGBSE 20.1 - Intelligence Brief", 0)
    doc.add_paragraph(f"Generated: {datetime.utcnow().isoformat()}Z")

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

    doc.add_heading("Analyst Review & Sign-off", 1)
    doc.add_paragraph("\nAnalyst Name: ________________________\nDate of Review: ______________________\nConclusion: [Agree] [Disagree]\nSignature: ___________________________")

    doc.save(path)
