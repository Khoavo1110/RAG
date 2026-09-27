import httpx,json,time
from pathlib import Path
cases=json.loads(Path('data/demo-doanh-nghiep/minh-an/evaluation/cases.json').read_text(encoding='utf-8'))
results=[]
with httpx.Client(base_url='http://127.0.0.1:8000',timeout=425) as client:
 catalog=client.get('/api/models');catalog.raise_for_status()
 for profile,ids in [('nvidia::nvidia/nemotron-3-super-120b-a12b',('T03',)),('gemini::gemini-2.5-flash',('T03','T06')),('groq::openai/gpt-oss-120b',('T03',)),('ollama::qwen2.5:3b',('T19',))]:
  for case in cases:
   if case['id'] not in ids:continue
   started=time.monotonic()
   r=client.post('/api/query',json={'query':case['question'],'tenant_id':'minh_an_demo','mode':'documents','model_profile':profile})
   result={'case':case['id'],'profile':profile,'status':r.status_code,'seconds':round(time.monotonic()-started,2),'response':r.json()};results.append(result)
   Path('artifacts/rag-upgrade/model-selection-final-adapter-check.json').write_text(json.dumps({'catalog':catalog.json(),'results':results},ensure_ascii=False,indent=2),encoding='utf-8')
   if r.status_code==200:
    assert result['response']['model_used']['id']==profile
    client.delete('/api/conversations/'+result['response']['conversation_id'],params={'tenant_id':'minh_an_demo'}).raise_for_status()
   print(profile,case['id'],r.status_code,result['response'].get('answer_mode'),result['response'].get('failure_reason'),result['seconds'],flush=True)
