"""Read source-only files and installed Python/API sources; never SDK/native."""
from pathlib import Path
import json, hashlib, zipfile, ast
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT.parents[1]
COLLECTOR=ROOT.parent/'collector'
PRIVATE=Path('/data/liyufeng/paperb_signed_force_calibration_20261015_v3')

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    c=COLLECTOR;p=PRIVATE
    freeze=json.loads((c/'SOURCE_FREEZE.json').read_text());release=json.loads((c/'EXECUTION_RELEASE.json').read_text())
    protocol=json.loads((c/'protocol.json').read_text());api=json.loads((c/'INSTALLED_API_PIN.json').read_text())
    assert sha(c/'SOURCE_FREEZE.json')=='29b848d388897fa8c08088e0bde940ec751585e83d308e137a26f99eacaace4f'
    assert sha(c/'EXECUTION_RELEASE.json')=='0de55ac995986d25a60f391b63d9606915dbeae37518e7cc4fb38ee75bc81771'
    for item in freeze['files']:
        assert sha(c/item['path'])==sha(p/item['private_flattened_path'])==item['sha256']
        assert (c/item['path']).stat().st_size==item['bytes']
    for name,pin in release['files'].items():assert sha(p/name)==pin
    for item in api['files'].values():assert sha(item['path'])==item['sha256'] and Path(item['path']).stat().st_size==item['bytes']
    archive_path=c/'force_fixture_v03_source.zip'
    assert sha(archive_path)=='702f4d1a84f8a9be956e509db7af5b3245322231d6a613131d5c920b2d6cd2c6'
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.testzip() is None and len(archive.infolist())==29
        for item in freeze['files']:
            name=next(n for n in archive.namelist() if n==item['path'] or n.endswith('/'+item['path']))
            assert hashlib.sha256(archive.read(name)).hexdigest()==item['sha256']
    parent=json.loads((c/'PARENT_FROZEN_FORCE_PROTOCOL_V02.json').read_text())
    for key in ('dt_s','setup','candidate_acceptance','cleanup_candidate','prospective_fixed_windows'):
        assert protocol[key]==parent[key],key
    metadata={'id','fixture_reference_case_id','contact_processing_disabled_requested','measurement_role',
              'positive_reference_case_id','negative_control_expected_scope'}
    clean=lambda obj:{k:v for k,v in obj.items() if k not in metadata}
    for new,old in zip(protocol['cases'][1:],parent['cases']):assert clean(new)==clean(old),(new['id'],old['id'])
    assert clean(protocol['cases'][0])==clean(parent['cases'][1])
    assert sum(x['controlled_steps'] for x in protocol['cases'])==5365
    assert [x['contact_processing_disabled_requested'] for x in protocol['cases']]==[True,False,False,False,False,False]
    assert protocol['cases'][0]['measurement_role']=='NEGATIVE_PROCESSING_DISABLED_CONTROL'
    budget=protocol['prospective_budget_confirmation']
    assert sha(budget['path'])=='8a9a74a00493454db0cbf54d2c0e4132ed3f3ddc528767ecd6daf646c0d004b9'
    selection=json.loads(Path(budget['path']).read_text())
    assert selection['selected_case_definitions']==protocol['cases']
    oldcode=BASE/'signed_force_fixture_calibration_v02_2026-10-15'/'independent_reader'/'code';newcode=ROOT/'code'
    for name in ('independent_math.py','cleanup_lifecycle.py'):assert (oldcode/name).read_bytes()==(newcode/name).read_bytes()
    def funcs(path):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef)}
    a,b=funcs(oldcode/'audit_fixture.py'),funcs(newcode/'audit_fixture.py')
    for name in a:
        if name!='main':assert a[name].replace('_v02','_v03').replace('calibration_v2:','calibration_v3:')==b[name],name
    report={'schema':'V03ProspectiveIndependentSourceVerification/1','status':'PASS_CPU_SOURCE_PRIVATE_API_ARCHIVE_AND_NUMERIC_INVARIANCE',
      'source_freeze_sha256':sha(c/'SOURCE_FREEZE.json'),'source_release_sha256':sha(c/'EXECUTION_RELEASE.json'),
      'NAS_and_private_files_verified':len(freeze['files']),'release_private_files_verified':len(release['files']),
      'installed_API_sources_verified':len(api['files']),'source_archive_members':29,'source_archive_crc':'PASS',
      'reader_math_byte_exact_parent':True,'reader_cleanup_byte_exact_parent':True,'reader_nonmain_functions_AST_identity_only':'PASS',
      'cases_positive_numeric_exact_parent':5,'negative_control_numeric_exact_C1':True,
      'root_selection_exact_case_objects':True,'no_native_GPU_SDK_executions':True,'native_outcomes_read':0,
      'opaque_backend_implementation_verified':False,'scope':'CONDITIONAL_FIXTURE_ONLY_NOT_ROBOT_LOAD_CHEMISTRY_SFR_OR_LEARNING'}
    destination=ROOT/'reports/SOURCE_VERIFICATION.json'
    with destination.open('x') as output:output.write(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:report[k] for k in ('status','NAS_and_private_files_verified','installed_API_sources_verified','source_archive_members')}))

if __name__=='__main__':main()
