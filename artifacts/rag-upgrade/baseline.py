import asyncio,json,time
from pathlib import Path
from backend.app.agents.router import AgenticRAG
async def main():
 cases=json.loads(Path("data/demo-doanh-nghiep/minh-an/evaluation/cases.json").read_text(encoding="utf-8"))
 results=[]
 for case in cases:
  if case["id"] not in ("T03","T06"): continue
  started=time.monotonic()
  try: result=await AgenticRAG().ainvoke({"query":case["question"],"tenant_id":"minh_an_demo","route":"documents"})
  except Exception as exc: result={"error":type(exc).__name__}
  results.append({"case":case["id"],"seconds":round(time.monotonic()-started,2),"result":result})
  Path("artifacts/rag-upgrade/baseline.json").write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding="utf-8")
  print(case["id"],"done",flush=True)
asyncio.run(main())
