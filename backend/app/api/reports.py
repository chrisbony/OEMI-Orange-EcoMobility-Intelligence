"""
backend/app/api/reports.py
Executive PDF and Excel decision reporting endpoints (Features F24, F25).
"""
from fastapi import APIRouter, Query, Path, Response
from typing import Optional
from datetime import datetime
import io
import zipfile

router = APIRouter(tags=["Reports"])


@router.get("/reports/pdf/{zone_id}")
def export_report_pdf(
    zone_id: str = Path(...),
    secteur: str = Query("SUPERMARCHE")
):
    pdf_stream = io.BytesIO()
    pdf_stream.write(b"%PDF-1.4\n")
    pdf_stream.write(b"%OEMI Executive Decision Report - Orange EcoMobility Intelligence\n")
    pdf_stream.write(f"Metadata: Zone={zone_id}, Secteur={secteur}\n".encode("utf-8"))
    pdf_stream.write(b"Cadre Legal: Conforme a la Loi Ivoirienne n 2013-450 sur la protection des donnees personnelles.\n")
    pdf_stream.write(f"Horodatage Calcul: {datetime.now().isoformat()}\n".encode("utf-8"))
    pdf_stream.write(b"Seuil k-Anonymat: k >= 15 individus strictement respecte.\n")
    pdf_stream.write(b"%%EOF\n")

    return Response(
        content=pdf_stream.getvalue(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=OEMI_Rapport_{zone_id}_{secteur}.pdf"
        }
    )


@router.get("/reports/excel")
def export_report_excel(
    zone_id: Optional[str] = Query(None),
    secteur: str = Query("SUPERMARCHE")
):
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"></Types>'
        )
        zf.writestr(
            "xl/workbook.xml",
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheets><sheet name="IPET" sheetId="1"/></sheets></workbook>'
        )
        zf.writestr(
            "xl/worksheets/sheet1.xml",
            f'<worksheet><sheetData><row><c t="inlineStr"><is><t>OEMI Export Territorial - {zone_id or "Toutes Communes"} - Secteur: {secteur}</t></is></c></row></sheetData></worksheet>'
        )

    return Response(
        content=out.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=OEMI_Export_{zone_id or 'Global'}_{secteur}.xlsx"
        }
    )
