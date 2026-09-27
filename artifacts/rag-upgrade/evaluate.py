import asyncio,json,re,time
from pathlib import Path
from backend.app.agents.tools import lexical_search, expand_evidence, fuse_sources
from backend.app.agents.router import AgenticRAG
ROOT=Path("artifacts/rag-upgrade")
async def main():
 cases=json.loads(Path("data/demo-doanh-nghiep/minh-an/evaluation/cases.json").read_text(encoding="utf-8"))
 retrieval=[]
 for case in cases:
  if case["id"]=="T20": continue
  lexical=lexical_search(case["question"],"minh_an_demo")
  new=expand_evidence(case["question"],"minh_an_demo",fuse_sources([],lexical),[])
  expected=case["sources"]
  before=[s["title"] for s in lexical[:6]]
  after=[s["title"] for s in new]
  retrieval.append({"case":case["id"],"expected":expected,"before":before,"after":after,
    "before_recall":sum(any(code in title for title in before) for code in expected)/len(expected),
    "after_recall":sum(any(code in title for title in after) for code in expected)/len(expected)})
 ROOT.joinpath("retrieval.json").write_text(json.dumps(retrieval,ensure_ascii=False,indent=2),encoding="utf-8")
 results=[]
 for case in cases:
  started=time.monotonic()
  question=case["question"]
  history=[]
  if case["id"]=="T20":
   first="Ai giao bản tích hợp cho Atlas?"
   first_result=await AgenticRAG().ainvoke({"query":first,"tenant_id":"minh_an_demo","route":"documents"})
   question="Người đó làm cho công ty nào, phải giao lúc nào và việc của họ ảnh hưởng dự án nào khác?"
   history=[{"role":"user","content":first},{"role":"assistant","content":first_result["final_answer"]}]
  try:
   result=await AgenticRAG().ainvoke({"query":question,"tenant_id":"minh_an_demo","route":"documents","history":history})
  except Exception as exc: result={"error":type(exc).__name__}
  results.append({"case":case["id"],"seconds":round(time.monotonic()-started,2),"result":result})
  ROOT.joinpath("after.json").write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding="utf-8")
  print(case["id"],result.get("answer_mode",result.get("error")),round(time.monotonic()-started),flush=True)
asyncio.run(main())
