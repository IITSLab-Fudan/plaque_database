"""Fetch public evidence without overwriting any previously archived file."""
import json, hashlib, urllib.request, urllib.parse, pathlib, datetime, concurrent.futures
ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / '01_raw_sources'
RAW.mkdir(parents=True, exist_ok=True)
def fetch(url, name):
    path = RAW / name
    if path.exists():
        return path.read_bytes()
    req = urllib.request.Request(url, headers={'User-Agent':'PlaqueEvidenceDatabase/1.0 (academic literature audit)'})
    data = urllib.request.urlopen(req, timeout=45).read()
    with path.open('xb') as f: f.write(data)
    meta = {'url':url, 'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(), 'sha256':hashlib.sha256(data).hexdigest(), 'bytes':len(data)}
    with path.with_suffix(path.suffix+'.meta.json').open('x',encoding='utf-8') as f: json.dump(meta,f,ensure_ascii=False,indent=2)
    return data
def article(key, query):
    u='https://www.ebi.ac.uk/europepmc/webservices/rest/search?'+urllib.parse.urlencode({'query':query,'format':'json','resultType':'core','pageSize':5})
    try:
        j=json.loads(fetch(u,key+'_metadata.json'))
        r=j['resultList']['result'][0]
        print(key, r.get('title'),r.get('doi'),r.get('pmcid'),flush=True)
        if r.get('pmcid'):
            try: fetch('https://www.ebi.ac.uk/europepmc/webservices/rest/'+r['pmcid']+'/fullTextXML',key+'_fulltext.xml')
            except Exception as e: print(key,'fulltext',str(e),flush=True)
    except Exception as e: print(key,str(e),flush=True)
if __name__=='__main__':
    entries=[('S001','DOI:10.1016/j.actbio.2014.09.001'),('S002','DOI:10.1016/j.jbiomech.2015.09.037'),('S003','EXT_ID:12119190'),('S004','EXT_ID:23664315'),('S005','EXT_ID:25553556'),('S006','TITLE:"Development of an intravascular ultrasound elastography based on a dual-element transducer"'),('S007','DOI:10.1161/CIRCULATIONAHA.112.132159'),('S008','DOI:10.1098/rsfs.2017.0008'),('S009','TITLE:"Mechanical properties of human atherosclerotic plaques"'),('S010','TITLE:"Experimental measurement of the mechanical properties of carotid atherothrombotic plaque fibrous cap"')]
    entries += [('S011','DOI:10.1038/s41467-026-70463-7'),('S012','EXT_ID:36832293'),('S013','EXT_ID:26091003'),('S014','PMC11766208'),('S015','PMC3230819'),('S016','DOI:10.3389/fbioe.2025.1478408')]
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        list(pool.map(lambda x:article(*x), entries))
