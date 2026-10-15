"""Independent release checks and intentional-invalid-input tests."""
import pathlib,json,csv,sqlite3,subprocess,sys,hashlib,copy,math
from prepare_catalog import ROOT
from quality_control import validate
from generate_priors import generate
from normalize_units import normalize
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify():
    required=['plaque_multimodal_database.csv','sources.csv','plaque_type_priors.csv','README.md','data_dictionary.md','search_log.csv','excluded_sources.csv','quality_control_report.md','plaque_database.sqlite','dataset_catalog.csv','dataset_samples.csv','dataset_membership.csv','dataset_files.csv','supplement_audit.csv','03_processed_data/omics_workbook_cells.csv','supplement_update_report.md']
    assert all((ROOT/p).is_file() for p in required)
    raw={str(p.relative_to(ROOT)):digest(p) for p in (ROOT/'01_raw_sources').glob('*') if p.is_file()}
    before={p:digest(ROOT/p) for p in required if p.endswith('.csv')}
    subprocess.run([sys.executable,str(ROOT/'04_scripts/build_database.py')],check=True)
    assert all(digest(ROOT/p)==v for p,v in raw.items()),'Rebuild changed original evidence'
    assert all(digest(ROOT/p)==v for p,v in before.items()),'Offline rebuild changed CSV outputs'
    records=json.loads((ROOT/'02_extracted_data/records_curated.json').read_text(encoding='utf-8'))
    sources=list(csv.DictReader((ROOT/'sources.csv').open(encoding='utf-8-sig')))
    priors=generate(records)
    # Safety checks must reject ROS-to-H2O2 and pseudo-multimodal specimen assertions.
    invalid=copy.deepcopy(records)
    next(r for r in invalid if r['modality']=='ros_other')['h2o2_value']=1
    assert not validate(invalid,sources,priors)['passed']
    invalid=copy.deepcopy(records);invalid[0]['data_level']='A';invalid[0]['ml_eligible']=True
    assert not validate(invalid,sources,priors)['passed']
    # Exact unit scaling, with no chemical-basis conversion.
    sample=copy.deepcopy(records[0]);sample['mechanical_unit']='MPa';sample['mechanical_median']=2.5
    assert normalize(sample)['normalized_value']==2500
    peroxide=next(r for r in records if r['modality']=='H2O2')
    assert normalize(peroxide)['normalized_value'] is None
    with sqlite3.connect(ROOT/'plaque_database.sqlite') as db:
        assert db.execute('SELECT COUNT(*) FROM observations').fetchone()[0]==102
        assert db.execute('SELECT COUNT(*) FROM multimodal_supervised').fetchone()[0]==0
        assert db.execute("SELECT COUNT(*) FROM observations WHERE species='human' AND modality='H2O2'").fetchone()[0]==0
        assert db.execute('PRAGMA foreign_key_check').fetchall()==[]
        assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        assert db.execute('SELECT COUNT(*) FROM observations WHERE stress IS NOT NULL OR strain IS NOT NULL').fetchone()[0]==0
    result={'pass':True,'csv_rebuild_identical':True,'raw_files_unchanged':len(raw),'negative_tests':['ROS cannot populate H2O2','group summary cannot become A-level'],'sqlite_integrity':'ok','multimodal_supervised_rows':0,'human_h2o2_rows':0,'stress_strain_pairs':0,'requirements_checked':required}
    (ROOT/'05_reports/release_verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':verify()
