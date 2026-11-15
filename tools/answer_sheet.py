"""Build the answer sheet one form-filling bot needs for one job.

Usage:
    python -I tools/answer_sheet.py <JobID> <Employer> <Role> <portal> <resume.pdf> [cover.pdf]
           [--abroad] [--consent] [--url <apply link>]

portal: workday | successfactors | oracle | eightfold | linkedin | boards | other
Writes discovery/answers/<JobID>.md (the bot reads this instead of the whole facts file and
the whole portal playbook) and discovery/answers/<JobID>.json (used by review_check.py).
Every value comes from tools/form_facts.json; nothing is invented here.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PORTALS = ('workday', 'successfactors', 'oracle', 'eightfold', 'linkedin', 'boards', 'other')


def main():
    args = sys.argv[1:]
    abroad = '--abroad' in args
    consent = '--consent' in args
    url = ''
    if '--url' in args:
        i = args.index('--url')
        url = args[i + 1]
        del args[i:i + 2]
    args = [a for a in args if not a.startswith('--')]
    if len(args) < 5 or args[3] not in PORTALS:
        sys.exit(__doc__)
    job, employer, role, portal, resume = args[:5]
    cover = args[5] if len(args) > 5 else ''
    for f in (resume, cover):
        if f and not os.path.isfile(os.path.join(ROOT, 'uploads', os.path.basename(f))):
            sys.exit('File not found in uploads: ' + f)
    with open(os.path.join(HERE, 'form_facts.json'), encoding='utf-8') as fh:
        facts = json.load(fh)

    fields = dict(facts['fields'])
    drop = 'Expected CTC (India)' if abroad else 'Expected salary (abroad)'
    fields.pop(drop, None)

    out = ['# Answer sheet %s - %s, %s' % (job, employer, role), '']
    if url:
        out += ['Apply link: ' + url, '']
    out += ['## Documents (folder uploads/)', '- Resume: ' + os.path.basename(resume)]
    out.append('- Cover letter: ' + (os.path.basename(cover) if cover else 'none for this job'))
    out += ['- Remove any older resume or letter the portal has kept.', '',
            '## Portal notes', 'Read the %s section of `docs/PORTAL_NOTES.md` and the '
            '"All portals" list there. Nothing else.' % portal, '',
            '## Fields']
    out += ['- %s: %s' % kv for kv in fields.items()]
    out += ['', '## Standard answers']
    out += ['- %s: %s' % kv for kv in facts['standard_answers'].items()]
    out += ['', '## Years of experience by domain']
    out += ['- %s: %s' % kv for kv in facts['domain_years'].items()]
    out += ['', '## Rules']
    out += ['- ' + r for r in facts['rules']]
    out.append('- Consent ticks (privacy / terms of the application): '
               + ('AUTHORISED for this job.' if consent else 'NOT authorised - stop and report.'))
    out += ['- After each page: read every field back, fix what differs, then save the page.',
            '- Stop on the last page before submit. Do not submit.', '']

    expect = dict(facts['review_expect'])
    expect['Resume file'] = [os.path.basename(resume)]
    if cover:
        expect['Cover letter file'] = [os.path.basename(cover)]
    check = {'job': job, 'employer': employer, 'role': role, 'portal': portal,
             'expect': expect, 'forbid': facts['review_forbid'], 'look': facts['review_look']}

    d = os.path.join(ROOT, 'discovery', 'answers')
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, job + '.md'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('\n'.join(out))
    with open(os.path.join(d, job + '.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(check, fh, ensure_ascii=False, indent=1)
    print('Wrote discovery/answers/%s.md (%d characters) and .json' % (job, len('\n'.join(out))))


if __name__ == '__main__':
    main()
