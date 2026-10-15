"""Fetch selected compact processed files; leave large raw instrument files remote."""
import json,concurrent.futures,urllib.parse
from acquire_sources import fetch,RAW
def get(job):
    url,name=job
    try:print(name,len(fetch(url,name)))
    except Exception as e:print(name,type(e).__name__,str(e))
if __name__=='__main__':
    jobs=[]
    for a in ['GSE28829','GSE43292','GSE163154']:
        bucket=a[:-3]+'nnn'
        jobs.append((f'https://ftp.ncbi.nlm.nih.gov/geo/series/{bucket}/{a}/matrix/{a}_series_matrix.txt.gz',a+'_series_matrix.txt.gz'))
    for a in ['PXD031052','PXD039077']:
        files=json.loads((RAW/(a+'_files.json')).read_text())
        extra=RAW/(a+'_files_page1.json')
        if extra.exists():files+=json.loads(extra.read_text())
        for f in files:
            if f['fileName'].endswith('.xlsx') or f['fileName']=='Sample_list.tsv':
                url=next(x['value'] for x in f['publicFileLocations'] if x['name']=='FTP Protocol').replace('ftp://','https://')
                jobs.append((url,a+'_'+f['fileName']))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:list(ex.map(get,jobs))
