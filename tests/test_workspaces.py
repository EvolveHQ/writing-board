"""Project invariants: exchange, source authority, safe output and packaging."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import writing_board as wb
import story_workbench as engine


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bundle = wb.initial('Test book',['en','it','es','cs','sk'])
        self.bundle['bible']['characters'] = [dict(id='hero',name='Hero',summary='',appearance='',backstory='',want='',need='',voice='',speech_mode='verbal',facts=[],extensions={'age':None})]
        self.bundle['stories'] = [engine.new_packet('first-story','First story','hero',3)]

    def cli(self,*args,success=True):
        result=subprocess.run([sys.executable,str(ROOT/'scripts/writing_board.py'),*map(str,args)],cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
        if success:
            self.assertEqual(result.returncode,0,result.stderr+result.stdout)
        else:
            self.assertNotEqual(result.returncode,0,result.stdout)
        return result

    def test_documented_fresh_project_journey(self):
        path=self.root/'project'
        self.cli('init',path,'--title','My book','--languages','en','cs')
        self.cli('character',path,'--id','hero','--name','Hero')
        self.cli('story',path,'--id','first-story','--title','First story','--protagonist','hero','--spreads','3')
        self.cli('validate',path)
        self.cli('build',path)
        self.assertTrue((path/'build/board.html').exists())
        self.cli('export',path,'--output',self.root/'bundle.json')
        self.cli('import',path,'--bundle',self.root/'bundle.json','--output',self.root/'revised')
        self.cli('status',self.root/'revised')
        self.cli('handoff',self.root/'revised','--output',self.root/'handoff')
        manifest=wb.read(self.root/'handoff/manifest.json')
        self.assertEqual(manifest['packets'][0]['production_status'],'not_generated')
        self.assertIn('cs',manifest['missing_languages'])

    def test_empty_project_builds(self):
        path=self.root/'empty'
        wb.persist(path,wb.initial('Empty',['en']),new=True)
        self.assertTrue(wb.build(path).exists())

    def test_bundle_roundtrip_preserves_extensions_and_context(self):
        self.bundle['guidelines']['extensions']={'odd':{'nested':['α',42]}}
        edited=copy.deepcopy(self.bundle)
        edited['bible']['characters'][0]['backstory']='A new backstory.'
        result=wb.imported(self.bundle,edited)
        self.assertEqual(result['guidelines']['extensions'],self.bundle['guidelines']['extensions'])
        self.assertEqual(result['bible']['characters'][0]['backstory'],'A new backstory.')
        self.assertEqual(result['project']['revision'],2)
        self.assertEqual(self.bundle['project']['revision'],1)

    def test_import_rejects_stale_and_unrelated(self):
        for key,value in [('base_revision',2),('base_revision',True)]:
            edited=copy.deepcopy(self.bundle);edited[key]=value
            with self.assertRaises(ValueError):wb.imported(self.bundle,edited)
        edited=copy.deepcopy(self.bundle);edited['project']['id']='other'
        with self.assertRaises(ValueError):wb.imported(self.bundle,edited)

    def test_import_rejects_changed_project_revision(self):
        edited=copy.deepcopy(self.bundle);edited['project']['revision']=19
        with self.assertRaises(ValueError):wb.imported(self.bundle,edited)

    def test_context_change_stales_review_history(self):
        packet=self.bundle['stories'][0]
        packet['reviews']=[{'id':'review-one','kind':'editorial','status':'passed','packet_revision':1,'reviewer':'Test reviewer','notes':'Reviewed original.'}]
        edited=copy.deepcopy(self.bundle)
        edited['guidelines']['voice']=['A different voice.']
        result=wb.imported(self.bundle,edited)['stories'][0]
        self.assertEqual(result['reviews'][0]['status'],'stale')
        self.assertEqual(result['reviews'][0]['packet_revision'],1)
        self.assertEqual(result['revision'],2)
        self.assertEqual(result['page_plan']['status'],'needs_review')

    def test_build_detects_direct_edits_once(self):
        path=self.root/'book';wb.persist(path,self.bundle,new=True);wb.build(path)
        bible=wb.read(path/'bible.json');bible['characters'][0]['backstory']='Changed.';wb.write(path/'bible.json',bible)
        wb.build(path);self.assertEqual(wb.load_workspace(path)['project']['revision'],2)
        wb.build(path);self.assertEqual(wb.load_workspace(path)['project']['revision'],2)

    def test_invalid_source_build_does_not_advance_or_overwrite(self):
        path=self.root/'book';wb.persist(path,self.bundle,new=True);wb.build(path)
        before=(path/'build/board.html').read_bytes()
        bible=wb.read(path/'bible.json');bible['characters']=[];wb.write(path/'bible.json',bible)
        with self.assertRaises(ValueError):wb.build(path)
        self.assertEqual((path/'build/board.html').read_bytes(),before)
        self.assertEqual(wb.read(path/'project.json')['revision'],1)

    def test_evidence_only_build_preserves_current_review(self):
        path=self.root/'book';wb.persist(path,self.bundle,new=True);wb.build(path)
        packet=wb.read(path/'stories/first-story.json')
        packet['reviews']=[{'id':'review-one','kind':'editorial','status':'passed','packet_revision':1,'reviewer':'Test reviewer','notes':'Reviewed current manuscript.'}]
        wb.write(path/'stories/first-story.json',packet);wb.build(path)
        current=wb.load_workspace(path)
        self.assertEqual(current['project']['revision'],1)
        self.assertEqual(current['stories'][0]['reviews'][0]['status'],'passed')

    def test_unbuilt_edits_block_stale_bundle_adoption(self):
        path=self.root/'book';wb.persist(path,self.bundle,new=True);wb.build(path)
        wb.write(self.root/'old.json',self.bundle)
        packet=wb.read(path/'stories/first-story.json');packet['beats'][0]['text']='New source text.'
        wb.write(path/'stories/first-story.json',packet)
        for command in ('status','export','handoff','import'):
            args=[command,path]
            if command!='status':args+=['--output',self.root/(command+'-output')]
            if command=='import':args+=['--bundle',self.root/'old.json']
            result=self.cli(*args,success=False)
            self.assertIn('Unbuilt source edits',result.stderr)
        wb.build(path)
        self.cli('import',path,'--bundle',self.root/'old.json','--output',self.root/'revised',success=False)
        self.assertEqual(wb.read(path/'stories/first-story.json')['beats'][0]['text'],'New source text.')

    def test_malformed_root_documents_have_clear_errors(self):
        path=self.root/'book';wb.persist(path,self.bundle,new=True)
        wb.write(path/'stories/first-story.json',[])
        result=self.cli('validate',path,success=False)
        self.assertNotIn('Traceback',result.stderr)
        edited=copy.deepcopy(self.bundle);edited['project']=[]
        with self.assertRaises(ValueError):wb.imported(self.bundle,edited)

    def test_managed_mutation_then_unbuilt_edit_still_conflicts(self):
        path=self.root/'book';wb.persist(path,self.bundle,new=True);wb.build(path)
        self.cli('character',path,'--id','guest','--name','Guest')
        self.cli('export',path,'--output',self.root/'old.json')
        packet=wb.read(path/'stories/first-story.json');packet['beats'][0]['text']='Keep this new source text.'
        wb.write(path/'stories/first-story.json',packet)
        result=self.cli('import',path,'--bundle',self.root/'old.json','--output',self.root/'revised',success=False)
        self.assertIn('Unbuilt source edits',result.stderr)
        wb.build(path)
        self.assertEqual(wb.load_workspace(path)['project']['revision'],3)
        self.cli('import',path,'--bundle',self.root/'old.json','--output',self.root/'revised',success=False)

    def test_established_facts_need_source(self):
        self.bundle['bible']['world_rules']=[dict(id='rule',statement='A rule.',status='established',source_ref=None)]
        self.assertIn('source_ref',' '.join(wb.check_bundle(self.bundle)['errors']))

    def test_bible_references_and_duplicate_ids(self):
        self.bundle['bible']['characters'].append(copy.deepcopy(self.bundle['bible']['characters'][0]))
        self.assertIn('duplicate IDs',' '.join(wb.check_bundle(self.bundle)['errors']))
        self.bundle['bible']['characters']=[]
        self.assertIn('unknown reference',' '.join(wb.check_bundle(self.bundle)['errors']))

    def test_nonverbal_rule_comes_from_bible(self):
        packet=self.bundle['stories'][0]
        packet['beats'][0]['dialogue']=[{'speaker_id':'hero','kind':'speech','text':'Hello.'}]
        self.assertFalse(wb.check_bundle(self.bundle)['errors'])
        self.bundle['bible']['characters'][0]['speech_mode']='nonverbal'
        self.assertIn('nonverbal',' '.join(wb.check_bundle(self.bundle)['errors']))

    def test_unsafe_ids_cannot_write_files(self):
        self.bundle['stories'][0]['id']='../../escape'
        with self.assertRaises(ValueError):wb.persist(self.root/'bad',self.bundle,new=True)
        self.assertFalse((self.root/'bad').exists())

    def test_outputs_refuse_existing_destination(self):
        path=self.root/'project';wb.persist(path,self.bundle,new=True)
        with self.assertRaises(FileExistsError):wb.persist(path,self.bundle,new=True)
        output=self.root/'handoff';wb.handoff(self.bundle,output)
        with self.assertRaises(FileExistsError):wb.handoff(self.bundle,output)

    def test_symlinked_source_directory_cannot_escape_workspace(self):
        path=self.root/'book';path.mkdir();outside=self.root/'outside';outside.mkdir()
        try:(path/'stories').symlink_to(outside,target_is_directory=True)
        except OSError:self.skipTest('Directory symlinks unavailable on this host')
        with self.assertRaises(ValueError):wb.persist(path,self.bundle)
        self.assertEqual(list(outside.iterdir()),[])

    def test_duplicate_and_nonfinite_json_rejected(self):
        for content in ['{"x":1,"x":2}','{"x":NaN}']:
            path=self.root/'bad.json';path.write_text(content)
            with self.assertRaises(ValueError):wb.read(path)

    def test_schema_unknown_fields_are_explicit_errors(self):
        self.bundle['bible']['surprise']={'keep':'me'}
        self.assertIn('unsupported field',' '.join(wb.check_bundle(self.bundle)['errors']))

    def test_bundle_shape_not_silently_dropped(self):
        self.bundle['extra']='unrecognized'
        with self.assertRaises(ValueError):wb.imported(wb.initial('Base',['en']),self.bundle)

    def test_script_injection_is_inert(self):
        text='</script><script>alert(1)</script>'
        result=wb.inject('<script id="embedded-project" type="application/json">{}</script>','embedded-project',{'title':text})
        self.assertNotIn('<script>alert',result)
        self.assertIn('\\u003c/script>',result)
        self.assertEqual(json.loads(result.split('>',1)[1].rsplit('</script>',1)[0])['title'],text)

    def test_language_scope_and_budget(self):
        self.bundle['stories'][0]['language']='de'
        self.bundle['guidelines']['word_budget']={'min':200,'max':100}
        errors=' '.join(wb.check_bundle(self.bundle)['errors'])
        self.assertIn('language is not configured',errors)
        self.assertIn('min must not exceed',errors)

    def test_source_translation_reference(self):
        self.bundle['stories'][0]['source_story_id']='missing'
        self.assertIn('source_story_id',' '.join(wb.check_bundle(self.bundle)['errors']))

    def test_source_translation_cycles_rejected(self):
        self.bundle['stories'][0]['source_story_id']='first-story'
        self.assertIn('cycle',' '.join(wb.check_bundle(self.bundle)['errors']))

    def test_zero_spreads_is_error(self):
        path=self.root/'project';wb.persist(path,self.bundle,new=True)
        self.cli('story',path,'--id','bad','--title','Bad','--protagonist','hero','--spreads','0',success=False)


if __name__ == '__main__':unittest.main()
