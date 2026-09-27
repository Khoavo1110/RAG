import asyncio
import json
import sys
import os
import time
import httpx

sys.stdout.reconfigure(encoding='utf-8')

CASES_FILE = r"d:\RAG\data\demo-doanh-nghiep\minh-an\evaluation\cases.json"
API_URL = "http://localhost:8000/api/query"
OUTPUT_FILE = r"d:\RAG\artifacts\evaluation_nori_gemini_20_questions.json"

async def run_eval():
    with open(CASES_FILE, "r", encoding="utf-8") as f:
        cases = json.load(f)

    results = []
    print(f"Bắt đầu đánh giá {len(cases)} câu hỏi với Nori (Google Gemini API)...\n" + "="*60)

    async with httpx.AsyncClient(timeout=180.0) as client:
        for idx, case in enumerate(cases, 1):
            qid = case["id"]
            qtype = case["type"]
            question = case["question"]
            expected = case["expected"]
            expected_sources = case.get("sources", [])

            print(f"\n[{idx}/20] Đang chạy {qid} ({qtype}): {question}")

            payload = {
                "query": question,
                "tenant_id": "minh_an_demo",
                "mode": "hybrid",
                "model_profile": "gemini::gemini-2.5-flash"
            }

            start_t = time.time()
            try:
                resp = await client.post(API_URL, json=payload)
                elapsed = time.time() - start_t
                if resp.status_code == 200:
                    data = resp.json()
                    answer = data.get("answer", "")
                    sources = data.get("sources", [])
                    steps = data.get("thought_process", [])
                    answer_mode = data.get("answer_mode")
                    print(f"  -> Hoàn thành trong {elapsed:.1f}s | Mode: {answer_mode}")
                    print(f"  -> Câu trả lời: {answer[:160]}...")
                else:
                    elapsed = time.time() - start_t
                    answer = f"ERROR: HTTP {resp.status_code} - {resp.text}"
                    sources = []
                    steps = []
                    answer_mode = "error"
                    print(f"  -> Lỗi: {answer}")
            except Exception as e:
                elapsed = time.time() - start_t
                answer = f"EXCEPTION: {str(e)}"
                sources = []
                steps = []
                answer_mode = "exception"
                print(f"  -> Exception: {e}")

            results.append({
                "id": qid,
                "type": qtype,
                "question": question,
                "expected": expected,
                "expected_sources": expected_sources,
                "answer": answer,
                "answer_mode": answer_mode,
                "elapsed": elapsed,
                "steps": steps
            })

            # Lưu tạm kết quả sau mỗi câu
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f_out:
                json.dump(results, f_out, ensure_ascii=False, indent=2)

            # Nghỉ 2.5s để tuân thủ RPM và rate limit của Google Gemini
            await asyncio.sleep(2.5)

    print("\n" + "="*60)
    print("Hoàn tất đánh giá toàn bộ 20 câu hỏi!")

if __name__ == "__main__":
    asyncio.run(run_eval())
