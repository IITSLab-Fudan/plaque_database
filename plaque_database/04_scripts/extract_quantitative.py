"""Deterministic, source-specific extraction. No synthetic samples or imputations."""
import csv, json, re, pathlib, xml.etree.ElementTree as ET
from prepare_catalog import ROOT, write_csv
from read_workbooks import sheets
FIB='Fibrous / stable plaque'
LIP='Lipid-rich plaque'
VUL='Vulnerable / unstable plaque'
CAL='Calcified plaque'
NOR='Normal / non-atherosclerotic vessel'
REQUIRED='''record_id source_id source_type title authors year journal doi url dataset_url species vascular_bed sample_type n_subjects n_samples original_plaque_type standardized_plaque_type histology_validation mechanical_parameter mechanical_value mechanical_unit mechanical_mean mechanical_sd mechanical_median mechanical_iqr stress strain measurement_frequency mechanical_method pH_value pH_mean pH_sd pH_range_min pH_range_max pH_method pH_location h2o2_value h2o2_unit h2o2_mean h2o2_sd h2o2_range_min h2o2_range_max h2o2_method measurement_basis ros_other_type ros_other_value ros_other_unit temperature experimental_condition sample_location data_level raw_data_available raw_data_format extraction_method confidence_level notes source_location source_quote original_value original_unit normalized_value normalized_unit'''.split()
EXTRA='''modality record_kind subject_id sample_id specimen_group_id cohort_group n_subjects_study n_observations sample_count_basis label_scope tissue_component mapping_rationale histology_scope mechanical_min mechanical_max mechanical_q1 mechanical_q3 mechanical_iqr_width stretch_ratio statistic_type reported_dispersion dispersion_type measurement_error measurement_error_unit temperature_unit measurement_frequency_unit loading_direction loading_rate_mm_s stress_definition strain_definition uncertainty_notes same_sample_linkage ml_eligible intended_use access_tier raw_data_obtained evidence_file evidence_sha256 original_secondary_value original_secondary_unit h2o2_location collection_timepoint intervention species_domain synthetic_value'''.split()
FIELDS=REQUIRED+EXTRA
def tree(s): return ET.parse(ROOT/f'01_raw_sources/{s}_fulltext.xml')
def txt(e): return ' '.join(''.join(e.itertext()).split())
def table(s,label):
    return next(t for t in tree(s).iter('table-wrap') if txt(t.find('label')).lower().replace('.','')==label.lower())
def metadata(s):return json.loads((ROOT/f'01_raw_sources/{s}_metadata.json').read_text(encoding='utf-8'))['resultList']['result'][0]
def numeric_triplet(v):
    return [float(x) for x in re.findall(r'\d+(?:\.\d+)?',v)]
def extract():
    sources={r['source_id']:r for r in csv.DictReader((ROOT/'sources.csv').open(encoding='utf-8-sig'))}
    records=[]
    def add(s,modality,original,standard=None,**kw):
        src=sources[s]
        r={k:None for k in FIELDS}
        for k in ['source_id','source_type','title','authors','year','journal','doi','url','species','vascular_bed','cohort_group']:
            r[k]=src.get(k)
        r.update(record_id=f'{s}-R{1+sum(a["source_id"]==s for a in records):03d}',dataset_url=src['data_repository'],modality=modality,original_plaque_type=original,standardized_plaque_type=standard,record_kind='group_summary',sample_type='ex_vivo',data_level='D',raw_data_available='not_located',raw_data_obtained=False,extraction_method='text_extracted',confidence_level='medium',same_sample_linkage='not_available',ml_eligible=False,intended_use='prior_only',label_scope='component',access_tier=src['access_status'],evidence_file=src['full_text_path'] if src['access_status']=='full_text_archived' else src['metadata_path'],temperature_unit='degC',species_domain='human',notes='No joining across records as a real multimodal sample.')
        r.update(kw)
        if r['species'] not in ('human',None) or r['sample_type']=='cell':
            r.update(data_level='E',intended_use='simulation_only',species_domain='cell' if r['sample_type']=='cell' else 'animal')
        # NA strings at extraction boundaries become missing in canonical JSON.
        r={k:(None if v=='NA' else v) for k,v in r.items()}
        records.append(r)
        return r
    # S001: 4 tissues x 4 stretch levels, table cells, not synthetic stress-strain points.
    t=table('S001','Table 2')
    counts={'Media':(17,65),'Fibrous cap':(14,59),'Lipid':(11,38),'IPH/T':(11,21)}
    for row in t.findall('.//tbody/tr'):
        cs=[txt(c) for c in row if c.tag in ('td','th')]
        if not cs or cs[0] not in counts: continue
        name=cs[0]
        for lam,cell in zip([1,1.05,1.1,1.15],cs[1:]):
            corrected=cell.replace('533.4.4','533.4').replace('176.9.0','176.9')
            med,q1,q3=numeric_triplet(corrected)
            correction=cell!=corrected
            # An explicit check against the primary abstract prevents unsupported correction.
            if correction: assert str(med) in metadata('S001')['abstractText']
            add('S001','mechanical',name,LIP if name=='Lipid' else None,n_subjects=counts[name][0],n_samples=counts[name][1],n_subjects_study=21,sample_count_basis='subjects supplying component; tissue strips; repeated conditions',specimen_group_id='S001_'+name,mechanical_parameter='incremental_Young_modulus_dCauchy_stress_dlambda',mechanical_unit='kPa',mechanical_median=med,mechanical_q1=q1,mechanical_q3=q3,mechanical_iqr=f'[{q1}, {q3}]',stretch_ratio=lam,statistic_type='median_Q1_Q3',mechanical_method='circumferential_uniaxial_extension',loading_direction='circumferential',loading_rate_mm_s=0.01,temperature=37,experimental_condition='cryopreserved <4 months; 10% DMSO; 37 C saline; 0.005 N preload; five preconditioning cycles',histology_validation='no',histology_scope='visual dissection; no per-strip histological confirmation',tissue_component=name,mapping_rationale='Lipid component only; fibrous cap is not whole-plaque stable; media from diseased artery is not healthy; IPH/T unresolved mixture',extraction_method='original_table',confidence_level='medium' if correction else 'high',original_value=cell,original_unit='kPa',source_location=f'Table 2; row {name}; lambda={lam}'+('; abstract corroborates numeric typo correction' if correction else ''),uncertainty_notes='Table typo corrected using abstract; original cell preserved.' if correction else None)
    # S002: exact Table 2, two endpoints per component, still one modality.
    counts={'Fibrous cap (FC)':(12,32),'Media':(15,35),'Lipid':(9,26),'Intraplaque hemorrhage/thrombus (IPH/T)':(7,12)}
    for row in table('S002','Table 2').findall('.//tbody/tr'):
        cs=[txt(c) for c in row if c.tag in ('td','th')]
        if not cs or cs[0] not in counts: continue
        name=cs[0]
        for param,unit,cell in zip(['ultimate_Cauchy_tensile_stress','failure_stretch_ratio'],['kPa','dimensionless'],cs[1:]):
            med,q1,q3=numeric_triplet(cell)
            add('S002','mechanical',name,LIP if name=='Lipid' else None,mechanical_parameter=param,mechanical_unit=unit,mechanical_median=med,mechanical_q1=q1,mechanical_q3=q3,mechanical_iqr=f'[{q1}, {q3}]',statistic_type='median_Q1_Q3',n_subjects=counts[name][0],n_samples=counts[name][1],n_subjects_study=21,sample_count_basis='component-contributing subjects; qualified tissue strips',specimen_group_id='S002_'+name,histology_validation='yes',histology_scope='adjacent rings; possible component misclassification',mechanical_method='circumferential_uniaxial_extension_to_failure',loading_direction='circumferential',loading_rate_mm_s=0.01,temperature=37,tissue_component=name,experimental_condition='cryopreserved; 10% DMSO; saline; failure >=about 2 mm from clamp; sliding strips excluded',source_location=f'Table 2; row {name}; {param}',extraction_method='original_table',original_value=cell,original_unit=unit,confidence_level='high',mapping_rationale='Component classification only; combined IPH/T is not pure IPH.',strain_definition='lambda = final length / initial length; not engineering strain' if unit=='dimensionless' else None)
    for label,med,q1,q3,n in [('weaker fibrous cap group',69.7,52.2,80.2,15),('stronger fibrous cap group',259.3,220.4,414.0,17)]:
        add('S002','mechanical',label,mechanical_parameter='ultimate_Cauchy_tensile_stress',mechanical_unit='kPa',mechanical_median=med,mechanical_q1=q1,mechanical_q3=q3,mechanical_iqr=f'[{q1}, {q3}]',statistic_type='median_Q1_Q3',n_samples=n,n_subjects_study=21,source_location='Results; paragraph accompanying Figure 5',original_value=f'{med} [{q1}, {q3}]',original_unit='kPa',mechanical_method='circumferential_uniaxial_extension_to_failure',temperature=37,tissue_component='fibrous cap',histology_validation='yes',histology_scope='adjacent sections',confidence_level='high',specimen_group_id='S002_FC_subgroups',notes='Post-hoc strength groups; subset of Table 2 FC; do not double-count or relabel as stable/vulnerable.')
    # S003 primary abstract: keep unknown error-bar semantics and participant denominator.
    for name,std,sp,bed,mean,disp,nsub,npts in [('CEA overall',None,'human','carotid',7.55,.32,None,415),('yellow (lipid-rich) areas',LIP,'human','carotid',7.15,.01,None,None),('calcified areas',CAL,'human','carotid',7.73,.01,None,None),('human umbilical arteries (controls)',NOR,'human','other',7.24,.1,11,233),('WHHL rabbit aortas',None,'rabbit','aorta',7.40,.43,9,275)]:
        add('S003','pH',name,std,species=sp,vascular_bed=bed,n_subjects=nsub,n_subjects_study=48 if bed=='carotid' else nsub,n_observations=npts,pH_mean=mean,reported_dispersion=disp,dispersion_type='unspecified_plus_minus',statistic_type='mean_plus_minus_unspecified',pH_method='glass_microelectrode',pH_location=name,temperature=37,measurement_basis='local tissue pH; extracellular specificity not fully verified',source_location='Primary abstract, Methods and results',original_value=f'{mean} +/- {disp}',original_unit='pH',experimental_condition='ex vivo viable tissue; incubator 37 C; fluorescent pH probes corroborate heterogeneity',label_scope='region' if bed=='carotid' else 'vessel',sample_location='umbilical artery' if name.startswith('human umbilical') else name,uncertainty_notes='Do not reinterpret unspecified ± as SD/SEM or range. 48 is total human CEA study cohort, not verified region-specific n. Umbilical controls are not matched adult carotid controls.')
    add('S004','mechanical','pooled carotid plaque indentation locations',mechanical_parameter='compressive_Young_modulus_inverse_FE',mechanical_median=30,mechanical_min=6,mechanical_max=891,mechanical_unit='kPa',statistic_type='median_range',mechanical_method='axial_indentation_inverse_FE_isotropic_neo_Hookean',source_location='Primary abstract, Results',original_value='median 30; range 6-891',original_unit='kPa',mapping_rationale='Pooled anatomical locations; no whole-plaque phenotype inferred.')
    add('S005','mechanical','pooled fibrous cap/shoulder/remaining intima',mechanical_parameter='constitutive_fibre_stiffness',mechanical_median=80.6,mechanical_q1=17.7,mechanical_q3=157,mechanical_iqr='[17.7, 157.0]',mechanical_unit='kPa',statistic_type='median_Q1_Q3',mechanical_method='microindentation_inverse_anisotropic_FE',source_location='Primary abstract, Results',original_value='80.6 [17.7, 157.0]',original_unit='kPa',notes='Constitutive fibre stiffness, not Young modulus. Locations pooled; no stable plaque label inferred.')
    add('S010','mechanical','fibrous cap',mechanical_parameter='neo_Hookean_shear_modulus',mechanical_median=11,mechanical_min=7,mechanical_max=100,mechanical_unit='kPa',statistic_type='median_range',n_samples=8,mechanical_method='indentation_inverse_FE_neo_Hookean',source_location='Primary abstract',original_value='median 11; range 7-100',original_unit='kPa',tissue_component='fibrous cap',notes='8 usable specimens from 11; 3 highly calcified specimens discarded. Subject count not inferred from specimen count.')
    # S006 imaging response and model-derived modulus are marked distinctly.
    for region,std,velocity,vd,disp,dd in [('lipid-rich plaque',LIP,.38,.19,3.7,1.2),('remaining arterial wall',None,3.45,.45,1.0,.2)]:
        for parameter,val,err,unit in [('shear_wave_velocity',velocity,vd,'m/s'),('ARF_peak_displacement',disp,dd,'um')]:
            add('S006','mechanical',region,std,species='rabbit',vascular_bed='aorta',n_subjects=1,n_subjects_study=1,sample_count_basis='one rabbit; regional imaging summary; pixel count not reported',mechanical_parameter=parameter,mechanical_mean=val,mechanical_unit=unit,reported_dispersion=err,dispersion_type='unspecified_plus_minus',statistic_type='mean_plus_minus_unspecified',mechanical_method='ARF_IVUS_elastography',source_location='Results, paragraph accompanying Figure 9',original_value=f'{val} +/- {err}',original_unit=unit,raw_data_available='true',raw_data_format='xlsx;mat.zip (listed, not downloaded)',label_scope='region',experimental_condition='male New Zealand White; 1.5% cholesterol diet; FeCl3 injury; sacrifice after 8 weeks; 8.5 MHz push, 31 MHz imaging',confidence_level='high',notes='Ultrasound excitation frequencies are not mechanical measurement frequency. No conversion to modulus applied.')
    add('S006','mechanical','lipid-rich plaque',LIP,species='rabbit',vascular_bed='aorta',n_subjects=1,mechanical_parameter='shear_modulus_author_inferred_wave_model',mechanical_value=.06,mechanical_unit='kPa',statistic_type='author_model_estimate',mechanical_method='ARF_IVUS_wave_model_equation_4_3',measurement_frequency=330,measurement_frequency_unit='Hz',source_location='Discussion; paragraph using equation (4.3)',original_value=.06,original_unit='kPa',label_scope='region',notes='Author-calculated from 0.38 m/s, 330 Hz, 1 mm thickness; not an independent direct material test.',raw_data_available='true',confidence_level='medium')
    # Whole plaque stable/vulnerable SWE. Mean±2SD is not stored as mean±SD.
    for s,stats in [('S012',[('Vulnerable',VUL,24.6,4.3,33),('Stable',FIB,49.6,8.1,30)]),('S014',[('STABLE',FIB,46.211,45.384,42),('VULN',VUL,25.653,27.237,36)])]:
        ttext=txt(table(s,'Table 2'))
        for orig,std,mean,err,n in stats:
            assert str(mean) in ttext and str(err) in ttext
            add(s,'mechanical',orig,std,sample_type='in_vivo',mechanical_parameter='SWE_Young_modulus',mechanical_mean=mean,mechanical_sd=err if s=='S014' else None,mechanical_unit='kPa',reported_dispersion=err,dispersion_type='SD' if s=='S014' else '2SD_as_reported',statistic_type='mean_SD' if s=='S014' else 'mean_2SD_as_reported',n_subjects=n,n_samples=n,n_subjects_study=78 if s=='S014' else 63,sample_count_basis='patients and plaques per group',histology_validation='yes',histology_scope='post-CEA histology used for group classification',label_scope='whole_plaque',mechanical_method='preoperative_point_shear_wave_elastography',source_location=f'Table 2; Young modulus row; {orig}',original_value=f'{mean} +/- {err}',original_unit='kPa',extraction_method='original_table',confidence_level='high' if s=='S014' else 'medium',raw_data_available='request_required' if s=='S014' else 'not_located',notes='Possible cohort overlap S012/S014/S016; no pooled independent-subject estimate. SWE is not contact indentation modulus.')
    for name,std,val in [('unstable',VUL,50),('stable',FIB,79.1)]:
        add('S013','mechanical',name,std,sample_type='in_vivo',mechanical_parameter='SWE_Young_modulus',mechanical_mean=val,mechanical_unit='kPa',statistic_type='mean_only',n_subjects_study=25,histology_validation='yes',histology_scope='post-CEA histology',label_scope='whole_plaque',mechanical_method='shear_wave_elastography',source_location='Primary abstract, Results',original_value=val,original_unit='kPa',notes='Subgroup n and dispersion not present in accessible abstract. No SD inferred.')
    ttext=txt(table('S016','TABLE 4'))
    for orig,std,n,vals in [('Vulnerable',VUL,43,[(12.4,34.5),(6.5,29.9),(11.9,38.4)]),('Stable',FIB,57,[(34.7,82.15),(6,39.9),(5.8,42.25)])]:
        for loc,(med,iqrw) in zip(['plaque','ICA','CCA'],vals):
            add('S016','mechanical',orig+'; '+loc,std if loc=='plaque' else None,sample_type='in_vivo',mechanical_parameter='SWE_Young_modulus',mechanical_median=med,mechanical_iqr_width=iqrw,mechanical_iqr=str(iqrw),mechanical_unit='kPa',statistic_type='median_IQR_width',n_subjects=n,n_samples=n,n_subjects_study=100,label_scope='whole_plaque' if loc=='plaque' else 'vessel_region',histology_validation='yes',histology_scope='histology subset 89/100; group membership not per-record linked',mechanical_method='preoperative_point_shear_wave_elastography',source_location=f'Table 4; YM_{loc} row; {orig}',original_value=f'{med} ({iqrw})',original_unit='kPa',extraction_method='original_table',confidence_level='high',raw_data_available='request_required',sample_location=loc,notes='IQR reported as width, not Q1/Q3. Adjacent ICA/CCA measurements not relabeled normal. Possible cohort overlap S012/S014/S016.')
    for orig,std,lo,hi,n in [('hypocellular fibrous caps',None,1,2,9),('calcified fibrous caps',CAL,4,5,11)]:
        add('S019','mechanical',orig,std,vascular_bed='aorta',mechanical_parameter='relative_dynamic_stiffness_vs_cellular_caps',mechanical_min=lo,mechanical_max=hi,mechanical_unit='fold',statistic_type='reported_ratio_range',n_samples=n,n_subjects_study=14,mechanical_method='dynamic_stress_strain_testing',histology_validation='yes',histology_scope='caps classified by histology',original_value=f'{lo}-{hi}',original_unit='fold',source_location='Primary abstract, Methods and results',experimental_condition='27 caps from 14 autopsies; cellular reference n=7; frequency sweep 0.05-10 Hz',notes='Relative stiffness only; no absolute modulus or reference-independent prior. Both endpoints are author-reported ratios, not individual sample extrema.')
    # One tissue-assay summary: two reported representations stay in ONE record.
    add('S011','H2O2','ApoE-/- atherosclerotic plaque tissue',species='mouse',vascular_bed='other',sample_type='tissue',h2o2_mean=.34,h2o2_sd=.05,h2o2_unit='mM',n_samples=6,sample_count_basis='six individual plaque samples; animal IDs not supplied for this assay',statistic_type='mean_SD',h2o2_method='Solarbio_BC3595_colorimetric_assay_415nm_standard_curve',measurement_basis='tissue content',h2o2_location='isolated plaque homogenate supernatant; exact vascular segment unspecified',original_value='0.34 +/- 0.05',original_unit='mM',original_secondary_value=.34,original_secondary_unit='umol/g wet tissue (approximate author-reported)',source_location='Methods > In vitro ROS-responsive drug release; paragraph beginning The H2O2 levels in plaque tissues',label_scope='plaque_unspecified',raw_data_available='false',raw_data_format='summary in XML; no six raw H2O2 values located in supplied XLSX',confidence_level='medium',experimental_condition='freshly isolated plaque homogenized on ice; supernatant after centrifugation; assay calibrated with H2O2 standards',notes='Not extracellular concentration. Authors report both mM and approximately umol/g wet tissue; missing extraction-volume/mass reconciliation prevents endorsing equivalence. No mapping to vulnerable/macrophage-rich human plaque. No chemical-modality pairing with separate ROS sheets.')
    # Actual author-provided ROS observations, retained separately from H2O2.
    ws=dict(sheets(ROOT/'01_raw_sources/S011_source_data.xlsx'))
    for row in range(3,7):
        seg=ws['Fig. 5i'][f'A{row}']
        for col in ['N','O','P']:
            cell=f'{col}{row}'; value=float(ws['Fig. 5i'][cell])
            add('S011','ros_other','aortic segment '+seg,NOR if seg=='A' else None,species='mouse',vascular_bed='aorta',sample_type='tissue',record_kind='raw_observation',ros_other_type='DHE_ROS_fluorescence_non_specific',ros_other_value=value,ros_other_unit='relative normalized signal',measurement_basis='tissue fluorescence',statistic_type='raw_observation',label_scope='region',source_location=f'Source Data XLSX; sheet Fig. 5i; cell {cell}; group A{row}={seg}',evidence_file='01_raw_sources/S011_source_data.xlsx',original_value=ws['Fig. 5i'][cell],original_unit='relative normalized signal',extraction_method='supplementary',raw_data_available='true',raw_data_obtained=True,raw_data_format='xlsx',confidence_level='high',n_observations=1,histology_validation='yes',histology_scope='regional H&E/ORO, Fig 5',notes='Column-level replicate has no animal ID; no assumed pairing across columns, modalities or sheets. DHE signal is not chemically specific H2O2; normalized ROS values not concentrations. Segment A has no visible plaque; B-D are severity regions, not temporal progression.')
    # Supplementary raw treatment response, six observations per group.
    def colname(n):
        s=''
        while n: n,r=divmod(n-1,26);s=chr(65+r)+s
        return s
    c=ws['Fig. 8g']
    for start in [2,8,14,20,26,32]:
        group=c[colname(start)+'2']
        for i in range(start,start+6):
            cell=colname(i)+'3'
            add('S011','ros_other','ApoE-/- AS plaque; '+group,species='mouse',vascular_bed='aorta',sample_type='tissue',record_kind='raw_observation',ros_other_type='DHE_ROS_fluorescence_non_specific',ros_other_value=float(c[cell]),ros_other_unit='arbitrary units',measurement_basis='tissue fluorescence',statistic_type='raw_observation',label_scope='plaque_unspecified',source_location=f'Source Data XLSX; sheet Fig. 8g; cell {cell}; group {group}',evidence_file='01_raw_sources/S011_source_data.xlsx',original_value=c[cell],original_unit='arbitrary units',extraction_method='supplementary',raw_data_available='true',raw_data_obtained=True,raw_data_format='xlsx',confidence_level='high',n_observations=1,intervention=group,notes='DHE mean fluorescence intensity; not H2O2 or calibrated superoxide. Six mice per group per caption; individual mouse IDs and across-assay pairing unavailable. Drug-treatment response not untreated phenotype prior.')
    # Final provenance refinements after reading the full classification protocols.
    for r in records:
        if r['source_id']=='S003' and r['original_plaque_type'] in ('human umbilical arteries (controls)','WHHL rabbit aortas'):
            r['n_samples']=11 if r['species']=='human' else 9
            r['n_subjects']=None
            r['n_subjects_study']=None
            r['sample_count_basis']='11 HUA specimens or 9 rabbit aortas explicitly reported; independent donor/animal count not separately confirmed'
        if r['source_id']=='S014':
            r['n_subjects_study']=100
            r['sample_count_basis']='100 enrolled; 78 analyzed; group sizes 42 stable and 36 vulnerable'
            r['histology_scope']='postoperative vulnerability features specified in Methods 2.1; no per-patient histology table supplied'
        if r['source_id']=='S016':
            r['histology_scope']='surgeon macroscopic class defines groups; histological confirmation assessed in 89/100'
            r['notes']+=' Group labels originate in surgeon macroscopic assessment, with histology as validation.'
            if r['sample_location'] in ('ICA','CCA'):
                r['standardized_plaque_type']=NOR
                r['original_plaque_type']='plaque-free '+r['sample_location']+' region; donor '+r['original_plaque_type']
                r['mapping_rationale']='Results explicitly calls ICA/CCA measurement regions without plaques; donors have carotid atherosclerosis.'
                r['notes']=r['notes'].replace('Adjacent ICA/CCA measurements not relabeled normal.','Plaque-free local region, not a healthy donor.')
    import hashlib
    for r in records:
        p=ROOT/r['evidence_file'];r['evidence_sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
    (ROOT/'02_extracted_data/records_curated.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    write_csv(ROOT/'02_extracted_data/records_curated.csv',records,FIELDS)
    print('Extracted',len(records),'records')
    return records
if __name__=='__main__':extract()
