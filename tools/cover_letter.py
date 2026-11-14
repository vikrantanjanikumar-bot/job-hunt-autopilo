"""One-page cover letters for the candidate.

Usage:
    python -I tools\\cover_letter.py <letters.json> [reportlab_lib_folder]

letters.json is a list of objects with keys:
    out   - full path of the PDF to write
    to    - addressee line, e.g. "Hiring Team, Eaton, Pune"
    role  - role and requisition, e.g. "Program Manager (Req 76794)"
    paras - list of paragraphs (reportlab markup: <b>..</b>, &amp;)
    date  - optional; defaults to today

Prints the page count of each letter; anything other than 1 must be shortened.
"""
import sys
import json
from datetime import date

import os
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resume_content.json'),
          encoding='utf-8') as _f:
    CAND = json.load(_f)

LIB = sys.argv[2] if len(sys.argv) > 2 else os.environ.get('JOBPIPE_LIB', '')
if LIB:
    sys.path.insert(0, LIB)

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from pypdf import PdfReader

pdfmetrics.registerFont(TTFont('Tahoma', r'C:\Windows\Fonts\tahoma.ttf'))
pdfmetrics.registerFont(TTFont('TahomaBd', r'C:\Windows\Fonts\tahomabd.ttf'))
body = ParagraphStyle('b', fontName='Tahoma', fontSize=12, leading=16.5, spaceAfter=8)
name = ParagraphStyle('n', fontName='TahomaBd', fontSize=16, leading=20, textColor=HexColor('#1F3864'))
bold = ParagraphStyle('bb', parent=body, fontName='TahomaBd')

d = date.today()
TODAY = f'{d.day} {d.strftime("%B %Y")}'

with open(sys.argv[1], encoding='utf-8') as f:
    letters = json.load(f)

for L in letters:
    doc = SimpleDocTemplate(L['out'], pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
                            topMargin=16 * mm, bottomMargin=14 * mm,
                            title='Cover Letter - ' + CAND['name'])
    s = [Paragraph(CAND['name'], name),
         Paragraph(CAND['contact'], body),
         Paragraph(L.get('date', TODAY), body),
         Paragraph(L['to'], body),
         Paragraph('Application: ' + L['role'], bold),
         Paragraph('Dear Hiring Team,', body)]
    s += [Paragraph(p, body) for p in L['paras']]
    s += [Paragraph('Yours sincerely,', body), Paragraph(CAND['name'], body)]
    doc.build(s)
    pages = len(PdfReader(L['out']).pages)
    flag = 'OK' if pages == 1 else 'TOO LONG - shorten'
    print(f'{pages} page(s) {flag}: {L["out"]}'.encode('ascii', 'replace').decode())
