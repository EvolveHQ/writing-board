"""Run the local publication gate (Python 3.11+, Node 18+)."""
from pathlib import Path
import json
import os
import re
import subprocess
import sys
import tempfile
from urllib.parse import unquote

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import build_docs
import story_workbench
import writing_board


def run(*args):
    result=subprocess.run(args,cwd=ROOT,env={**os.environ,'PYTHONUTF8':'1'})
    if result.returncode:raise SystemExit(result.returncode)


def main():
    run(sys.executable,'scripts/docflow.py','--check')
    run(sys.executable,'scripts/build_docs.py','--check')
    for path in [*build_docs.documents(), ROOT/'docs/index.md']:
        if path.name.startswith('0000-'):continue
        for href in re.findall(r'\[[^\]]*\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
            target=href.strip('<>').split('#')[0]
            if not target or re.match(r'^[\w+.-]+:',target):continue
            if not (path.parent/unquote(target)).exists():raise ValueError(f'Broken documentation link: {path.relative_to(ROOT)} -> {href}')
    for skill in (ROOT/'skills').glob('*/SKILL.md'):
        raw=skill.read_text(encoding='utf-8')
        if not re.match(r'^---\nname: [a-z0-9-]+\ndescription: .+\n---\n',raw):raise ValueError(f'Invalid skill frontmatter: {skill}')
    if (ROOT/'CLAUDE.md').read_text(encoding='utf-8').strip()!='@AGENT.md':raise ValueError('CLAUDE.md must only import AGENT.md')
    raw=(ROOT/'web/board.html').read_text(encoding='utf-8')
    embedded=re.search(r'<script id="packet-schema" type="application/json">(.*?)</script>',raw,re.S)
    if not embedded or json.loads(embedded[1])!=story_workbench.load(ROOT/'schemas/story.schema.json'):raise ValueError('Board schema snapshot is stale')
    for marker in ('embedded-project','embedded-packets'):
        if raw.count(f'id="{marker}"')!=1:raise ValueError(f'Missing/duplicate board marker: {marker}')
    if re.search(r'<(?:script|link|img)[^>]+(?:src|href)=["\']https?://',raw,re.I):raise ValueError('Board must not load remote resources')
    writing_board.require_bundle(writing_board.load_workspace(ROOT/'examples/rainy-day'))
    run(sys.executable,'-m','unittest','discover','-s','tests','-p','test_*.py')
    run('node','tests/test_board_state.cjs')
    # Build from a temporary source copy: verification never changes the sample.
    with tempfile.TemporaryDirectory() as temp:
        path=Path(temp)/'sample'
        writing_board.persist(path,writing_board.load_workspace(ROOT/'examples/rainy-day'),new=True)
        writing_board.build(path)
        writing_board.handoff(writing_board.load_workspace(path),Path(temp)/'handoff')
    print('PASS: project, story engine, browser state, skills, documentation and handoff')


if __name__=='__main__':
    try:main()
    except (OSError,ValueError,KeyError,TypeError) as error:raise SystemExit(f'FAIL: {error}')
