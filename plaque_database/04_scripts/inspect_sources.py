import pathlib, sys, json, re, xml.etree.ElementTree as ET, zipfile
from acquire_sources import article, fetch, ROOT, RAW
if __name__=='__main__':
    article('S017','EXT_ID:19107789')
    article('S018','EXT_ID:30218776')
    article('S019','EXT_ID:2022029')
    downloads=[('https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41467-026-70463-7/MediaObjects/41467_2026_70463_MOESM4_ESM.xlsx','S011_source_data.xlsx'),('https://datadryad.org/dataset/doi:10.5061/dryad.h862n','S006_dryad.html')]
    for u,n in downloads:
        try: print('Downloaded',n,len(fetch(u,n)))
        except Exception as e: print(n,e)
    for s in ['S003','S004','S005','S010','S013','S017','S018','S019']:
        p=RAW/(s+'_metadata.json')
        print('\n',s,json.loads(p.read_text(encoding='utf-8'))['resultList']['result'][0].get('abstractText'))
    for s in ['S012','S014','S016']:
        tree=ET.parse(RAW/(s+'_fulltext.xml'))
        for e in tree.iter('sec'):
            title=' '.join(e.find('title').itertext()) if e.find('title') is not None else ''
            if any(w in title.lower() for w in ['statistical','data avail','study population','histolog']): print(s,title,' '.join(e.itertext())[:6500])
    for s in ['S006']:
        tree=ET.parse(RAW/(s+'_fulltext.xml'))
        for e in tree.iter('sec'):
            title=' '.join(e.find('title').itertext()) if e.find('title') is not None else ''
            if any(w in title.lower() for w in ['atherosclerotic','ex vivo','data acces']): print(s,title,' '.join(e.itertext())[:5500])
