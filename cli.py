import sys
import os
import asyncio
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Ensure root directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# Load env variables into system environment
load_dotenv(BASE_DIR / ".env")

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.status import Status
from rich.table import Table
from rich import print as rprint

from backend.app.ingestion.database_sync import init_db, SessionLocal, db_sync_manager
from backend.app.ingestion.graph_extractor import graph_extractor
from backend.app.agents.router import agentic_rag_app

console = Console()

def show_welcome_banner():
    banner = """
  [bold cyan]⚡ AGENTIC RAG 2.0 CLI TERMINAL ⚡[/bold cyan]
  [dim]PGVector + Neo4j Graphiti + Multi-Agent Reasoning Loop[/dim]
  ======================================================
  """
    rprint(banner)

async def handle_ingest(file_path: str, title: str | None, tenant_id: str | None):
    path = Path(file_path)
    if not path.exists():
        console.print(f"[bold red]❌ Lỗi:[/bold red] Đường dẫn file '{file_path}' không tồn tại.")
        return

    if not title:
        title = path.name

    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        console.print(f"[bold red]❌ Lỗi khi đọc file:[/bold red] {e}")
        return

    console.print(f"[cyan]ℹ[/cyan] Đang đọc file: [bold]{title}[/bold] ({len(content)} ký tự)...")
    
    with Status("[bold yellow]Đang khởi tạo database và nạp tài liệu...", console=console) as status:
        try:
            init_db()
            await graph_extractor.initialize()
            db = SessionLocal()
            
            doc = await db_sync_manager.ingest_document(
                db=db,
                title=title,
                content=content,
                tenant_id=tenant_id
            )
            db.close()
            await graph_extractor.close()
            
            console.print(f"\n[bold green]✓ Nạp tài liệu thành công![/bold green]")
            console.print(Panel(
                f"[bold]ID:[/bold] {doc.id}\n"
                f"[bold]Tiêu đề:[/bold] {doc.title}\n"
                f"[bold]Tenant ID:[/bold] {tenant_id or 'global'}\n"
                f"[bold]Graphiti Episode UUID:[/bold] {doc.metadata_json.get('graphiti_episode_uuid')}",
                title="Thông tin tài liệu đã lưu", border_style="green"
            ))
        except Exception as e:
            console.print(f"\n[bold red]❌ Lỗi trong quá trình nạp tài liệu:[/bold red] {e}")

async def run_query(query_text: str, tenant_id: str | None):
    init_db()
    await graph_extractor.initialize()
    
    initial_state = {
        "query": query_text,
        "tenant_id": tenant_id,
        "route": "hybrid",
        "retrieved_contexts": [],
        "draft_answer": "",
        "critic_feedback": None,
        "refinement_query": None,
        "loop_count": 0,
        "final_answer": "",
        "thought_process": [],
        "sources": []
    }

    db = SessionLocal()
    config = {
        "configurable": {
            "db": db
        }
    }

    try:
        with Status("[bold yellow]Agent đang suy nghĩ và truy xuất dữ liệu...", console=console) as status:
            result = await agentic_rag_app.ainvoke(initial_state, config=config)
        
        # Print Thought Process
        console.print("\n[bold magenta]🧠 QUÁ TRÌNH SUY NGHĨ (THOUGHT PROCESS):[/bold magenta]")
        for idx, thought in enumerate(result.get("thought_process", [])):
            console.print(f"  [bold]{idx + 1}.[/bold] {thought}")
        
        # Print Final Answer
        answer = result.get("final_answer") or result.get("draft_answer") or "Không có câu trả lời."
        console.print("\n[bold green]💬 CÂU TRẢ LỜI:[/bold green]")
        console.print(Panel(Markdown(answer), border_style="cyan"))

        # Print Sources
        sources = result.get("sources", [])
        if sources:
            console.print("\n[bold yellow]📖 NGUỒN THAM CHIẾU:[/bold yellow]")
            table = Table(show_header=True, header_style="bold yellow")
            table.add_column("Loại", style="dim", width=12)
            table.add_column("Nội dung trích xuất", width=60)
            
            for src in sources:
                source_type = src.get("source_type", "unknown")
                if source_type == "vector":
                    content = src.get("content", "")
                    if len(content) > 120:
                        content = content[:117] + "..."
                    table.add_row("Vector DB", content)
                elif source_type == "graph":
                    content = src.get("context_string", "")
                    table.add_row("Neo4j Graph", content)
            
            console.print(table)
            
    except Exception as e:
        console.print(f"\n[bold red]❌ Lỗi thực thi Agent RAG:[/bold red] {e}")
    finally:
        db.close()
        await graph_extractor.close()

async def handle_chat(tenant_id: str | None):
    show_welcome_banner()
    console.print(f"[cyan]ℹ[/cyan] Đang ở chế độ Chat. Nhập [bold red]'exit'[/bold red] hoặc [bold red]'quit'[/bold red] để thoát.")
    console.print(f"[cyan]ℹ[/cyan] Tenant ID hiện tại: [bold]{tenant_id or 'global'}[/bold]")
    console.print("-" * 50)
    
    while True:
        try:
            query = Prompt.ask("\n[bold blue]Hỏi AI[/bold blue]")
            if query.strip().lower() in ["exit", "quit"]:
                console.print("[yellow]Tạm biệt![/yellow]")
                break
                
            if not query.strip():
                continue
                
            await run_query(query, tenant_id)
            console.print("-" * 50)
        except KeyboardInterrupt:
            console.print("\n[yellow]Tạm biệt![/yellow]")
            break
        except Exception as e:
            console.print(f"[bold red]Lỗi:[/bold red] {e}")

def main():
    parser = argparse.ArgumentParser(description="Agentic RAG 2.0 CLI Tool")
    subparsers = parser.add_subparsers(dest="command", help="Lệnh cần chạy")

    # Ingest subcommand
    parser_ingest = subparsers.add_parser("ingest", help="Nạp tài liệu văn bản vào cơ sở dữ liệu")
    parser_ingest.add_argument("--file", required=True, help="Đường dẫn tới file văn bản (.txt, .md)")
    parser_ingest.add_argument("--title", help="Tiêu đề tài liệu (Mặc định lấy tên file)")
    parser_ingest.add_argument("--tenant", help="Tenant ID để phân quyền tài liệu")

    # Query subcommand
    parser_query = subparsers.add_parser("query", help="Gửi câu hỏi đơn lẻ đến Agentic RAG")
    parser_query.add_argument("--text", required=True, help="Nội dung câu hỏi")
    parser_query.add_argument("--tenant", help="Tenant ID để lọc dữ liệu")

    # Chat subcommand
    parser_chat = subparsers.add_parser("chat", help="Khởi động chế độ chat tương tác")
    parser_chat.add_argument("--tenant", help="Tenant ID mặc định khi chat")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Run async loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        if args.command == "ingest":
            loop.run_until_complete(handle_ingest(args.file, args.title, args.tenant))
        elif args.command == "query":
            loop.run_until_complete(run_query(args.text, args.tenant))
        elif args.command == "chat":
            loop.run_until_complete(handle_chat(args.tenant))
    finally:
        loop.close()

if __name__ == "__main__":
    main()
