"""Archive primary repository metadata for the user-supplied supplement."""
import concurrent.futures,json,urllib.parse
from acquire_sources import fetch,article
GEO=['GSE28829','GSE43292','GSE163154','GSE159677','GSE253903','GSE253904','GSE210152','GSE253902']
def get_geo(a):
    try:
        b=fetch('https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc='+a+'&targ=all&form=text&view=quick',a+'_metadata.soft')
        print(a,len(b),b[:90])
    except Exception as e:print(a,str(e))
def get_pride(a):
    try:
        b=fetch('https://www.ebi.ac.uk/pride/ws/archive/v2/projects/'+a,a+'_metadata.json');print(a,len(b))
        b=fetch('https://www.ebi.ac.uk/pride/ws/archive/v2/projects/'+a+'/files?pageSize=100&page=0',a+'_files.json');print(a,'files',len(b))
        if a=='PXD031052':fetch('https://www.ebi.ac.uk/pride/ws/archive/v2/projects/'+a+'/files?pageSize=100&page=1',a+'_files_page1.json')
    except Exception as e:print(a,str(e))
def get_paper(p):
    try:article(*p)
    except Exception as e:print(p,str(e))
if __name__=='__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        list(ex.map(get_geo,GEO))
        list(ex.map(get_pride,['PXD031052','PXD039077']))
        list(ex.map(get_paper,[('S020','DOI:10.1038/s41467-019-11983-3'),('S021','EXT_ID:42313484 AND SRC:MED'),('S022','EXT_ID:10828566 AND SRC:MED'),('S023','DOI:10.1016/j.mbplus.2024.100141'),('R005','PMCID:PMC10165242'),('R006','PMCID:PMC5446086'),('R004','DOI:10.1186/s13062-025-00600-7')]))
