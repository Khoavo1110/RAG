import asyncio,json,time
from pathlib import Path
from backend.app.agents.router import AgenticRAG
async def main():
 cases=json.loads(Path("data/demo-doanh-nghiep/minh-an/evaluation/cases.json").read_text(encoding="utf-8"))
 results=[]
 for profile in ("gemini::gemini-2.5-flash","nvidia::nvidia/nemotron-3-super-120b-a12b","groq::openai/gpt-oss-120b"):
  for case in cases:
   if profile.split('::')[0]!='gemini' and case['id'] not in ('T03','T06'):continue
   started=time.monotonic();query=case['question'];history=[]
   if case['id']=='T20':
    first='Ai giao bản tích hợp cho Atlas?'
    answer=await AgenticRAG().ainvoke({'query':first,'tenant_id':'minh_an_demo','route':'documents','model_profile':profile})
    query='Người đó làm cho công ty nào, phải giao lúc nào và việc của họ ảnh hưởng dự án nào khác?'
    history=[{'role':'user','content':first},{'role':'assistant','content':answer['final_answer']}]
   try:result=await AgenticRAG().ainvoke({'query':query,'tenant_id':'minh_an_demo','route':'documents','history':history,'model_profile':profile})
   except Exception as exc:result={'error':type(exc).__name__}
   results.append({'case':case['id'],'profile':profile,'seconds':round(time.monotonic()-started,2),'result':result})
   Path('artifacts/rag-upgrade/api-model-evaluation.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
   print(profile,case['id'],result.get('answer_mode',result.get('error')),round(time.monotonic()-started,2),flush=True)
asyncio.run(main())
