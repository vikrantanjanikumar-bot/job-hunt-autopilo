"""Per-job resume for the candidate, built only from approved wording.

Usage:
    python -I tools\\tailor_resume.py <jd.txt> <base: controls|npi|defence> <Employer_Role_slug>

What it changes (nothing is invented, no sentence is rewritten):
  - Core skills: the base variant's own skills, with those whose words appear in the job
    description moved to the front. No skill is added, dropped or borrowed.
  - Bullets inside each programme: the ones sharing most words with the job description
    come first. Programme order (chronology), profile and headline stay as the base variant.
Writes uploads\\<Name>_Resume_<slug>_<date>.pdf through tools\\resume.py and prints
the page count (must be 2) and the job-description keywords the resume does not contain,
so they can be checked with the candidate before anything is claimed.
"""
import sys
import os
import re
import json
import subprocess
import tempfile
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
STOP = set('''a an the and or of in on for to with by from at as is are be this that will you your our we
their its it have has can may must should including include etc other all any more than into across within
role job work team teams experience years year ability strong good skills skill knowledge required
preferred responsibilities responsible ensure manage management manager project projects
his her his/her not who whom which when where what how also such each both per via well new
associated relevant define defined respect case members managers functionally challenge
project/system based using use used make made take taken given within without'''.split())


def words(text):
    return [w for w in re.findall(r'[a-z][a-z0-9+/&-]{2,}', text.lower()) if w not in STOP]


def overlap(text, jd_set):
    return sum(1 for w in set(words(text)) if w in jd_set)


def main():
    jd_path, base, slug = sys.argv[1], sys.argv[2], sys.argv[3]
    with open(jd_path, encoding='utf-8', errors='replace') as f:
        jd = f.read()
    with open(os.path.join(HERE, 'resume_content.json'), encoding='utf-8') as f:
        c = json.load(f)
    jd_words = words(jd)
    jd_set = set(jd_words)
    v = dict(c['variants'][base])

    base_skills = list(v['skills'])  # reorder only: never borrow skills from another variant
    v['skills'] = sorted(base_skills, key=lambda x: (-overlap(x, jd_set), base_skills.index(x)))
    v['file'] = c['name'].replace(' ', '_') + '_Resume_' + slug

    for p in c['programmes']:
        base_order = list(p.get('order', {}).get(base, range(len(p['bullets']))))
        p.setdefault('order', {})['job'] = sorted(
            base_order, key=lambda i: (-overlap(p['bullets'][i], jd_set), base_order.index(i)))
    c['variants'] = {'job': v}

    tmp = os.path.join(tempfile.gettempdir(), 'resume_job_%s_%d.json' % (slug[:40], os.getpid()))
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(c, f, ensure_ascii=False)
    suffix = '_' + date.today().isoformat()
    subprocess.run([sys.executable, '-I', os.path.join(HERE, 'resume.py'), tmp,
                    os.path.join(ROOT, 'uploads'), suffix], check=True)

    resume_words = set(words(json.dumps(c, ensure_ascii=False)))
    freq = {}
    for w in jd_words:
        freq[w] = freq.get(w, 0) + 1
    missing = [w for w, n in sorted(freq.items(), key=lambda x: -x[1])
               if n >= 2 and w not in resume_words][:20]
    print('Base variant:', base)
    print('Skills first:', '; '.join(v['skills'][:6]).encode('ascii', 'replace').decode())
    print('JD words not in resume (ask the candidate before claiming):',
          ', '.join(missing).encode('ascii', 'replace').decode())


if __name__ == '__main__':
    main()
