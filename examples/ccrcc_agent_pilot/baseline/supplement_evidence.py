import evidence as e,json,urllib.parse
queries={'ca9_zircon':'girentuximab AND ZIRCON','nnmt_renal':'NNMT AND renal AND carcinoma','mtor_renal':'TITLE:"Temsirolimus, interferon alfa, or both for advanced renal-cell carcinoma"','ndufa4l2_renal':'NDUFA4L2 AND renal AND carcinoma'}
for name,q in queries.items():
 d=e.fetch(name,'https://www.ebi.ac.uk/europepmc/webservices/rest/search?'+urllib.parse.urlencode(dict(query=q,format='json',pageSize=3,resultType='core')))
 print(name,json.dumps([{'id':r.get('id'),'title':r.get('title'),'year':r.get('pubYear'),'abstract':r.get('abstractText')} for r in (d or {}).get('resultList',{}).get('result',[])],indent=2))
(e.S/'source_manifest.json').write_text(json.dumps(sorted(e.records,key=lambda x:x['name']),indent=2))
