import asyncio,json,time
from pathlib import Path
from backend.app.models import resolve_profile,selected_profile
from backend.app.agents.critic import complete
async def probe(profile_id):
 p=resolve_profile(profile_id);token=selected_profile.set(p);started=time.monotonic()
 try:
  raw=await complete([{"role":"user","content":"Return only JSON with ok equal to true."}],json_mode=True)
  try:valid=json.loads(raw).get("ok") is True
  except Exception:valid=False
  result={"profile":profile_id,"generated":True,"json_valid":valid,"seconds":round(time.monotonic()-started,2)}
 except Exception as exc:result={"profile":profile_id,"generated":False,"error":type(exc).__name__,"status":getattr(exc,"status_code",None),"seconds":round(time.monotonic()-started,2)}
 finally:selected_profile.reset(token)
 print(json.dumps(result),flush=True);return result
async def main():
 ids=["gemini::gemini-2.5-flash","nvidia::nvidia/nemotron-3-super-120b-a12b","groq::openai/gpt-oss-120b","openrouter::nvidia/nemotron-3-super-120b-a12b:free"]
 results=await asyncio.gather(*(probe(i) for i in ids))
 Path("artifacts/rag-upgrade/provider-generation-check.json").write_text(json.dumps(results,indent=2),encoding="utf-8")
asyncio.run(main())
