"""Rebuild repository metadata, sample annotations and file index offline.

Omics features are kept outside the physical/chemical observation table.
"""
import csv,collections,gzip,hashlib,html,json,re
from pathlib import Path
from prepare_catalog import ROOT,write_csv
RAW=ROOT/'01_raw_sources'
GEO=['GSE28829','GSE43292','GSE163154','GSE159677','GSE253903','GSE253904','GSE210152','GSE253902']
NOTES={
'GSE28829':'13 early / 16 advanced lesions; stage is not a stable/vulnerable label. Autopsy tissue; subject pairing not supplied.',
'GSE43292':'32 paired patients / 64 samples. Macroscopically intact comparator is Stary I/II, not healthy tissue; atheroma is IV or above.',
'GSE163154':'16 non-IPH / 27 IPH lesion segments; patient IDs not supplied here. non-IPH is not equivalent to stable.',
'GSE159677':'3 patients / 6 paired AC and PA samples. AC described as calcified; adjacent PA is not an independently healthy donor.',
'GSE253903':'12 subjects / 6 symptomatic in this scRNA-seq subseries. Overall article summary 21/13 is not this subseries count.',
'GSE253902':'6 subjects / 5 symptomatic; 12 GEX/ADT libraries. GEX and ADT from one plaque are not separate patients.',
'GSE253904':'SuperSeries contains GSE253902 and GSE253903. 24 GSM libraries resolve to 18 deposited donor labels, 11 symptomatic; summary 21/13 describes the broader study. Missing 3 subjects are not fabricated.',
'GSE210152':'6 CD45+ immune-cell samples. Series update 10/6/26 identifies 4 symptomatic and 2 asymptomatic; symptom is not a histological phenotype.',
'PXD031052':'Study 120 patients, 219 specimens (110 core / 109 periphery); not number of PRM columns. Four proteomic clusters are not the eight target classes. Original workbook run IDs retained; no unverified clinical pairing.',
'PXD039077':'21 patients: 7 hard / 7 soft / 7 mixed, macroscopic classification. Repository says 575 differential proteins; final paper S023 says 714, 4498 quantified proteins. Repository >46700 is inconsistent with final paper; not treated as validated count.'}
PAPERS={
'S020':('qualitative_support','human;mouse','pHrodo/LS662 acidification imaging, Fig 1 human n=5 and mouse n=7; not calibrated absolute tissue pH. Colocalization is not a universal pH classification threshold.'),
'S021':('qualitative_support','mouse;cell','Primary abstract verifies multi-analyte probe and two-photon imaging. No calibrated plaque H2O2 concentration or individual values available in the accessed abstract; quantitative extraction deferred.'),
'S022':('auxiliary_support','human','33 cadaver plaques, 18 coronary / 15 noncoronary, ICP-OES total calcium. Abstract supplies density and correlations, not absolute calcium concentration. Noncalcified n=19 plus calcified n=13 leaves one specimen unexplained; free Ca2+ unavailable.'),
'S023':('dataset_publication','human','Primary publication for PXD039077. Final abstract reports 714 differential and 4498 quantified proteins, unlike repository description. Macroscopic hard/soft/mixed are not mechanically measured stiffness.'),
'R004':('secondary_reference','human','PMC11780792 and DOI 10.1186/s13062-025-00600-7 are the same secondary analysis; no duplicate cohort and no gene expression to ROS concentration conversion.'),
'R005':('review_reference','human;animal;cell','Review of plaque microenvironment, not new individual pH observations. Review pH ranges are not imported as human thresholds.'),
'R006':('method_reference','other','AHA scientific statement on ROS measurement, not an independent plaque concentration dataset. Only metadata/abstract archived; full-text endpoint returned HTTP 500.')}
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def soft(a):
    series=collections.defaultdict(list);samples={};current=None
    for line in (RAW/(a+'_metadata.soft')).read_text(encoding='utf-8').splitlines():
        if line.startswith('^SAMPLE = '):current=collections.defaultdict(list);samples[line.split(' = ',1)[1]]=current
        elif line.startswith('^'):current=None
        elif ' = ' in line:
            k,v=line.split(' = ',1)
            if k.startswith('!Series_'):series[k[8:]].append(v)
            elif k.startswith('!Sample_') and current is not None:current[k[8:]].append(v)
    return dict(series),samples
def join(m,k):return '; '.join(m.get(k,[])) or None
def source_rows():
    rows=[]
    for a in GEO+['PXD031052','PXD039077']:
        geo=a.startswith('GSE');p=RAW/(a+('_metadata.soft' if geo else '_metadata.json'))
        m=soft(a)[0] if geo else json.loads(p.read_text(encoding='utf8'))
        rows.append(dict(source_id=a,title=join(m,'title') if geo else m['title'],authors=None,year=(join(m,'submission_date') or '')[-4:] if geo else m['publicationDate'][:4],journal=None,doi=None,url='https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc='+a if geo else 'https://www.ebi.ac.uk/pride/archive/projects/'+a,data_repository='GEO' if geo else 'PRIDE/ProteomeXchange',species='human',vascular_bed='carotid',plaque_types=NOTES[a],mechanical_data='no',pH_data='no',H2O2_data='no',raw_data_available='repository_files_listed',access_status='repository_metadata_archived',notes=NOTES[a],decision='catalogued_omics',cohort_group='GSE253904' if a in ['GSE253902','GSE253903','GSE253904'] else a,source_type='dataset',full_text_url=None,metadata_path=str(p.relative_to(ROOT)).replace('\\','/'),full_text_path=None))
    for sid,(role,species,note) in PAPERS.items():
        m=json.loads((RAW/(sid+'_metadata.json')).read_text(encoding='utf8'))['resultList']['result'][0]
        full=RAW/(sid+'_fulltext.xml')
        rows.append(dict(source_id=sid,title=html.unescape(re.sub('<[^>]+>','',m['title'])),authors=m.get('authorString'),year=m.get('pubYear'),journal=m['journalInfo']['journal']['title'],doi=m.get('doi'),url='https://pubmed.ncbi.nlm.nih.gov/'+m['id']+'/',data_repository='PXD039077' if sid=='S023' else None,species=species,vascular_bed='carotid;coronary;other' if sid=='S022' else 'other',plaque_types=None,mechanical_data='no',pH_data='qualitative_imaging_only' if sid=='S020' else 'no',H2O2_data='probe_response_only' if sid=='S021' else 'no',raw_data_available='not_extracted',access_status='full_text_archived' if full.exists() else 'primary_abstract_only',notes=note,decision=role,cohort_group='PXD039077' if sid=='S023' else sid,source_type='journal' if sid.startswith('S') else 'reference',full_text_url='https://pmc.ncbi.nlm.nih.gov/articles/'+m['pmcid']+'/' if m.get('pmcid') else None,metadata_path='01_raw_sources/'+sid+'_metadata.json',full_text_path='01_raw_sources/'+full.name if full.exists() else None))
    return rows
def build_supplement():
    catalog=[];samples={};members=[];files=[]
    def file_row(a,url,kind,local=None,**extra):
        if not url or url=='NONE':return
        key=a+'|'+url
        if any(f['file_id']==key for f in files):return
        files.append(dict(file_id=key,dataset_id=a,url=url,kind=kind,local_path=str(local.relative_to(ROOT)).replace('\\','/') if local else None,downloaded=bool(local),sha256=digest(local) if local else None,bytes=local.stat().st_size if local else None,**extra))
    for a in GEO:
        series,ss=soft(a);labels=collections.Counter();donors=set()
        for gsm,m in ss.items():
            title=join(m,'title');chars={}
            for x in m.get('characteristics_ch1',[]):
                if ': ' in x:k,v=x.split(': ',1);chars[k.lower()]=v
            subject=chars.get('patient');label=chars.get('phenotype') or chars.get('classification') or chars.get('location') or chars.get('tissue')
            symptom=chars.get('symptom presence');mapping=None;why='Retain original label; no validated equivalence to target phenotype.'
            if a=='GSE159677':subject=re.search(r'Patient (\d+)',title)[1];mapping='Calcified plaque' if chars.get('location')=='atherosclerotic core' else None;why='Calcified AC in series design; patient-matched PA not assumed healthy.'
            if a.startswith('GSE25390'):
                subject=title.split(',')[0];label=symptom
            if a=='GSE210152':
                subject=re.search(r'\((P\d+)\)',title)[1];symptom='Symptomatic' if subject in ['P1','P2','P6','P7'] else 'Asymptomatic';label='CD45+ intraplaque immune cells'
            if a=='GSE163154' and label=='IPH':mapping='Intraplaque hemorrhage';why='Explicit IPH classification; does not imply isolated pure hemorrhage tissue.'
            if subject:donors.add(subject)
            labels[label]+=1
            row=dict(sample_key=gsm,repository_sample_id=gsm,species='human',title=title,original_label=label,standardized_plaque_type=mapping,mapping_rationale=why,subject_id=subject,cohort_group='GSE253904' if a.startswith('GSE25390') else a,symptom_status=symptom,library_type=chars.get('library type') or join(m,'library_strategy'),source_tissue=join(m,'source_name_ch1'),characteristics_json=json.dumps(chars,ensure_ascii=False,sort_keys=True),target_multimodal_eligible=False,evidence_file='01_raw_sources/'+a+'_metadata.soft',source_location='^SAMPLE = '+gsm)
            if gsm in samples:
                assert all(samples[gsm].get(k)==row.get(k) for k in ['title','original_label','subject_id','symptom_status']),gsm
            else:samples[gsm]=row
            members.append(dict(membership_id=a+':'+gsm,dataset_id=a,sample_key=gsm))
            for k,vs in m.items():
                if k.startswith('supplementary_file'):
                    for url in vs:file_row(a,url,'sample_supplement')
        for url in series.get('supplementary_file',[]):file_row(a,url,'series_supplement')
        matrix=RAW/(a+'_series_matrix.txt.gz');features=None
        if matrix.exists():
            with gzip.open(matrix,'rt',encoding='utf8') as f:
                active=False;features=0
                for line in f:
                    if line.startswith('!series_matrix_table_begin'):active=True;next(f);continue
                    if line.startswith('!series_matrix_table_end'):break
                    if active:features+=1
            meta=json.loads(matrix.with_name(matrix.name+'.meta.json').read_text());file_row(a,meta['url'],'processed_expression_matrix',matrix,feature_rows=features,sample_columns=len(ss))
        catalog.append(dict(dataset_id=a,source_id=a,repository='GEO',title=join(series,'title'),species='human',vascular_bed='carotid',assay=join(series,'type'),parent_dataset='GSE253904' if a in ['GSE253902','GSE253903'] else None,cohort_group='GSE253904' if a.startswith('GSE25390') else a,repository_sample_count=len(ss),identifiable_donor_count=len(donors) or None,study_n_subjects=21 if a.startswith('GSE25390') else len(donors) or None,study_n_samples=None,original_groups=json.dumps(dict(labels),ensure_ascii=False),clinical_label_available=any(samples[g]['original_label'] for g in ss),mechanical_available=False,pH_available=False,H2O2_available=False,processed_data_local=matrix.exists(),local_data_scope='processed matrix + metadata' if matrix.exists() else 'metadata only; expression files indexed remotely',notes=NOTES[a],evidence_file='01_raw_sources/'+a+'_metadata.soft'))
    for a in ['PXD031052','PXD039077']:
        m=json.loads((RAW/(a+'_metadata.json')).read_text(encoding='utf8'))
        fs=json.loads((RAW/(a+'_files.json')).read_text())
        if a=='PXD031052':fs+=json.loads((RAW/(a+'_files_page1.json')).read_text())
        for f in fs:
            url=next((x['value'] for x in f['publicFileLocations'] if x['name']=='FTP Protocol'),None)
            local=RAW/(a+'_'+f['fileName'])
            file_row(a,url,f['fileCategory']['value'],local if local.exists() else None,repository_bytes=f['fileSizeBytes'],repository_sha1=f.get('checksum'))
        if a=='PXD039077':
            p=RAW/'PXD039077_Sample_list.tsv'
            for r in csv.DictReader(p.open(encoding='utf8'),delimiter='\t'):
                key=a+':'+r['sample'];lab=r['morphology']
                samples[key]=dict(sample_key=key,repository_sample_id=r['sample'],species='human',title=r['sample'],original_label=lab,standardized_plaque_type={'Hard':'Fibrous / stable plaque','Soft':'Vulnerable / unstable plaque','Mixed':'Mixed plaque'}[lab],mapping_rationale='Author macroscopic classification; provisional phenotype mapping, not measured stiffness or universal histology.',subject_id=None,cohort_group=a,symptom_status='Symptomatic',library_type='DIA-PASEF',source_tissue='carotid plaque',characteristics_json=json.dumps(r,sort_keys=True),target_multimodal_eligible=False,evidence_file='01_raw_sources/'+p.name,source_location='Record ID '+r['Record ID'])
                members.append(dict(membership_id=key,dataset_id=a,sample_key=key))
        catalog.append(dict(dataset_id=a,source_id=a,repository='PRIDE/ProteomeXchange',title=m['title'],species='human',vascular_bed='carotid',assay='mass spectrometry proteomics',parent_dataset=None,cohort_group=a,repository_sample_count=21 if a=='PXD039077' else None,identifiable_donor_count=None,study_n_subjects=120 if a=='PXD031052' else 21,study_n_samples=219 if a=='PXD031052' else 21,original_groups='110 core;109 periphery;4 proteomic phenotypes' if a=='PXD031052' else '7 Hard;7 Soft;7 Mixed',clinical_label_available=True,mechanical_available=False,pH_available=False,H2O2_available=False,processed_data_local=a=='PXD031052',local_data_scope='PRM result workbook + peptide annotation workbook' if a=='PXD031052' else '21 sample annotations; proteomic intensities remote',notes=NOTES[a],evidence_file='01_raw_sources/'+a+'_metadata.json'))
    audit=[]
    for sid in ['S003','S011']+list(PAPERS)+GEO+['PXD031052','PXD039077']:
        audit.append(dict(audit_id=sid,source_id=sid,previous_status='already_in_sources_and_observations' if sid in ['S003','S011'] else 'not_in_v1_source_catalog',action='retained_no_duplicate' if sid in ['S003','S011'] else 'added_related_resource' if sid in ['GSE253902','S023'] else 'added',destination='observations' if sid in ['S003','S011'] else 'dataset_catalog;dataset_samples;dataset_files' if sid.startswith(('GSE','PXD')) else 'sources',notes=NOTES.get(sid) or PAPERS.get(sid,('','','Existing verified measurements retained.'))[2]))
    catalog.sort(key=lambda r: bool(r.get('parent_dataset')))
    for r in catalog:
        r['metadata_sha256']=digest(ROOT/r['evidence_file'])
        r['license']='Creative Commons Public Domain (CC0)' if r['dataset_id'].startswith('PXD') else 'GEO public access; source-specific terms not separately verified'
        r['retrieved_utc']=json.loads((ROOT/r['evidence_file']).with_name(Path(r['evidence_file']).name+'.meta.json').read_text())['retrieved_utc']
    tables={'dataset_catalog':catalog,'dataset_samples':list(samples.values()),'dataset_membership':members,'dataset_files':files,'supplement_audit':audit}
    for name,rows in tables.items():write_csv(ROOT/(name+'.csv'),rows)
    # Compact importable, lossless workbook cell table; cells are not biological samples.
    from read_workbooks import sheets
    cells=[]
    for p in sorted(RAW.glob('PXD*.xlsx')):
        for sheet,values in sheets(p):
            for address,value in values.items():cells.append(dict(cell_id=p.name+'|'+sheet+'|'+address,dataset_id='PXD031052',evidence_file='01_raw_sources/'+p.name,sheet=sheet,cell=address,raw_value=value))
    tables['omics_workbook_cells']=cells
    write_csv(ROOT/'03_processed_data/omics_workbook_cells.csv',cells)
    return tables
