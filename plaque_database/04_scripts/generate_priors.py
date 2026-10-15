"""Phenotype evidence constraints, without assuming a distribution or mixing domains."""
from prepare_catalog import ROOT,write_csv
PHENOTYPES=['Normal / non-atherosclerotic vessel','Fibrous / stable plaque','Lipid-rich plaque','Vulnerable / unstable plaque','Calcified plaque','Intraplaque hemorrhage','Necrotic core','Mixed plaque']
FIELDS='''standardized_plaque_type mechanical_parameter mechanical_distribution mechanical_min mechanical_max mechanical_mean mechanical_sd pH_distribution pH_min pH_max pH_mean pH_sd h2o2_distribution h2o2_min h2o2_max h2o2_mean h2o2_sd human_evidence_count animal_evidence_count confidence_level supporting_source_ids notes mechanical_unit mechanical_median mechanical_q1 mechanical_q3 mechanical_method mechanical_stretch_ratio selected_record_ids prior_status population_scope covariance_available'''.split()
def generate(records):
    rows=[]
    for phenotype in PHENOTYPES:
        relevant=[r for r in records if r.get('standardized_plaque_type')==phenotype and r['modality'] in ('mechanical','pH','H2O2')]
        r={k:None for k in FIELDS};r.update(standardized_plaque_type=phenotype,human_evidence_count=len({x['source_id'] for x in relevant if x['species']=='human'}),animal_evidence_count=len({x['source_id'] for x in relevant if x['species']!='human'}),confidence_level='low',supporting_source_ids=';'.join(sorted({x['source_id'] for x in relevant})) or None,prior_status='insufficient_evidence',population_scope='human only in numeric fields',covariance_available=False)
        selected=[]
        # One explicitly chosen method/cohort for a readable summary. All alternatives remain in long-form evidence.
        candidates=[x for x in relevant if x['source_id']=='S014' and x['mechanical_parameter']=='SWE_Young_modulus']
        if phenotype=='Lipid-rich plaque':
            candidates=[x for x in relevant if x['source_id']=='S001' and x['stretch_ratio']==1]
        if candidates:
            x=candidates[0];selected.append(x)
            for k in ['mechanical_parameter','mechanical_mean','mechanical_sd','mechanical_median','mechanical_q1','mechanical_q3','mechanical_unit','mechanical_method']:
                r[k]=x.get(k)
            r['mechanical_stretch_ratio']=x.get('stretch_ratio')
            r['prior_status']='conditional_summary_constraints_only'
        ph=[x for x in relevant if x['source_id']=='S003' and x['species']=='human']
        if ph:
            x=ph[0];selected.append(x);r['pH_mean']=x['pH_mean'];r['prior_status']='conditional_summary_constraints_only'
        r['selected_record_ids']=';'.join(x['record_id'] for x in selected) or None
        notes={
          'Normal / non-atherosclerotic vessel':'Selected pH is umbilical-artery control only; not an adult coronary/carotid baseline. S016 plaque-free ICA/CCA mechanics from diseased donors retained separately, not pooled or paired with umbilical pH. Dispersion type unresolved.',
          'Fibrous / stable plaque':'Whole-plaque stable SWE from S014 only. Fibrous-cap tensile/indentation data are not assigned to this label. S012/S014/S016 may overlap.',
          'Lipid-rich plaque':'Mechanics is isolated lipid component at lambda=1 (median/Q1/Q3); pH is yellow region from independent S003. This row is not a paired sample or joint distribution.',
          'Vulnerable / unstable plaque':'Histology-classified whole-plaque SWE S014; not local contact modulus. S012/S014/S016 possible overlap; S013 independent abstract-only mean also retained in evidence table.',
          'Calcified plaque':'Only region-specific pH mean selected. S019 has relative cap stiffness, not an absolute modulus prior. S017/S018 remain deferred pending numerical full text.',
          'Intraplaque hemorrhage':'S001/S002 merge IPH and thrombus; no pure-IPH numerical prior assigned. Combined-component evidence is retained in component_prior_evidence.csv.',
          'Necrotic core':'Lipid is not automatically necrotic core; no verified parameter-specific evidence suitable for this phenotype in this release.',
          'Mixed plaque':'Unspecified atherosclerosis is not automatically mixed plaque; no verified type-specific numerical prior in this release.'}
        r['notes']=notes[phenotype]+' No fitted distribution, observed min/max, missing SD, or cross-modal correlation is invented. Human H2O2 remains NA.'
        rows.append(r)
    write_csv(ROOT/'plaque_type_priors.csv',rows,FIELDS)
    evidence=[x for x in records if x.get('standardized_plaque_type') and x['modality'] in ('mechanical','pH','H2O2')]
    write_csv(ROOT/'03_processed_data/plaque_prior_evidence.csv',evidence)
    components=[x for x in records if not x.get('standardized_plaque_type') and x['modality']=='mechanical']
    write_csv(ROOT/'03_processed_data/component_prior_evidence.csv',components)
    return rows
if __name__=='__main__':
    import json
    generate(json.loads((ROOT/'02_extracted_data/records_curated.json').read_text(encoding='utf-8')))
