"""Two-page resume variants for the candidate.

Usage:
    python -I tools\\resume.py <resume_content.json> <output_folder> [suffix] [reportlab_lib_folder]

Writes one PDF per variant in the content file, named <variant file><suffix>.pdf,
and prints page and word counts. Anything other than 2 pages needs editing.
Single-column flow text only (no tables or text boxes) so screening software reads
it in order.
"""
import sys
import os
import re
import json

LIB = sys.argv[4] if len(sys.argv) > 4 else os.environ.get('JOBPIPE_LIB', '')
if LIB:
    sys.path.insert(0, LIB)

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, KeepTogether
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER
from pypdf import PdfReader

pdfmetrics.registerFont(TTFont('Tahoma', r'C:\Windows\Fonts\tahoma.ttf'))
pdfmetrics.registerFont(TTFont('TahomaBd', r'C:\Windows\Fonts\tahomabd.ttf'))
pdfmetrics.registerFontFamily('Tahoma', normal='Tahoma', bold='TahomaBd',
                              italic='Tahoma', boldItalic='TahomaBd')

NAVY = HexColor('#1F3864')
SIZE = 10.3
body = ParagraphStyle('body', fontName='Tahoma', fontSize=SIZE, leading=SIZE * 1.33, spaceAfter=3)
name = ParagraphStyle('name', fontName='TahomaBd', fontSize=19, leading=23, textColor=NAVY,
                      alignment=TA_CENTER)
headline = ParagraphStyle('headline', fontName='TahomaBd', fontSize=10.5, leading=14,
                          textColor=NAVY, alignment=TA_CENTER)
contact = ParagraphStyle('contact', parent=body, alignment=TA_CENTER, fontSize=9.6, spaceAfter=2)
section = ParagraphStyle('section', fontName='TahomaBd', fontSize=11, leading=14, textColor=NAVY,
                         spaceBefore=7, spaceAfter=1)
strong = ParagraphStyle('strong', parent=body, fontName='TahomaBd', spaceBefore=4, spaceAfter=2)
bullet = ParagraphStyle('bullet', parent=body, leftIndent=11, bulletIndent=1, spaceAfter=2)


def sec(title):
    return [Paragraph(title, section),
            HRFlowable(width='100%', thickness=0.7, color=NAVY, spaceBefore=0, spaceAfter=4)]


def bullets(items):
    return [Paragraph(t, bullet, bulletText='•') for t in items]


def build(c, key, out):
    v = c['variants'][key]
    doc = SimpleDocTemplate(out, pagesize=A4, leftMargin=16 * mm, rightMargin=16 * mm,
                            topMargin=13 * mm, bottomMargin=12 * mm,
                            title='Resume - ' + c['name'], author=c['name'])
    s = [Paragraph(c['name'], name), Paragraph(v['headline'], headline),
         Paragraph(c['contact'], contact)]
    s += sec('PROFILE') + [Paragraph(v['profile'], body)]
    s += sec('CORE SKILLS') + [Paragraph(', '.join(v['skills']), body),
                               Paragraph('<b>Tools:</b> ' + c['tools'], body)]
    s += sec('PROFESSIONAL EXPERIENCE')
    s += [Paragraph(c['employer'], strong), Paragraph(c['title'], strong),
          Paragraph(c['role_summary'], body)]
    for p in c['programmes']:
        order = p.get('order', {}).get(key, range(len(p['bullets'])))
        items = [p['bullets'][i] for i in order]
        s.append(KeepTogether([Paragraph(p['head'], strong)] + bullets(items)))
    s += sec('EDUCATION') + bullets(c['education'])
    s += sec('CERTIFICATIONS AND TRAINING') + bullets(c['certifications'])
    s += sec('AWARDS') + bullets(c['awards'])
    s += sec('LANGUAGES') + [Paragraph(c['languages'], body)]
    doc.build(s)
    r = PdfReader(out)
    text = ' '.join(pg.extract_text(extraction_mode='layout') for pg in r.pages)
    words = len(re.findall(r'\S+', text))
    pages = len(r.pages)
    flag = 'OK' if pages == 2 else 'CHECK LENGTH'
    print(f'{pages} page(s) {flag}, {words} words: {out}'.encode('ascii', 'replace').decode())


with open(sys.argv[1], encoding='utf-8') as f:
    content = json.load(f)
folder = sys.argv[2]
suffix = sys.argv[3] if len(sys.argv) > 3 else ''
for k, var in content['variants'].items():
    build(content, k, os.path.join(folder, var['file'] + suffix + '.pdf'))
