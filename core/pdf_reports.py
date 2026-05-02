from __future__ import annotations

from decimal import Decimal
from io import BytesIO
from typing import Iterable, Sequence
from xml.sax.saxutils import escape

from django.http import FileResponse
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def format_currency(value) -> str:
    if value in (None, ''):
        return '-'
    amount = value if isinstance(value, Decimal) else Decimal(str(value))
    return f'R$ {amount:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def format_value(value) -> str:
    if value in (None, ''):
        return '-'
    if hasattr(value, 'strftime'):
        return value.strftime('%d/%m/%Y')
    return str(value)


def paragraph(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(str(text)).replace('\n', '<br/>'), style)


def build_key_value_table(rows: Sequence[tuple[str, str]]) -> Table:
    data = [[paragraph(label, _styles()['label']), paragraph(value, _styles()['value'])] for label, value in rows]
    table = Table(data, colWidths=[55 * mm, 120 * mm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.whitesmoke),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#d9dee3')),
        ('INNERGRID', (0, 0), (-1, -1), 0.35, colors.HexColor('#d9dee3')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    return table


def build_data_table(headers: Sequence[str], rows: Iterable[Sequence[str]], col_widths: Sequence[int | float] | None = None) -> Table:
    data = [[paragraph(header, _styles()['table_header']) for header in headers]]
    for row in rows:
        data.append([paragraph(cell, _styles()['table_cell']) for cell in row])
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#eceff3')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1f2937')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#d9dee3')),
        ('INNERGRID', (0, 0), (-1, -1), 0.35, colors.HexColor('#d9dee3')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    return table


def build_pdf_response(filename: str, title: str, story: list) -> FileResponse:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=title,
        author='Mãos na Obra',
    )
    doc.build(story, onFirstPage=lambda canvas, document: _draw_page_header(canvas, document, title), onLaterPages=lambda canvas, document: _draw_page_header(canvas, document, title))
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=filename)


def heading(text: str):
    return paragraph(text, _styles()['heading'])


def subheading(text: str):
    return paragraph(text, _styles()['subheading'])


def body(text: str):
    return paragraph(text, _styles()['body'])


def spacer(height: int = 4):
    return Spacer(1, height)


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='ReportHeading',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#111827'),
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name='ReportSubheading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#374151'),
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name='ReportBody',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=9.2,
        leading=12,
        textColor=colors.HexColor('#1f2937'),
    ))
    styles.add(ParagraphStyle(
        name='ReportLabel',
        parent=styles['BodyText'],
        fontName='Helvetica-Bold',
        fontSize=8.8,
        leading=11,
        textColor=colors.HexColor('#374151'),
    ))
    styles.add(ParagraphStyle(
        name='ReportValue',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=8.8,
        leading=11,
        textColor=colors.HexColor('#111827'),
    ))
    styles.add(ParagraphStyle(
        name='ReportTableHeader',
        parent=styles['BodyText'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=10,
        alignment=TA_LEFT,
        textColor=colors.HexColor('#111827'),
    ))
    styles.add(ParagraphStyle(
        name='ReportTableCell',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=8.2,
        leading=10,
        textColor=colors.HexColor('#111827'),
    ))
    return {
        'heading': styles['ReportHeading'],
        'subheading': styles['ReportSubheading'],
        'body': styles['ReportBody'],
        'label': styles['ReportLabel'],
        'value': styles['ReportValue'],
        'table_header': styles['ReportTableHeader'],
        'table_cell': styles['ReportTableCell'],
    }


def _draw_page_header(canvas, document, title: str) -> None:
    canvas.saveState()
    canvas.setFont('Helvetica-Bold', 10)
    canvas.setFillColor(colors.HexColor('#111827'))
    canvas.drawString(document.leftMargin, A4[1] - 12 * mm, title)
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.HexColor('#6b7280'))
    canvas.drawRightString(A4[0] - document.rightMargin, A4[1] - 12 * mm, f'Página {canvas.getPageNumber()}')
    canvas.restoreState()
