"""Check repository scope, real sample identity, matrix headers, provenance and dedup."""
import csv,gzip,hashlib,json,sqlite3,collections
from prepare_catalog import ROOT
def verify():
    checks=[]
    def check(ok,msg):
        checks.append({'check':msg,'passed':bool(ok)})
        if not ok:raise AssertionError(msg)
    with sqlite3.connect(ROOT/'plaque_database.sqlite') as db:
        db.row_factory=sqlite3.Row
        check(db.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLite integrity')
        check(not db.execute('PRAGMA foreign_key_check').fetchall(),'All foreign keys')
        check(db.execute('SELECT count(*) FROM sources').fetchone()[0]==35,'35 source entities, not independent studies')
        check(db.execute('SELECT count(*) FROM dataset_catalog').fetchone()[0]==10,'10 accession records including parent/children')
        check(db.execute('SELECT count(*) FROM dataset_samples').fetchone()[0]==193,'193 unique sample/library annotations')
        check(db.execute('SELECT count(*) FROM dataset_membership').fetchone()[0]==217,'217 memberships preserve shared parent/subseries samples')
        check(db.execute('SELECT count(*) FROM observations').fetchone()[0]==102,'Target measurements unchanged')
        check(db.execute('SELECT count(*) FROM multimodal_supervised').fetchone()[0]==0,'No manufactured physical/chemical A/B samples')
        check(db.execute('SELECT count(*) FROM dataset_samples WHERE target_multimodal_eligible!=0').fetchone()[0]==0,'Omics does not imply target multimodal eligibility')
        expected={'GSE28829':29,'GSE43292':64,'GSE163154':43,'GSE159677':6,'GSE210152':6,'GSE253902':12,'GSE253903':12,'GSE253904':24,'PXD039077':21}
        for a,n in expected.items():
            check(db.execute('SELECT count(*) FROM dataset_membership WHERE dataset_id=?',(a,)).fetchone()[0]==n,a+' membership count')
        for a in ['GSE253902','GSE253903']:
            child={r[0] for r in db.execute('SELECT sample_key FROM dataset_membership WHERE dataset_id=?',(a,))}
            parent={r[0] for r in db.execute("SELECT sample_key FROM dataset_membership WHERE dataset_id='GSE253904'")}
            check(child.issubset(parent),a+' samples are already in parent, not duplicate people')
        check(db.execute("SELECT count(DISTINCT subject_id) FROM omics_phenotype_samples WHERE dataset_id='GSE253904'").fetchone()[0]==18,'18 deposited GSE253904 donor labels')
        check(db.execute("SELECT count(DISTINCT subject_id) FROM omics_phenotype_samples WHERE dataset_id='GSE253904' AND symptom_status='Symptomatic'").fetchone()[0]==11,'11 deposited symptomatic donors, not 13 inferred')
        check(db.execute("SELECT count(*) FROM dataset_samples WHERE standardized_plaque_type='Normal / non-atherosclerotic vessel'").fetchone()[0]==0,'No diseased comparator is falsely labeled healthy')
        for a in ['GSE43292','GSE159677']:
            counts=db.execute('SELECT subject_id,count(*) FROM omics_phenotype_samples WHERE dataset_id=? GROUP BY subject_id',(a,)).fetchall()
            check(all(r[0] is not None and r[1]==2 for r in counts),a+' true patient pairs')
        morph=dict(db.execute("SELECT original_label,count(*) FROM omics_phenotype_samples WHERE dataset_id='PXD039077' GROUP BY original_label").fetchall())
        check(morph=={'Hard':7,'Mixed':7,'Soft':7},'PXD039077 original three groups')
        matrices=[]
        for r in db.execute('SELECT * FROM dataset_files WHERE downloaded=1').fetchall():
            p=ROOT/r['local_path'];raw=p.read_bytes()
            check(hashlib.sha256(raw).hexdigest()==r['sha256'],p.name+' SHA-256')
            if r['repository_sha1']:check(hashlib.sha1(raw).hexdigest()==r['repository_sha1'],p.name+' repository SHA-1')
            if r['repository_bytes'] is not None:check(len(raw)==r['repository_bytes'],p.name+' repository byte size')
            if r['kind']=='processed_expression_matrix':
                with gzip.open(p,'rt',encoding='utf8') as f:
                    for line in f:
                        if line.startswith('!series_matrix_table_begin'):break
                    header=next(csv.reader([next(f)],delimiter='\t'))
                    members={x[0] for x in db.execute('SELECT sample_key FROM dataset_membership WHERE dataset_id=?',(r['dataset_id'],))}
                    check(set(header[1:])==members,p.name+' matrix columns match real GSMs')
                    check(len(header[1:])==len(set(header[1:])),p.name+' unique sample columns')
                    rows=0;seen=set()
                    for line in f:
                        if line.startswith('!series_matrix_table_end'):break
                        v=next(csv.reader([line],delimiter='\t'))
                        if len(v)!=len(header):raise AssertionError(p.name+' matrix width')
                        if v[0] in seen:raise AssertionError(p.name+' duplicate feature ID')
                        seen.add(v[0]);rows+=1
                        for x in v[1:]:
                            if x not in ('null','NA','NaN',''):float(x)
                    check(rows==r['feature_rows'],p.name+' complete feature rows and numeric entries')
                    matrices.append({'dataset_id':r['dataset_id'],'features':rows,'libraries':len(header)-1})
        check(db.execute("SELECT count(*) FROM sources WHERE lower(doi)='10.1186/s13062-025-00600-7'").fetchone()[0]==1,'PMC11780792 and DOI deduplicated')
        check(db.execute('SELECT count(*) FROM omics_workbook_cells').fetchone()[0]==46761,'Lossless workbook cell import')
    result={'passed':True,'check_count':len(checks),'matrices':matrices,'checks':checks}
    (ROOT/'05_reports/supplement_verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in result.items() if k!='checks'},ensure_ascii=False,indent=2))
if __name__=='__main__':verify()
