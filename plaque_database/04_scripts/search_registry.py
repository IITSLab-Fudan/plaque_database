"""Additional directly queried public indexes, cached append-only by acquire_sources."""
import json, urllib.parse, pathlib
from acquire_sources import fetch, ROOT
SEARCHES=[
 ('Europe PMC (PubMed-indexed literature)','(atherosclero* OR carotid) AND (plaque) AND (mechanical OR modulus OR indentation)'),
 ('Europe PMC (PubMed-indexed literature)','(atherosclero* OR carotid) AND plaque AND ("extracellular pH" OR "microelectrode" OR "pH heterogeneity")'),
 ('Europe PMC (PubMed-indexed literature)','(atherosclero* OR carotid) AND plaque AND ("hydrogen peroxide" OR H2O2)')]
def main():
    logs=[]
    for i,(engine,q) in enumerate(SEARCHES,1):
        url='https://www.ebi.ac.uk/europepmc/webservices/rest/search?'+urllib.parse.urlencode({'query':q,'format':'json','pageSize':20,'resultType':'lite'})
        try:
            j=json.loads(fetch(url,f'index_search_{i:02}.json'))
            results=j['resultList']['result']
            print(engine,q,'TOTAL',j['hitCount'])
            for r in results: print(r['id'],r['title'])
            logs.append(dict(search_engine=engine,query=q,date='2026-10-14',number_of_results_screened=len(results),reported_total_hits=j['hitCount'],url=url,archive=f'01_raw_sources/index_search_{i:02}.json',notes='First 20 returned titles screened; not all index hits. Exact article decisions recorded separately.'))
        except Exception as e:print('FAILED',url,e)
    url='https://api.crossref.org/works?'+urllib.parse.urlencode({'query.title':'atherosclerotic plaque mechanical pH hydrogen peroxide','rows':10})
    try:
        j=json.loads(fetch(url,'crossref_search.json'))
        for r in j['message']['items']:print('Crossref',r.get('DOI'),r.get('title'))
        logs.append(dict(search_engine='Crossref API',query='query.title=atherosclerotic plaque mechanical pH hydrogen peroxide; rows=10',date='2026-10-14',number_of_results_screened=len(j['message']['items']),url=url,archive='01_raw_sources/crossref_search.json',notes='Bibliographic discovery only; numerical extraction requires primary evidence.'))
    except Exception as e:print('Crossref failed',e)
    (ROOT/'02_extracted_data/index_search_log.json').write_text(json.dumps(logs,ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__':main()
