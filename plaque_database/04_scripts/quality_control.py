"""Scientific integrity and referential checks; failures stop the build."""
import hashlib,collections,math
from prepare_catalog import ROOT
def validate(records,sources,priors):
    failures=[]; checks=[]
    def check(ok,msg):
        checks.append({'check':msg,'pass':bool(ok)})
        if not ok:failures.append(msg)
    ids={s['source_id'] for s in sources}
    check(len(records)==len({r['record_id'] for r in records}),'Unique record_id')
    check(all(r['source_id'] in ids for r in records),'Every observation has a valid source_id')
    for r in records:
        rid=r['record_id']
        check(bool(r['source_location'] and r['doi'] and r['evidence_file']),rid+' traceable locator')
        p=ROOT/r['evidence_file']
        check(p.exists() and hashlib.sha256(p.read_bytes()).hexdigest()==r['evidence_sha256'],rid+' evidence SHA-256')
        check(r['synthetic_value'] is None,rid+' no synthetic values')
        check(r['species'] in ('human','mouse','rabbit','pig','other'),rid+' species resolved')
        check(r['data_level']=='E' if r['species']!='human' or r['sample_type']=='cell' else r['data_level'] in ('A','B','C','D'),rid+' species/level separation')
        if r['record_kind']=='group_summary':
            check(r['sample_id'] is None and r['subject_id'] is None,rid+' no fake sample ID for summary')
            check(r['data_level'] not in ('A','B','C'),rid+' aggregate is not sample-level data')
        # Only exact chemical analyte gets an H2O2 field.
        hkeys=['h2o2_value','h2o2_mean','h2o2_sd','h2o2_range_min','h2o2_range_max']
        check(not any(r[k] is not None for k in hkeys) or r['modality']=='H2O2',rid+' H2O2 analyte specificity')
        if r['modality']=='H2O2':
            check(bool(r['h2o2_method'] and r['measurement_basis'] and r['h2o2_unit']),rid+' H2O2 assay basis')
            check(r.get('normalized_value') is None,rid+' no tissue/concentration conversion')
        if r.get('dispersion_type') in ('unspecified_plus_minus','2SD_as_reported'):
            check(r.get('mechanical_sd') is None and r.get('pH_sd') is None,rid+' ambiguous error not SD')
        if r['mechanical_q1'] is not None:
            check(r['mechanical_q1']<=r['mechanical_median']<=r['mechanical_q3'],rid+' ordered quartiles')
        if r['mechanical_min'] is not None:
            check(r['mechanical_min']<=r['mechanical_max'],rid+' ordered bounds')
        if r['data_level'] in ('A','B'):
            present=sum(any(r.get(k) is not None for k in ks) for ks in [('mechanical_value','mechanical_mean','mechanical_median'),('pH_value','pH_mean'),('h2o2_value','h2o2_mean')])
            check(bool(r['sample_id']) and r['same_sample_linkage']=='verified' and present>=({'A':3,'B':2}[r['data_level']]),rid+' real multimodal linkage')
        else:check(r['ml_eligible'] is False,rid+' training eligibility blocked for C/D/E')
    check(len(priors)==8 and len({r['standardized_plaque_type'] for r in priors})==8,'Eight requested phenotype prior rows')
    check(all(r['h2o2_mean'] is None for r in priors),'No animal H2O2 in human priors')
    check(all(r['mechanical_distribution'] is None and r['pH_distribution'] is None and r['h2o2_distribution'] is None for r in priors),'No unsupported fitted distributions')
    check(all(r['mechanical_min'] is None and r['mechanical_max'] is None for r in priors),'Quartiles not misrepresented as population extrema')
    for r in priors:
        chosen=[x for x in records if x['record_id'] in (r['selected_record_ids'] or '').split(';')]
        check(all(x['species']=='human' for x in chosen),'Human-only selected prior '+r['standardized_plaque_type'])
    # Manifest detects external modifications to downloaded original files too.
    for meta in (ROOT/'01_raw_sources').glob('*.meta.json'):
        import json
        m=json.loads(meta.read_text(encoding='utf-8'));p=meta.with_name(meta.name.removesuffix('.meta.json'))
        check(hashlib.sha256(p.read_bytes()).hexdigest()==m['sha256'],'Archive integrity '+p.name)
    return {'passed':not failures,'check_count':len(checks),'failed_checks':failures,'checks':checks,'counts':{'records':len(records),'modalities':dict(collections.Counter(r['modality'] for r in records)),'levels':dict(collections.Counter(r['data_level'] for r in records)),'record_kinds':dict(collections.Counter(r['record_kind'] for r in records)),'quantitative_sources':len({r['source_id'] for r in records})}}
if __name__=='__main__':
    import json,csv
    from generate_priors import generate
    rows=json.loads((ROOT/'02_extracted_data/records_curated.json').read_text(encoding='utf-8'))
    sources=list(csv.DictReader((ROOT/'sources.csv').open(encoding='utf-8-sig')))
    result=validate(rows,sources,generate(rows));print(json.dumps({k:v for k,v in result.items() if k!='checks'},indent=2))
    raise SystemExit(0 if result['passed'] else 1)
