import React, { useState, useRef } from 'react';
import { GraphVisualizer } from './components/GraphVisualizer';
import { ChatWindow } from './components/ChatWindow';
import { ThoughtProcess } from './components/ThoughtProcess';

interface Message {
  role: 'user' | 'assistant';
  text: string;
  sources?: any[];
  latency?: number;
}

export default function App() {
  const [selectedTenant, setSelectedTenant] = useState('tenant_fpt_001');
  const [tenantDisplayName, setTenantDisplayName] = useState('FPT Corporate (tenant_fpt_001)');
  const [isTenantDropdownOpen, setIsTenantDropdownOpen] = useState(false);
  
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      text: 'Xin chào! Tôi là Trợ lý Aetheris RAG 2.0. Tôi có thể truy xuất thông tin từ tài liệu thông thường và đồ thị thực thể Neo4j của bạn để đưa ra các câu trả lời chính xác, được kiểm chứng bởi Critic Agent.'
    }
  ]);
  const [thoughts, setThoughts] = useState<string[]>([]);
  const [graphSources, setGraphSources] = useState<any[]>([]);
  const [isQuerying, setIsQuerying] = useState(false);
  const [latency, setLatency] = useState<string | number>('--');
  
  const [isIngesting, setIsIngesting] = useState(false);
  const [ingestStatus, setIngestStatus] = useState<string | null>(null);
  const [ingestError, setIngestError] = useState<string | null>(null);

  // Graph details
  const [hoveredNode, setHoveredNode] = useState<{ name: string; type: string; fact: string } | null>(null);
  const [stats, setStats] = useState({ nodes: 0, edges: 0 });

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Handle Tenant selection
  const handleTenantSelect = (tenantId: string, displayName: string) => {
    setSelectedTenant(tenantId);
    setTenantDisplayName(displayName);
    setIsTenantDropdownOpen(false);
    // Clear chat history on tenant switch to maintain absolute security isolation
    setMessages([
      {
        role: 'assistant',
        text: `Đã chuyển sang môi trường **${displayName}**. Lịch sử hội thoại đã được làm mới để đảm bảo cách ly bảo mật.`
      }
    ]);
    setThoughts([]);
    setGraphSources([]);
  };

  const handleCustomTenant = () => {
    const customId = prompt("Nhập Tenant ID của bạn:");
    if (customId && customId.trim()) {
      handleTenantSelect(customId.trim(), `Custom Workspace (${customId.trim()})`);
    }
    setIsTenantDropdownOpen(false);
  };

  // Document Ingestion API trigger
  const handleFileUpload = async (file: File) => {
    if (isIngesting) return;
    setIsIngesting(true);
    setIngestStatus(`Đang đọc tệp ${file.name}...`);
    setIngestError(null);

    const reader = new FileReader();
    reader.onload = async (e) => {
      const text = e.target?.result as string;
      if (!text) {
        setIngestError("Không thể đọc tệp văn bản hoặc tệp rỗng.");
        setIsIngesting(false);
        return;
      }

      try {
        setIngestStatus(`Đang tải lên hệ thống...`);
        const response = await fetch('http://localhost:8000/api/ingest', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            title: file.name,
            content: text,
            metadata: { tenant_id: selectedTenant }
          })
        });

        if (!response.ok) {
          throw new Error(`API response error: ${response.statusText}`);
        }

        setIngestStatus(`Tải lên thành công! Tài liệu đang được trích xuất đồ thị...`);
        setTimeout(() => setIngestStatus(null), 3000);
      } catch (err: any) {
        setIngestError(`Lỗi tải lên: ${err.message}`);
        setTimeout(() => setIngestError(null), 4000);
      } finally {
        setIsIngesting(false);
      }
    };
    reader.readAsText(file);
  };

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  // Send query to API
  const handleSendMessage = async (text: string) => {
    if (isQuerying) return;
    
    const userMsg: Message = { role: 'user', text };
    setMessages((prev) => [...prev, userMsg]);
    setIsQuerying(true);
    setLatency('...');
    setThoughts([]);

    const startTime = performance.now();

    try {
      const response = await fetch('http://localhost:8000/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: text,
          tenant_id: selectedTenant
        })
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
      }

      const data = await response.json();
      const endTime = performance.now();
      const durationMs = Math.round(endTime - startTime);
      setLatency(`${durationMs}ms`);

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: data.answer,
          sources: data.sources
        }
      ]);

      if (data.thought_process) {
        setThoughts(data.thought_process);
      }
      if (data.sources) {
        setGraphSources(data.sources);
      }
    } catch (err: any) {
      setLatency('Lỗi');
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: `**Lỗi hệ thống:** Không thể kết nối tới backend. Vui lòng đảm bảo cổng 8000 đang hoạt động. (${err.message})`
        }
      ]);
    } finally {
      setIsQuerying(false);
    }
  };

  return (
    <div className="h-screen w-screen font-sans bg-background text-on-surface overflow-hidden relative select-none">
      
      {/* Top Navbar */}
      <nav className="fixed top-0 w-full z-50 flex justify-between items-center px-6 h-16 bg-surface/60 backdrop-blur-xl border-b border-white/10 shadow-[0_0_15px_-3px_rgba(93,230,255,0.05)]">
        <div className="flex items-center gap-4">
          <span className="font-bold text-lg text-secondary tracking-wide">Aetheris RAG</span>
          <div className="hidden md:flex gap-6 ml-8">
            <a className="font-semibold text-sm text-secondary border-b-2 border-secondary pb-1" href="#workspace">Workspace</a>
            <a className="font-semibold text-sm text-on-surface-variant hover:text-secondary transition-colors duration-200" href="#models">Models</a>
            <a className="font-semibold text-sm text-on-surface-variant hover:text-secondary transition-colors duration-200" href="#security">Security</a>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <button className="material-symbols-outlined text-on-surface-variant hover:text-secondary transition-colors cursor-pointer">notifications</button>
          <button className="material-symbols-outlined text-on-surface-variant hover:text-secondary transition-colors cursor-pointer">settings</button>
          <div className="w-8 h-8 rounded-full overflow-hidden border border-secondary/30">
            <img className="w-full h-full object-cover" alt="User profile" src="https://lh3.googleusercontent.com/aida-public/AB6AXuBNZXIzQx9tIoftU1Nds8KrbzLG3az0zHwDbkKqvZNb1-alFpZ2TNpK7TGLXW10qUgnDQkKrxBDQ_QdojWmmUzgjOGI_hK0d7fiw2Bxgie1QdYNd8bdoTG3K85cTMnmAc3UelG-76Hyso8OHLaEIdSBLyEO9F1uu8040XvASFkL7b6_oIuJBZfgNy8iL8p4C0g6EB03OGhqKF7Rtp99ssDfLlOW3pmlbRHqx3S5nVAwO0ijtkw8ym7N03eg2h3EVAXC-Wys3fNlMpM3" />
          </div>
        </div>
      </nav>

      {/* Workspace Panel Container */}
      <main className="relative z-10 pt-16 h-full flex w-full">
        
        {/* Left Aside: Ingestion & Process */}
        <aside className="w-[25%] h-[calc(100vh-64px)] glass-panel border-r border-white/10 flex flex-col py-6 px-6 gap-8 overflow-hidden">
          
          {/* Workspace Environment Dropdown */}
          <div>
            <label className="text-[12px] font-bold text-on-surface-variant/70 uppercase tracking-widest block mb-2">Workspace Environment</label>
            <div className="relative">
              <button
                onClick={() => setIsTenantDropdownOpen(!isTenantDropdownOpen)}
                className="w-full flex items-center justify-between bg-surface-container-high/40 p-3 rounded-lg border border-white/5 hover:border-secondary/50 transition-all text-left cursor-pointer"
              >
                <div className="flex items-center gap-3">
                  <span className="material-symbols-outlined text-secondary" style={{ fontVariationSettings: "'FILL' 1" }}>corporate_fare</span>
                  <span className="font-semibold text-sm text-on-surface">{tenantDisplayName}</span>
                </div>
                <span className="material-symbols-outlined text-on-surface-variant">unfold_more</span>
              </button>

              {isTenantDropdownOpen && (
                <div className="absolute top-full left-0 right-0 mt-2 bg-surface-container-low border border-white/10 rounded-lg shadow-xl z-[999] overflow-hidden glass-panel">
                  <button
                    onClick={() => handleTenantSelect('tenant_fpt_001', 'FPT Corporate (tenant_fpt_001)')}
                    className="w-full p-3 text-left hover:bg-secondary/15 transition-all text-on-surface flex flex-col border-none bg-transparent cursor-pointer"
                  >
                    <span className="font-semibold text-sm text-on-surface">FPT Corporate</span>
                    <span className="text-[11px] text-on-surface-variant">tenant_fpt_001</span>
                  </button>
                  <button
                    onClick={() => handleTenantSelect('tenant_nvidia_002', 'NVIDIA Partner (tenant_nvidia_002)')}
                    className="w-full p-3 text-left hover:bg-secondary/15 transition-all text-on-surface flex flex-col border-t border-white/5 border-b-none border-x-none bg-transparent cursor-pointer"
                  >
                    <span className="font-semibold text-sm text-on-surface">NVIDIA Partner</span>
                    <span className="text-[11px] text-on-surface-variant">tenant_nvidia_002</span>
                  </button>
                  <button
                    onClick={() => handleTenantSelect('tenant_general_003', 'General Tenant (tenant_general_003)')}
                    className="w-full p-3 text-left hover:bg-secondary/15 transition-all text-on-surface flex flex-col border-t border-white/5 border-b-none border-x-none bg-transparent cursor-pointer"
                  >
                    <span className="font-semibold text-sm text-on-surface">General Public</span>
                    <span className="text-[11px] text-on-surface-variant">tenant_general_003</span>
                  </button>
                  <button
                    onClick={handleCustomTenant}
                    className="w-full p-3 text-left hover:bg-secondary/15 transition-all text-on-surface flex items-center justify-between border-t border-white/5 border-b-none border-x-none bg-transparent cursor-pointer"
                  >
                    <span className="font-semibold text-sm text-secondary">Custom Tenant ID...</span>
                    <span className="material-symbols-outlined text-sm text-secondary">edit</span>
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Document Ingestion Zone */}
          <div className="flex flex-col gap-4">
            <h3 className="font-semibold text-secondary flex items-center gap-2 text-sm">
              <span className="material-symbols-outlined text-sm">cloud_upload</span>
              DOCUMENT INGESTION
            </h3>
            <div
              onDragOver={onDragOver}
              onDrop={onDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-xl p-8 flex flex-col items-center justify-center gap-3 transition-all cursor-pointer group relative ${
                isIngesting 
                  ? 'border-amber-500/50 bg-amber-500/5' 
                  : 'border-secondary/20 bg-secondary/5 hover:bg-secondary/10 hover:border-secondary/40'
              }`}
            >
              <input
                type="file"
                ref={fileInputRef}
                onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0])}
                className="hidden"
                accept=".txt,.md,.json,.html"
              />
              
              <div className={`w-12 h-12 rounded-full flex items-center justify-center transition-transform group-hover:scale-110 ${
                isIngesting ? 'bg-amber-500/10 text-amber-500' : 'bg-secondary/10 text-secondary'
              }`}>
                <span className="material-symbols-outlined text-3xl">
                  {isIngesting ? 'progress_activity' : 'upload_file'}
                </span>
              </div>

              <div className="text-center">
                <p className="font-medium text-sm text-on-surface">
                  {isIngesting ? 'Đang tải tài liệu...' : 'Thả tệp hoặc click chọn'}
                </p>
                <p className="text-[11px] text-on-surface-variant/70 uppercase tracking-widest mt-1">/api/ingest</p>
              </div>
            </div>

            {/* Ingestion status alert messages */}
            {ingestStatus && (
              <div className="text-xs p-3 rounded bg-amber-500/20 text-amber-300 flex items-center gap-2 border border-amber-500/30">
                <span className="material-symbols-outlined text-sm">info</span>
                <span>{ingestStatus}</span>
              </div>
            )}
            {ingestError && (
              <div className="text-xs p-3 rounded bg-red-500/20 text-red-300 flex items-center gap-2 border border-red-500/30">
                <span className="material-symbols-outlined text-sm">error</span>
                <span>{ingestError}</span>
              </div>
            )}
          </div>

          {/* Staggered thoughts timeline */}
          <ThoughtProcess thoughts={thoughts} />
        </aside>

        {/* Center Panel: Chat logs */}
        <ChatWindow
          messages={messages}
          onSendMessage={handleSendMessage}
          isQuerying={isQuerying}
          latency={latency}
          onAttachClick={() => fileInputRef.current?.click()}
        />

        {/* Right Aside: 3D Visualization */}
        <aside className="w-[35%] h-[calc(100vh-64px)] glass-panel border-l border-white/10 flex flex-col overflow-hidden relative">
          
          {/* Graph Visualization Container */}
          <div className="relative flex-1 bg-surface-container-lowest/10">
            <GraphVisualizer
              sources={graphSources}
              onNodeHover={setHoveredNode}
              onStatsChange={(nodes, edges) => setStats({ nodes, edges })}
            />

            {/* Header Overlay */}
            <div className="absolute top-6 left-6 right-6 flex justify-between items-start pointer-events-none">
              <div className="pointer-events-auto">
                <h3 className="text-xs font-bold text-secondary uppercase tracking-widest">KNOWLEDGE GRAPH</h3>
                <p className="text-[12px] text-on-surface-variant">Mapping Semantic Entities</p>
              </div>
              <div className="flex gap-2 pointer-events-auto">
                <button 
                  onClick={() => alert("Zoom & xoay đồ thị bằng cách nhấp và kéo chuột trên màn hình 3D.")}
                  className="w-10 h-10 rounded-lg bg-surface/80 backdrop-blur-md border border-white/10 flex items-center justify-center hover:bg-surface hover:text-secondary transition-colors shadow-lg cursor-pointer"
                >
                  <span className="material-symbols-outlined text-[20px]">zoom_in</span>
                </button>
                <button 
                  onClick={() => setGraphSources([])}
                  className="w-10 h-10 rounded-lg bg-surface/80 backdrop-blur-md border border-white/10 flex items-center justify-center hover:bg-surface hover:text-secondary transition-colors shadow-lg cursor-pointer"
                  title="Đặt lại Graph"
                >
                  <span className="material-symbols-outlined text-[20px]">recenter</span>
                </button>
              </div>
            </div>

            {/* Dynamic Bottom Detail Panel */}
            <div className="absolute bottom-6 left-6 right-6">
              <div className="glass-panel p-5 rounded-2xl border-l-4 border-l-tertiary cyan-glow">
                <div className="flex justify-between items-start mb-3">
                  <div className="flex items-center gap-2">
                    <span className="material-symbols-outlined text-tertiary">database_search</span>
                    <span className="font-semibold text-sm text-on-surface">
                      {hoveredNode ? hoveredNode.name : 'Chưa chọn thực thể'}
                    </span>
                  </div>
                  <span className="text-[10px] bg-tertiary/20 text-tertiary px-2 py-0.5 rounded uppercase font-bold tracking-tighter">
                    {hoveredNode ? hoveredNode.type : 'NONE'}
                  </span>
                </div>
                <p className="text-[13px] text-on-surface-variant leading-relaxed">
                  {hoveredNode ? hoveredNode.fact : 'Rê chuột vào các nút hình cầu trong đồ thị 3D để kiểm tra chi tiết các thực thể liên quan và liên kết ngữ cảnh.'}
                </p>
              </div>
            </div>
          </div>

          {/* Stats Bar */}
          <div className="p-6 bg-surface-container-high/40 border-t border-white/10 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex flex-col">
                <span className="text-[10px] text-on-surface-variant/50 uppercase font-bold">Nodes</span>
                <span className="font-bold text-[18px] text-secondary">{stats.nodes}</span>
              </div>
              <div className="w-px h-8 bg-white/10"></div>
              <div className="flex flex-col">
                <span className="text-[10px] text-on-surface-variant/50 uppercase font-bold">Edges</span>
                <span className="font-bold text-[18px] text-tertiary">{stats.edges}</span>
              </div>
            </div>
            <button 
              onClick={() => alert(`Các thực thể đang hiển thị: ${stats.nodes} nút, ${stats.edges} liên kết.`)}
              className="font-semibold text-[12px] text-on-surface hover:text-secondary flex items-center gap-2 border border-white/10 px-4 py-2 rounded-lg bg-white/5 transition-all cursor-pointer"
            >
              CHI TIẾT <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
            </button>
          </div>
        </aside>
      </main>
    </div>
  );
}
