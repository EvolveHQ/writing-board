"""Create, validate, package and exchange portable writing projects."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path

import story_workbench as story

ROOT = Path(__file__).resolve().parents[1]
ID = re.compile(r'^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$')
LANG = re.compile(r'^[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$')
MAX_BYTES = 20 * 1024 * 1024
BUNDLE_KEYS = {'bundle_version','base_revision','project','guidelines','bible','stories'}


def read(path):
    path = Path(path)
    if path.stat().st_size > MAX_BYTES:
        raise ValueError(f'{path.name}: exceeds 20 MiB input limit')
    return story.load(path)


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = value if isinstance(value, str) else story.json_text(value)
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', newline='\n', dir=path.parent, delete=False) as handle:
        temp = Path(handle.name)
        handle.write(text)
    try:
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


def authored_content(bundle):
    """Compare authored work independently of revision and review bookkeeping."""
    result = copy.deepcopy(bundle)
    result.pop('base_revision',None)
    if isinstance(result.get('project'),dict):
        result['project'].pop('revision',None)
    for packet in result.get('stories',[]):
        if not isinstance(packet,dict):
            continue
        for field in ('revision','status','reviews','proofs'):
            packet.pop(field,None)
        if isinstance(packet.get('page_plan'),dict):
            packet['page_plan'].pop('status',None)
        if isinstance(packet.get('extensions'),dict):
            packet['extensions'].pop('workbench_base_revision',None)
            if not packet['extensions']:
                packet.pop('extensions')
    return result


def guard_workspace(path):
    root = Path(path).resolve()
    for name in ('project.json','guidelines.json','bible.json','stories','build'):
        if not (root / name).resolve().is_relative_to(root):
            raise ValueError(f'{name} must remain inside the selected workspace')
    return root


def load_workspace(path, *, check_freshness=True):
    path = guard_workspace(path)
    bundle = {name: read(path / f'{name}.json') for name in ('project','guidelines','bible')}
    for name in ('project','guidelines','bible'):
        errors = schema_errors(bundle[name],name)
        if errors:
            raise ValueError('\n'.join(errors))
    packet_paths = sorted((path / 'stories').glob('*.json'))
    if any(not item.resolve().is_relative_to(path) for item in packet_paths):
        raise ValueError('Story files must stay inside the workspace')
    bundle.update(bundle_version=1, base_revision=bundle['project']['revision'], stories=[read(p) for p in packet_paths])
    if any(not isinstance(s,dict) or p.stem != s.get('id') for p,s in zip(packet_paths,bundle['stories'])):
        raise ValueError('Each story filename must equal its stable ID')
    snapshot = path / 'build/source-state.json'
    if not snapshot.exists():
        snapshot = path / 'build/snapshot.json'
    if check_freshness and snapshot.exists():
        previous = read(snapshot)
        if bundle['project']['revision'] != previous['project']['revision'] or authored_content(bundle) != authored_content(previous):
            raise ValueError('Unbuilt source edits: run build for this project before validating, exporting, importing, checking status or preparing a handoff')
    return bundle


def schema_errors(value, name):
    schema = read(ROOT / 'schemas' / f'{name}.schema.json')
    return story.schema_errors(value, schema, schema.get('$defs', {}), name)


def check_bundle(bundle):
    errors, warnings = [], []
    if not isinstance(bundle, dict) or set(bundle) != BUNDLE_KEYS:
        return {'errors':['Bundle requires exactly bundle_version, base_revision, project, guidelines, bible, stories'], 'warnings':[]}
    if type(bundle['bundle_version']) is not int or bundle['bundle_version'] != 1:
        errors.append('Unsupported bundle version')
    if type(bundle['base_revision']) is not int or not 1 <= bundle['base_revision'] < 2**53:
        errors.append('Bundle base_revision must be a positive safe integer')
    for name in ('project','guidelines','bible'):
        errors.extend(schema_errors(bundle[name], name))
    if not isinstance(bundle['stories'], list):
        errors.append('stories must be an array')
    if errors:
        return {'errors':errors,'warnings':warnings}
    project, guidelines, bible = (bundle[k] for k in ('project','guidelines','bible'))
    if project['revision'] != bundle['base_revision']:
        errors.append('Project revision must match bundle base_revision')
    if not 1 <= project['default_spreads'] <= 200:
        errors.append('default_spreads must be between 1 and 200')
    if guidelines['word_budget']['min'] > guidelines['word_budget']['max']:
        errors.append('word_budget min must not exceed max')
    languages = project['languages']
    if len(set(languages)) != len(languages) or any(not LANG.fullmatch(x) for x in languages):
        errors.append('languages must contain unique language tags, e.g. en, it, es, cs, sk')
    characters = {c['id']:c for c in bible['characters']}
    locations = {loc['id'] for loc in bible['locations']}

    def unique(items, label):
        ids = [item['id'] for item in items]
        if len(ids) != len(set(ids)):
            errors.append(f'{label}: duplicate IDs')

    def fact(item, label):
        if item['status'] != 'proposed' and not (item['source_ref'] or '').strip():
            errors.append(f'{label}: sourced/established entries require a source_ref')

    for name in ('characters','locations','world_rules','relationships','timeline'):
        unique(bible[name], f'bible.{name}')
    for item in bible['characters'] + bible['locations']:
        unique(item['facts'], item['id'] + '.facts')
        for value in item['facts']:
            fact(value, item['id'] + '.' + value['id'])
    for item in bible['world_rules'] + bible['relationships']:
        fact(item,item['id'])
    for rel in bible['relationships']:
        if rel['from_id'] not in characters or rel['to_id'] not in characters or rel['from_id'] == rel['to_id']:
            errors.append(f'{rel["id"]}: relationship requires two distinct known characters')
    for event in bible['timeline']:
        if any(c not in characters for c in event['character_ids']) or len(event['character_ids']) != len(set(event['character_ids'])):
            errors.append(f'{event["id"]}: unknown or duplicate timeline character')
    for term in bible['glossary']:
        if term['language'] not in languages:
            errors.append(f'Glossary {term["term"]}: language is not configured')
    packet_ids = []
    for packet in bundle['stories']:
        report = story.check_packet(packet, known_ids=characters)
        label = packet.get('id','story') if isinstance(packet,dict) else 'story'
        errors.extend(f'{label}: {v}' for v in report['errors'])
        warnings.extend(f'{label}: {v}' for v in report['warnings'])
        if report['errors']:
            continue
        packet_ids.append(packet['id'])
        if packet['language'] not in languages:
            errors.append(f'{label}: story language is not configured')
        for loc in packet['locations']:
            if loc['id'] not in locations:
                errors.append(f'{label}: location {loc["id"]} is absent from the bible')
        for beat in packet['beats']:
            for line in beat['dialogue']:
                c = characters.get(line['speaker_id'],{})
                if line['kind'] == 'speech' and c.get('speech_mode') == 'nonverbal':
                    errors.append(f'{label}/{beat["id"]}: {line["speaker_id"]} is nonverbal in the bible')
        words = sum(len(re.findall(r"\S+", b['text'])) for b in packet['beats'])
        if not guidelines['word_budget']['min'] <= words <= guidelines['word_budget']['max']:
            warnings.append(f'{label}: {words} manuscript words outside configured target; editorial review decides fit')
    if len(packet_ids) != len(set(packet_ids)):
        errors.append('Story IDs must be unique in a project')
    for packet in bundle['stories']:
        if isinstance(packet,dict) and packet.get('source_story_id') and packet['source_story_id'] not in packet_ids:
            errors.append(f'{packet.get("id")}: source_story_id must identify a story in this project')
    sources = {p['id']:p.get('source_story_id') for p in bundle['stories'] if isinstance(p,dict) and isinstance(p.get('id'),str) and isinstance(p.get('source_story_id'),(str,type(None)))}
    for identifier in sources:
        seen, current = set(), identifier
        while current in sources:
            if current in seen:
                errors.append(f'{identifier}: source_story_id cannot reference itself or form a cycle')
                break
            seen.add(current)
            current = sources[current]
    return {'errors':errors,'warnings':warnings}


def require_bundle(bundle):
    report = check_bundle(bundle)
    if report['errors']:
        raise ValueError('\n'.join(report['errors']))
    return report


def persist(path, bundle, *, new=False):
    require_bundle(bundle)
    path = guard_workspace(path)
    if new:
        path.mkdir(parents=True, exist_ok=False)
    for name in ('project','guidelines','bible'):
        write(path / f'{name}.json', bundle[name])
    (path / 'stories').mkdir(exist_ok=True)
    for packet in bundle['stories']:
        write(path / 'stories' / f'{packet["id"]}.json', packet)
    # Managed mutations may precede the next HTML build. Keep their accepted
    # source baseline too, so subsequent direct edits cannot evade conflicts.
    write(path / 'build/source-state.json',bundle)


def initial(title, languages, audience='Children aged 3–6', spreads=14, project_id=None):
    slug = re.sub(r'[^a-z0-9]+','-',title.lower()).strip('-')
    slug = slug if ID.fullmatch(slug) else 'my-project'
    return {
        'bundle_version':1,'base_revision':1,
        'project':{'schema_version':1,'id':project_id or slug,'title':title,'revision':1,'audience':audience,'languages':languages,'format':'illustrated-book','default_spreads':spreads,'extensions':{}},
        'guidelines':{'schema_version':1,'profile':'Picture book · editable starting point',
            'voice':['Concrete language, clear rhythm and natural read-aloud phrasing.'],
            'teaching':['Choose one focus when teaching is intended; show its use through consequences.'],
            'content_boundaries':['Use audience-appropriate stakes and a resolution that leaves room for warmth.'],
            'composition':['Give each spread a clear action and a reason to turn the page.','Let words and images contribute different information.','Keep text clear of faces, action, trim and gutter.'],
            'word_budget':{'min':150,'max':600},'required_reviews':['editorial','continuity','read_aloud','layout','art','translation'],'extensions':{}},
        'bible':{'schema_version':1,'characters':[],'locations':[{'id':'home','name':'Home','description':'Develop this location.','facts':[],'extensions':{}}], 'world_rules':[],'relationships':[],'timeline':[],'glossary':[],'extensions':{}},
        'stories':[]}


def advance(bundle):
    bundle['project']['revision'] += 1
    bundle['base_revision'] = bundle['project']['revision']
    for packet in bundle['stories']:
        story.invalidate_evidence(packet,packet['revision'] + 1)


def imported(base, edited):
    require_bundle(base)
    if not isinstance(edited,dict) or set(edited) != BUNDLE_KEYS:
        raise ValueError('Invalid project bundle shape')
    if type(edited['base_revision']) is not int or type(edited['bundle_version']) is not int or edited['bundle_version'] != 1:
        raise ValueError('Invalid bundle version or base_revision type')
    if not isinstance(edited['project'],dict):
        raise ValueError('project must be an object')
    if edited.get('base_revision') != base['project']['revision'] or edited.get('project',{}).get('id') != base['project']['id']:
        raise ValueError('Stale or unrelated project bundle; reload the current base')
    if edited['project'].get('revision') != edited['base_revision']:
        raise ValueError('Edited project revision must still match its base_revision')
    # Clear inherited approval claims before semantic validation. Shape validation
    # precedes mutation, so malformed drafts cannot be partly adopted.
    for name in ('project','guidelines','bible'):
        errors = schema_errors(edited[name],name)
        if errors:
            raise ValueError('\n'.join(errors))
    if not isinstance(edited['stories'],list):
        raise ValueError('stories must be an array')
    schema = read(ROOT / 'schemas/story.schema.json')
    for packet in edited['stories']:
        errors = story.schema_errors(packet,schema,schema['$defs'])
        if errors:
            raise ValueError('\n'.join(errors))
    result = copy.deepcopy(edited)
    revisions = {p['id']:p['revision'] for p in base['stories']}
    for packet in result['stories']:
        story.invalidate_evidence(packet,revisions.get(packet['id'],0) + 1)
    result['project']['revision'] = base['project']['revision'] + 1
    result['base_revision'] = result['project']['revision']
    require_bundle(result)
    return result


def inject(template, marker, value):
    pattern = rf'(<script id="{re.escape(marker)}" type="application/json">).*?(</script>)'
    payload = json.dumps(value,ensure_ascii=False,allow_nan=False).replace('<','\\u003c')
    result, count = re.subn(pattern,lambda m:m[1]+payload+m[2],template,flags=re.S)
    if count != 1:
        raise ValueError(f'Expected exactly one {marker} marker')
    return result


def build(path):
    path = Path(path)
    bundle = load_workspace(path,check_freshness=False)
    previous_path = path / 'build' / 'source-state.json'
    if not previous_path.exists():
        previous_path = path / 'build' / 'snapshot.json'
    previous = read(previous_path) if previous_path.exists() else None
    # Source-state follows every managed write, independent of HTML builds.
    if previous and bundle['project']['revision'] != previous['project']['revision']:
        raise ValueError('Do not change project revision manually; restore the accepted source revision before rebuilding')
    if previous and authored_content(bundle) != authored_content(previous):
        bundle = imported(previous,bundle)
    report = require_bundle(bundle)
    template = (ROOT / 'web/board.html').read_text(encoding='utf-8')
    template = inject(template,'packet-schema',read(ROOT / 'schemas/story.schema.json'))
    template = inject(template,'embedded-project',bundle)
    template = inject(template,'embedded-packets',bundle['stories'])
    files = {'board.html':template,'snapshot.json':story.json_text(bundle),'validation.json':story.json_text(report)}
    for packet in bundle['stories']:
        for name,text in story.render_views(packet).items():
            files[f'stories/{packet["id"]}/{name}'] = text
    persist(path,bundle)
    for name,value in files.items():
        write(path / 'build' / name,value)
    return path / 'build/board.html'


def status(bundle):
    report = require_bundle(bundle)
    rows = []
    for packet in bundle['stories']:
        passed = {r['kind'] for r in packet['reviews'] if r['status']=='passed' and r['packet_revision']==packet['revision'] and r.get('reviewer')}
        missing = [kind for kind in bundle['guidelines']['required_reviews'] if kind not in passed]
        rows.append({'id':packet['id'],'language':packet['language'],'revision':packet['revision'],'missing_reviews':missing})
    next_step = 'Create the first character dossier.' if not bundle['bible']['characters'] else 'Create a story and develop its premise.' if not rows else 'Develop and review current stories; inspect missing_reviews.'
    return {'project':bundle['project']['title'],'revision':bundle['project']['revision'],'next_step':next_step,'stories':rows,'warnings':report['warnings'],'approval':'No quality approval is inferred from these checks.'}


def handoff(bundle, output):
    require_bundle(bundle)
    if not bundle['stories']:
        raise ValueError('Create a story before preparing a production handoff')
    output = Path(output)
    if output.exists():
        raise FileExistsError('Handoff output must be a new directory')
    files = {}
    packets = []
    for packet in bundle['stories']:
        files[f'{packet["id"]}/manuscript.md'] = '# '+packet['title']+'\n\n'+'\n\n'.join(b['text'] or '[Unwritten beat: '+b['id']+']' for b in packet['beats'])+'\n'
        files[f'{packet["id"]}/art-briefs.json'] = story.json_text({'packet_id':packet['id'],'revision':packet['revision'],'cover':{'title':packet['title'],'brand_assets':'Supply project-owned logo and rights information.'},'spreads':[{'id':s['id'],'pages':[s['left_page'],s['right_page']],'composition':s.get('composition',{}),'page_turn':s['page_turn'],'reveal':s['reveal'],'beats':[b for b in packet['beats'] if b['id'] in s['beat_ids']]} for s in packet['page_plan']['story_spreads']]})
        packets.append({'id':packet['id'],'language':packet['language'],'revision':packet['revision'],'sha256':hashlib.sha256(story.json_text(packet).encode()).hexdigest(),'requested_deliverables':['reading PDF','printer-specific publishing PDF','EPUB'],'production_status':'not_generated'})
    manifest = {'project_id':bundle['project']['id'],'project_revision':bundle['project']['revision'],'languages':bundle['project']['languages'],'packets':packets,'review_status':status(bundle),'missing_languages':[lang for lang in bundle['project']['languages'] if lang not in {p['language'] for p in bundle['stories']}], 'limitations':['Planning handoff only: artwork, PDFs and EPUBs are not generated.','Printer trim, bleed, fonts, color profile and export checks remain to be supplied.','Review each story family for language coverage; project coverage alone does not prove every story was translated.']}
    files['manifest.json'] = story.json_text(manifest)
    files['project-bundle.json'] = story.json_text(bundle)
    files['README.md'] = '# Production handoff\n\nUse manifest.json to identify exact source revisions and missing reviews.\nManuscripts and art briefs are draft inputs, not finished publication files.\nConfirm language coverage for each source story, commission assets, compose pages,\nthen proof the reading PDF, printer-specific PDF and EPUB independently.\n'
    output.mkdir(parents=True,exist_ok=False)
    for name,value in files.items():
        write(output / name,value)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command',required=True)
    init = sub.add_parser('init',help='Create a private project scaffold')
    init.add_argument('project'); init.add_argument('--title',default='My book'); init.add_argument('--id')
    init.add_argument('--audience',default='Children aged 3–6'); init.add_argument('--languages',nargs='+',default=['en'])
    init.add_argument('--spreads',type=int,default=14); init.add_argument('--interactive',action='store_true')
    for command in ('validate','build','status','export','import','handoff','character','story'):
        p = sub.add_parser(command)
        p.add_argument('project')
        if command in ('export','import','handoff'):
            p.add_argument('--output',required=True)
        if command == 'import':
            p.add_argument('--bundle',required=True)
        if command in ('character','story'):
            p.add_argument('--id',required=True)
        if command == 'character':
            p.add_argument('--name',required=True)
        if command == 'story':
            p.add_argument('--title',required=True); p.add_argument('--protagonist',required=True)
            p.add_argument('--language'); p.add_argument('--spreads',type=int)
    args = parser.parse_args(argv)
    try:
        if args.command == 'init':
            if args.interactive:
                args.title = input(f'Title [{args.title}]: ').strip() or args.title
                args.audience = input(f'Audience [{args.audience}]: ').strip() or args.audience
                args.languages = (input(f'Language tags, separated by spaces [{" ".join(args.languages)}]: ').strip() or ' '.join(args.languages)).split()
                args.spreads = int(input(f'Story spreads [{args.spreads}]: ').strip() or args.spreads)
            persist(args.project,initial(args.title,args.languages,args.audience,args.spreads,args.id),new=True)
            print(f'Created {args.project}. Set guidelines and create a character; use status for next steps.')
            return 0
        if args.command == 'build':
            print(f'Built {build(args.project)}')
            return 0
        bundle = load_workspace(args.project)
        if args.command == 'validate':
            report = check_bundle(bundle)
            print(story.json_text(report))
            return int(bool(report['errors']))
        require_bundle(bundle)
        if args.command == 'status':
            print(story.json_text(status(bundle)))
        elif args.command == 'export':
            story.save_new(args.output,story.json_text(bundle))
            print(f'Exported {args.output}')
        elif args.command == 'import':
            persist(args.output,imported(bundle,read(args.bundle)),new=True)
            print(f'Imported {args.output}; reviews require a new pass. Build this revised project next.')
        elif args.command == 'handoff':
            handoff(bundle,args.output)
            print(f'Prepared {args.output}; finished artwork/PDF/EPUB are not generated.')
        elif args.command == 'character':
            if any(c['id']==args.id for c in bundle['bible']['characters']):
                raise ValueError('Character already exists; edit its dossier in bible.json or the board')
            bundle['bible']['characters'].append(dict(id=args.id,name=args.name,summary='',appearance='',backstory='',want='',need='',voice='',speech_mode='unspecified',facts=[],extensions={}))
            advance(bundle); persist(args.project,bundle)
            print(f'Created dossier {args.id}. Fill in its profile and sources.')
        elif args.command == 'story':
            if any(p['id']==args.id for p in bundle['stories']):
                raise ValueError('Story ID already exists')
            if args.protagonist not in {c['id'] for c in bundle['bible']['characters']}:
                raise ValueError('Create the protagonist in the bible first')
            if not bundle['bible']['locations']:
                raise ValueError('Create a location in the bible first')
            spreads = bundle['project']['default_spreads'] if args.spreads is None else args.spreads
            if not 1 <= spreads <= 200:
                raise ValueError('Story spread count must be between 1 and 200')
            packet = story.new_packet(args.id,args.title,args.protagonist,spreads)
            packet['language'] = args.language or bundle['project']['languages'][0]
            location = bundle['bible']['locations'][0]
            old = packet['locations'][0]
            old.update(id=location['id'],name=location['name'],source_status='proposed',source_ref=None)
            for beat in packet['beats']:
                beat['location_id'] = location['id']
            advance(bundle); bundle['stories'].append(packet); persist(args.project,bundle)
            print(f'Created {args.id}; develop purpose, premise, beats and composition before review.')
        return 0
    except (OSError,ValueError,TypeError,KeyError,EOFError) as error:
        print(f'ERROR: {error}',file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
