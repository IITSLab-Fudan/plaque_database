"""Only exact dimensional scaling; no tissue-content/concentration conversion."""
def normalize(record):
    r=dict(record)
    if r['modality']=='mechanical':
        key=next((k for k in ('mechanical_value','mechanical_mean','mechanical_median') if r.get(k) is not None),None)
        # Canonical mechanical pressure unit kPa; do not convert wave speed, fold or displacement to modulus.
        if key and r.get('mechanical_unit') in {'Pa','kPa','MPa','GPa'}:
            r['normalized_value']=r[key]*{'Pa':.001,'kPa':1,'MPa':1000,'GPa':1000000}[r['mechanical_unit']]
            r['normalized_unit']='kPa'
            r['normalized_statistic']=key.removeprefix('mechanical_')
            r['normalization_rule']='exact pressure-unit scaling only; original statistical form retained'
    return r
if __name__=='__main__':
    from prepare_catalog import ROOT,write_csv
    import json
    rows=json.loads((ROOT/'02_extracted_data/records_curated.json').read_text(encoding='utf-8'))
    write_csv(ROOT/'03_processed_data/normalized_preview.csv',[normalize(r) for r in rows])
