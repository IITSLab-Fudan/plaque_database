"""Build the source catalog BEFORE quantitative extraction. Python stdlib only."""
import csv, json, pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
def write_csv(path,rows,fields=None):
    path.parent.mkdir(parents=True,exist_ok=True)
    if fields is None: fields=list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='raise');w.writeheader()
        w.writerows({k:('NA' if r.get(k) is None or r.get(k)=='' else r.get(k,'NA')) for k in fields} for r in rows)
def catalog():
    specs=json.loads((ROOT/'02_extracted_data/source_decisions.json').read_text(encoding='utf-8'))
    rows=[]
    for sid,spec in specs.items():
        m=json.loads((ROOT/f'01_raw_sources/{sid}_metadata.json').read_text(encoding='utf-8'))['resultList']['result'][0]
        full=(ROOT/f'01_raw_sources/{sid}_fulltext.xml').exists()
        rows.append(dict(source_id=sid,title=m['title'],authors=m.get('authorString'),year=m.get('pubYear') or m['journalInfo']['yearOfPublication'],journal=m['journalInfo']['journal']['title'],doi=m.get('doi'),url='https://pubmed.ncbi.nlm.nih.gov/'+m['id']+'/',data_repository=spec.get('data_repository'),species=spec['species'],vascular_bed=spec['vascular_bed'],plaque_types=spec['plaque_types'],mechanical_data=spec.get('mechanical_data','no'),pH_data=spec.get('pH_data','no'),H2O2_data=spec.get('H2O2_data','no'),raw_data_available=spec.get('raw_data_available','not_located'),access_status='full_text_archived' if full else 'primary_abstract_only',notes=spec['notes'],decision=spec['decision'],cohort_group=spec.get('cohort_group',sid),source_type='journal',full_text_url='https://pmc.ncbi.nlm.nih.gov/articles/'+m['pmcid']+'/' if m.get('pmcid') else None,metadata_path=f'01_raw_sources/{sid}_metadata.json',full_text_path=f'01_raw_sources/{sid}_fulltext.xml' if full else None))
    from supplement_catalog import source_rows
    rows.extend(source_rows())
    write_csv(ROOT/'sources.csv',rows)
    write_csv(ROOT/'02_extracted_data/sources_curated.csv',rows)
    print('Source catalog:',len(rows),'studies;',sum(r['decision']=='include' for r in rows),'included')
    return rows
if __name__=='__main__':catalog()
