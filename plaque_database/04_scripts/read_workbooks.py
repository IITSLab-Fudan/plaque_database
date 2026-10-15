"""Read OOXML source workbooks using Python standard library; no source edits."""
import zipfile, xml.etree.ElementTree as E, json, re
from acquire_sources import RAW, ROOT, fetch
NS={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
def sheets(path):
    with zipfile.ZipFile(path) as z:
        shared=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            shared=[''.join(t.itertext()) for t in E.fromstring(z.read('xl/sharedStrings.xml'))]
        rels={r.get('Id'):r.get('Target') for r in E.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
        for s in E.fromstring(z.read('xl/workbook.xml')).find('m:sheets',NS):
            target=rels[s.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')]
            target=target.lstrip('/') if target.startswith('/') else 'xl/'+target
            cells={}
            for c in E.fromstring(z.read(target)).iter('{'+NS['m']+'}c'):
                v=c.find('m:v',NS)
                value=v.text if v is not None else ''.join(c.find('m:is',NS).itertext()) if c.find('m:is',NS) is not None else ''
                if c.get('t')=='s' and value: value=shared[int(value)]
                if value: cells[c.get('r')]=value
            yield s.get('name'),cells
if __name__=='__main__':
    out=ROOT/'02_extracted_data';out.mkdir(exist_ok=True)
    p=RAW/'S006_dryad.html'
    html=p.read_text(encoding='utf-8')
    for m in re.finditer(r'href="([^"]+)"[^>]*>\s*curves_data.xlsx',html):
        u='https://datadryad.org'+m.group(1) if m.group(1).startswith('/') else m.group(1)
        try: print('Dryad download',u,len(fetch(u,'S006_curves_data.xlsx')))
        except Exception as e: print(e)
    for p in RAW.glob('*.xlsx'):
        ss=dict(sheets(p))
        (out/(p.stem+'_cells.json')).write_text(json.dumps(ss,ensure_ascii=False,indent=2),encoding='utf-8')
        for name,cells in ss.items():
            print(p.name,name,len(cells),list(cells.items())[:8])
            hits={k:v for k,v in cells.items() if any(w in v.lower() for w in ['peroxide','h2o2','h₂o₂','plaque','arter','lipid'])}
            if hits: print('MATCHES',hits)
