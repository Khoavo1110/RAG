import httpx,json,time
from pathlib import Path
cases=json.loads(Path("data/demo-doanh-nghiep/minh-an/evaluation/cases.json").read_text(encoding="utf-8"))
results=[]
with httpx.Client(base_url="http://127.0.0.1:8000",timeout=240) as client:
 health=client.get("/api/health");health.raise_for_status();print("health",health.json(),flush=True)
 for case in cases:
  if case["id"] not in ("T03","T06","T19"):continue
  start=time.monotonic();response=client.post("/api/query",json={"query":case["question"],"tenant_id":"minh_an_demo","mode":"documents"})
  result={"case":case["id"],"status":response.status_code,"seconds":round(time.monotonic()-start,2),"response":response.json()}
  results.append(result)
  Path("artifacts/rag-upgrade/final-api-check.json").write_text(json.dumps({"health":health.json(),"results":results},ensure_ascii=False,indent=2),encoding="utf-8")
  if response.status_code==200:client.delete("/api/conversations/"+result["response"]["conversation_id"],params={"tenant_id":"minh_an_demo"}).raise_for_status()
  print(case["id"],response.status_code,result["seconds"],flush=True)
