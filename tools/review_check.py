"""Compare the text of a form's review page with the job's answer sheet, locally.

Usage:
    python -I tools/review_check.py <JobID> <review_page_text.txt>

Reads discovery/answers/<JobID>.json (written by answer_sheet.py). Prints one line per
expected value (OK / MISSING), every forbidden string found, and the lines that contain
words a person must look at (claims the candidate does not hold, importer-made employers).
Exit code 0 = PASS, 1 = FAIL. A PASS still needs the "LOOK" lines read by the reviewer.
"""
import json
import os
import re
import sys
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def norm(s):
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c)).lower()
    s = s.replace('&amp;', '&')
    return re.sub(r'\s+', ' ', s)


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    job, path = sys.argv[1], sys.argv[2]
    with open(os.path.join(ROOT, 'discovery', 'answers', job + '.json'), encoding='utf-8') as fh:
        sheet = json.load(fh)
    with open(path, encoding='utf-8', errors='replace') as fh:
        raw = fh.read()
    text = norm(raw)
    digits = re.sub(r'(?<=\d)[\s().-]+(?=\d)', '', text)  # joins digit groups split by spaces or dashes

    fail = 0
    print('Review check %s - %s, %s (%d characters of page text)'
          % (job, sheet['employer'], sheet['role'], len(raw)))
    if len(raw) < 500:
        print('FAIL: page text is too short to be a review page.')
        sys.exit(1)
    for label, values in sheet['expect'].items():
        hit = next((v for v in values if norm(v) in text or norm(v) in digits), None)
        if hit:
            print('OK       %-18s %s' % (label, hit))
        else:
            fail += 1
            print('MISSING  %-18s expected one of: %s' % (label, ' | '.join(values)))
    for bad in sheet['forbid']:
        if norm(bad) in text:
            fail += 1
            print('FORBIDDEN found: ' + bad)
    lines = [re.sub(r'\s+', ' ', l).strip() for l in raw.splitlines()]
    for word in sheet['look']:
        pat = re.compile(r'(?<![a-z0-9])' + re.escape(word.lower()) + r'(?![a-z0-9])')
        for i, l in enumerate(lines):
            if pat.search(norm(l)):
                nxt = lines[i + 1] if i + 1 < len(lines) else ''
                print(('LOOK     %s: %s | %s' % (word, l[:140], nxt[:60]))
                      .encode('ascii', 'replace').decode())
    print('RESULT: ' + ('FAIL - %d item(s) to fix' % fail if fail
                        else 'PASS on fixed fields - read the LOOK lines and screening answers'))
    sys.exit(1 if fail else 0)


if __name__ == '__main__':
    main()
