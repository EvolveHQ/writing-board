"""Generate the complete Markdown and offline HTML documentation entrypoints."""
from pathlib import Path
import argparse
import html
import os
import re
from urllib.parse import quote, unquote

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT/'docs'
SKIP = {'.git','tmp','projects','build','__pycache__'}


def documents():
    return sorted(p for p in ROOT.rglob('*.md') if not (set(p.relative_to(ROOT).parts) & SKIP) and p != DOCS/'index.md')


def label(path):
    text=path.read_text(encoding='utf-8')
    heading=re.search(r'^# (.+)$',text,re.M)
    return heading[1] if heading else path.stem.replace('-',' ').title()


def relative(path, origin=DOCS):
    return Path(os.path.relpath(path,origin)).as_posix()


def inline(text,path):
    # Escape first; authored HTML is data. Only explicit Markdown links become
    # anchors, resolved relative to their source document, without network reads.
    escaped=html.escape(text)
    def link(m):
        href=html.unescape(m[2]).strip('<>')
        if re.match(r'^[A-Za-z][A-Za-z0-9+.-]*:',href):
            if not href.startswith(('https://','http://','mailto:')):
                return m[1]
            target=href
        else:
            file,_,anchor=href.partition('#')
            target=relative((path.parent/unquote(file)).resolve()) if file else relative(path)
            if anchor:target+='#'+anchor
        return '<a href="'+html.escape(target,quote=True)+'">'+m[1]+'</a>'
    escaped=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',link,escaped)
    escaped=re.sub(r'`([^`]+)`',r'<code>\1</code>',escaped)
    escaped=re.sub(r'\*\*([^*]+)\*\*',r'<strong>\1</strong>',escaped)
    return escaped


def render(path):
    rows=[]; block=[]; in_code=False; in_table=False; in_list=False
    raw=path.read_text(encoding='utf-8')
    raw=re.sub(r'^---\n.*?\n---\n','',raw,count=1,flags=re.S)
    def close():
        nonlocal in_table,in_list
        if in_table:rows.append('</tbody></table>');in_table=False
        if in_list:rows.append('</ul>');in_list=False
    for line in raw.splitlines():
        if line.startswith('```'):
            close()
            if in_code:rows.append('<pre><code>'+html.escape('\n'.join(block))+'</code></pre>');block=[]
            in_code=not in_code;continue
        if in_code:block.append(line);continue
        if line.startswith('|'):
            if re.fullmatch(r'[| :\-]+',line):continue
            if not in_table:close();rows.append('<table><tbody>');in_table=True
            rows.append('<tr>'+''.join('<td>'+inline(c.strip(),path)+'</td>' for c in line.strip('|').split('|'))+'</tr>');continue
        if re.match(r'^(?:- |\d+\. )',line):
            if not in_list:close();rows.append('<ul>');in_list=True
            rows.append('<li>'+inline(re.sub(r'^(?:- |\d+\. )','',line),path)+'</li>');continue
        close()
        head=re.match(r'^(#{1,6}) (.*)',line)
        if head:
            level=min(len(head[1])+1,6)
            rows.append(f'<h{level}>'+inline(head[2],path)+f'</h{level}>')
        elif line.strip():rows.append('<p>'+inline(line,path)+'</p>')
    close()
    if block:rows.append('<pre>'+html.escape('\n'.join(block))+'</pre>')
    return '\n'.join(rows)


def outputs():
    groups={'Start and contribute':[], 'Writing guides':[], 'Agent skills':[], 'Worksheets':[], 'Contributor decisions and plans':[]}
    for path in documents():
        rel=path.relative_to(ROOT).as_posix()
        group='Contributor decisions and plans' if rel.startswith('.docflow/') else 'Agent skills' if rel.startswith('skills/') else 'Worksheets' if rel.startswith('templates/') else 'Writing guides' if rel.startswith('docs/') else 'Start and contribute'
        groups[group].append(path)
    md=['# Documentation index\n','Start with the [README](../README.md), follow the [writing workflow](workflow.md), or open the [offline HTML reader](index.html). This index includes every maintained Markdown guide, skill, worksheet and contributor decision. Regenerate with `python scripts/build_docs.py`.\n']
    parts=[]
    for group,paths in groups.items():
        md.append('\n## '+group+'\n')
        parts.append('<section><h2>'+html.escape(group)+'</h2>')
        for path in paths:
            title=label(path);rel=relative(path)
            md.append(f'- [{title}]({rel})\n')
            parts.append('<details data-search="'+html.escape((title+' '+rel).lower(),quote=True)+'"><summary>'+html.escape(title)+' <span>'+html.escape(path.relative_to(ROOT).as_posix())+'</span></summary><article><a class="source" href="'+html.escape(rel,quote=True)+'">Open Markdown source</a>'+render(path)+'</article></details>')
        parts.append('</section>')
    data=['\n## Data and commands\n','- [Workspace contracts](contracts.md) and `python scripts/writing_board.py --help`.\n']
    for path in sorted((ROOT/'schemas').glob('*.json')):
        data.append(f'- [{path.name}]({relative(path)})\n')
    data.append('- [Original sample](../examples/rainy-day/project.json). Build it with `python scripts/writing_board.py build examples/rainy-day`.\n')
    md.extend(data)
    page='''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; base-uri 'none'; form-action 'none'"><title>Writing Board · Documentation</title><style>
:root{color-scheme:light;--ink:#223d3a;--paper:#fcf9f2;--line:#d5ded7;--green:#275951}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:17px/1.6 system-ui,sans-serif}main{max-width:1120px;margin:auto;padding:52px 24px 80px}header{margin-bottom:40px}h1{font-size:clamp(32px,5vw,54px);line-height:1.1;margin:12px 0}h2{margin-top:36px}a{color:#176958;text-underline-offset:3px}label{display:block;font-weight:650;margin-top:25px}input{width:100%;border:1px solid var(--line);border-radius:9px;padding:13px;font:inherit;background:white}details{border:1px solid var(--line);border-radius:10px;margin:10px 0;background:white}summary{cursor:pointer;padding:17px 20px;font-weight:650}summary span{display:block;font-size:12px;font-weight:400;color:#556963;margin-left:17px;overflow-wrap:anywhere}article{padding:10px 25px 30px;max-width:100%;border-top:1px solid var(--line)}article p{margin:7px 0}article h2{font-size:26px}article h3{font-size:21px}pre{overflow:auto;background:#f1f4f0;padding:18px;border-radius:7px;font-size:13px}code{background:#f1f4f0;font-size:.9em;padding:2px 3px}table{border-collapse:collapse;display:block;overflow:auto;width:100%;font-size:14px;margin:16px 0}td{border:1px solid var(--line);padding:9px;vertical-align:top}.source{font-size:13px}input:focus-visible,summary:focus-visible,a:focus-visible{outline:3px solid #dcad47;outline-offset:4px}footer{margin-top:40px;font-size:14px}[hidden]{display:none}
</style></head><body><main><header><small>WRITING BOARD / FIELD GUIDE</small><h1>From a first idea to a book plan.</h1><p>Start with the README or follow the writing workflow. Open any guide below to read it here. Authors and agents use the same documented files.</p><p><a href="../README.md">README</a> · <a href="workflow.md">Writing workflow</a> · <a href="index.md">Markdown index</a></p><label for="search">Find a guide, skill or worksheet</label><input id="search" type="search" placeholder="Try character, review, localization…"></header>'''+''.join(parts)+'''<footer>Generated by scripts/build_docs.py. Fully offline; no tracking or network requests. Schemas and command reference: <a href="contracts.md">Workspace contracts</a>.</footer></main><script>
document.getElementById('search').addEventListener('input',event=>{const query=event.target.value.toLowerCase().trim();document.querySelectorAll('details').forEach(item=>{item.hidden=!item.dataset.search.includes(query)});document.querySelectorAll('section').forEach(section=>{section.hidden=![...section.querySelectorAll('details')].some(item=>!item.hidden)})});
</script></body></html>\n'''
    return {DOCS/'index.md':''.join(md),DOCS/'index.html':page}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    for path,content in outputs().items():
        if args.check:
            if not path.exists() or path.read_text(encoding='utf-8') != content:raise SystemExit(f'{path.name} is stale; run python scripts/build_docs.py')
        else:path.write_text(content,encoding='utf-8',newline='\n')
    print('PASS: Markdown and HTML documentation indexes')


if __name__=='__main__':main()
