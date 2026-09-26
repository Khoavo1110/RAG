import { useEffect, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import { ArrowUp, ArrowUpRight, BookOpen, Check, ChevronDown, ChevronRight, Copy, FileText, FolderOpen, Leaf, LoaderCircle, Menu, MessageSquare, Moon, PanelLeftClose, Paperclip, Plus, Search, Settings2, Sparkles, Sun, Trash2, Upload, X } from 'lucide-react';
import { request, workspace } from './api';
import type { Conversation, Document, Health, Message, Source, ModelCatalog } from './types';

function Mark({ small = false }: { small?: boolean }) {
  return <svg className={small ? 'mark small' : 'mark'} viewBox="0 0 64 64" fill="none" aria-hidden="true"><path d="M32 31C12 34 8 14 18 10c11-5 15 9 14 21Z" fill="currentColor"/><path d="M33 31c-3-20 17-24 21-14 5 11-9 15-21 14Z" fill="currentColor" opacity=".8"/><path d="M33 33c20-3 24 17 14 21-11 5-15-9-14-21Z" fill="currentColor" opacity=".65"/><path d="M31 33c3 20-17 24-21 14-5-11 9-15 21-14Z" fill="currentColor" opacity=".9"/></svg>;
}
function Dialog({ title, children, close }: { title: string; children: ReactNode; close: () => void }) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => { const d = ref.current; d?.showModal(); return () => d?.close(); }, []);
  return <dialog ref={ref} onCancel={close} onClick={e => { if (e.target === e.currentTarget) close(); }}><div className="dialog-inner"><header><h2>{title}</h2><button className="icon" onClick={close} aria-label="Đóng"><X size={20}/></button></header>{children}</div></dialog>;
}
function RichText({ text, onSource }: { text: string; onSource: () => void }) {
  const inline = (line: string) => line.split(/(\*\*.*?\*\*|`[^`]+`|\[\d+\])/g).map((part, i) => part.startsWith('**') ? <strong key={i}>{part.slice(2, -2)}</strong> : part.startsWith('`') ? <code key={i}>{part.slice(1, -1)}</code> : /^\[\d+\]$/.test(part) ? <button key={i} className="citation" onClick={onSource} aria-label={`Xem nguồn ${part}`}>{part.slice(1, -1)}</button> : part);
  return <div className="rich-text">{text.split(/(```[\s\S]*?```)/g).map((block, i) => block.startsWith('```') ? <pre key={i}><code>{block.slice(3, -3).replace(/^\w*\n/, '')}</code></pre> : block.split('\n').map((line, j) => /^#{1,4} /.test(line) ? <h3 key={`${i}-${j}`}>{inline(line.replace(/^#+ /, ''))}</h3> : /^[-*] /.test(line) ? <div className="bullet" key={`${i}-${j}`}><span>•</span><div>{inline(line.slice(2))}</div></div> : <p key={`${i}-${j}`}>{line ? inline(line) : <br/>}</p>))}</div>;
}
const safeTheme = () => { try { return localStorage.getItem('nori-theme') === 'dark'; } catch { return false; } };
const safeWorkspace = () => { try { return localStorage.getItem('nori-workspace') ?? 'minh_an_demo'; } catch { return 'minh_an_demo'; } };
const workspaceName = (id: string) => id === 'minh_an_demo' ? 'Minh An Supply' : id || 'Không gian chung';
const safeModelProfile = () => { try { return localStorage.getItem('nori-model-profile') || ''; } catch { return ''; } };
export default function App() {
  const [dark, setDark] = useState(safeTheme);
  const [mobile, setMobile] = useState(false);
  const [view, setView] = useState<'chat' | 'library'>('chat');
  const [tenant, setTenant] = useState(safeWorkspace);
  const [tenants, setTenants] = useState<(string | null)[]>([null]);
  const [modelCatalog, setModelCatalog] = useState<ModelCatalog | null>(null);
  const [modelProfile, setModelProfile] = useState(safeModelProfile);
  const lastModelProfiles = useRef({ local: '', api: '' });
  const selectedModel = modelCatalog?.profiles.find(p => p.id === modelProfile);
  const executionMode = selectedModel?.mode || 'api';
  const [health, setHealth] = useState<Health | null>(null);
  const [docs, setDocs] = useState<Document[]>([]);
  const [chats, setChats] = useState<Conversation[]>([]);
  const [active, setActive] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState('');
  const [search, setSearch] = useState('');
  const [mode, setMode] = useState('hybrid');
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [settings, setSettings] = useState(false);
  const [sourceMessage, setSourceMessage] = useState<Message | null>(null);
  const [preview, setPreview] = useState<Document | null>(null);
  const [confirm, setConfirm] = useState<{ kind: 'document' | 'chat'; id: string; title: string } | null>(null);
  const [copied, setCopied] = useState<string | null>(null);
  const file = useRef<HTMLInputElement>(null);
  const input = useRef<HTMLTextAreaElement>(null);
  const bottom = useRef<HTMLDivElement>(null);
  const generation = useRef(0);
  const sendLock = useRef(false);
  const pending = busy || uploading || loading;

  useEffect(() => { document.documentElement.dataset.theme = dark ? 'dark' : 'light'; try { localStorage.setItem('nori-theme', dark ? 'dark' : 'light'); } catch { /* Storage may be disabled. */ } }, [dark]);
  useEffect(() => {
    let alive = true;
    const check = () => request<Health>('/api/health').then(v => { if (alive) setHealth(v); }).catch(() => { if (alive) setHealth(null); });
    request<ModelCatalog>('/api/models').then(catalog => {
      if (!alive) return;
      setModelCatalog(catalog);
      setModelProfile(current => {
        const valid = catalog.profiles.some(p => p.id === current && p.configured && p.available !== false);
        const next = valid ? current : catalog.api_default_id || catalog.local_default_id;
        for (const modeName of ['local', 'api'] as const) {
          try {
            const saved = localStorage.getItem(`nori-model-profile-${modeName}`) || '';
            if (catalog.profiles.some(p => p.id === saved && p.mode === modeName && p.configured && p.available !== false)) lastModelProfiles.current[modeName] = saved;
          } catch { /* Storage may be disabled. */ }
        }
        const profile = catalog.profiles.find(p => p.id === next);
        if (profile) lastModelProfiles.current[profile.mode] = next;
        try { localStorage.setItem('nori-model-profile', next); } catch { /* Storage may be disabled. */ }
        return next;
      });
    }).catch(() => { if (alive) setError('Chưa tải được danh sách mô hình. Hãy kiểm tra backend và tải lại trang.'); });
    void check(); const interval = setInterval(check, 30000);
    request<(string | null)[]>('/api/workspaces').then(v => { if (alive) { setTenants(v); setTenant(current => v.some(t => (t || '') === current) ? current : v.includes('minh_an_demo') ? 'minh_an_demo' : ''); } }).catch(() => {});
    return () => { alive = false; clearInterval(interval); };
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    const load = async () => {
      try {
        const [d, c] = await Promise.all([request<Document[]>(`/api/documents${workspace(tenant)}`, { signal: controller.signal }), request<Conversation[]>(`/api/conversations${workspace(tenant)}`, { signal: controller.signal })]);
        setDocs(d); setChats(c);
      } catch (e) { if (!controller.signal.aborted) setError(e instanceof Error ? e.message : 'Không kết nối được backend.'); }
    };
    void load(); const interval = setInterval(load, 6000);
    return () => { controller.abort(); clearInterval(interval); };
  }, [tenant]);
  useEffect(() => { bottom.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, busy]);
  useEffect(() => { if (!notice) return; const timeout = setTimeout(() => setNotice(''), 4500); return () => clearTimeout(timeout); }, [notice]);
  const refresh = async () => { const [d, c] = await Promise.all([request<Document[]>(`/api/documents${workspace(tenant)}`), request<Conversation[]>(`/api/conversations${workspace(tenant)}`)]); setDocs(d); setChats(c); };
  const newChat = () => { if (pending) return; generation.current++; setActive(null); setMessages([]); setDraft(''); setSourceMessage(null); setError(''); setView('chat'); setMobile(false); input.current?.focus(); };
  const openChat = async (id: string) => {
    if (pending) return;
    const epoch = ++generation.current; setLoading(true); setError('');
    try { const c = await request<Conversation>(`/api/conversations/${id}${workspace(tenant)}`); if (epoch === generation.current) { setActive(id); setMessages(c.messages || []); setView('chat'); setSourceMessage(null); setMobile(false); } }
    catch (e) { setError(e instanceof Error ? e.message : 'Không mở được hội thoại.'); }
    finally { setLoading(false); }
  };
  const changeModel = (id: string) => {
    if (pending || id === modelProfile) return;
    const profile = modelCatalog?.profiles.find(p => p.id === id);
    if (!profile?.configured || profile.available === false) return;
    newChat(); setModelProfile(id); lastModelProfiles.current[profile.mode] = id;
    try { localStorage.setItem('nori-model-profile', id); localStorage.setItem(`nori-model-profile-${profile.mode}`, id); } catch { /* Storage may be disabled. */ }
  };
  const changeExecution = (next: 'local' | 'api') => {
    const id = lastModelProfiles.current[next] || (next === 'local' ? modelCatalog?.local_default_id : modelCatalog?.api_default_id);
    if (id) changeModel(id);
  };
  const send = async (text = draft) => {
    const question = text.trim(); if (!question || pending || sendLock.current || !selectedModel?.configured) return;
    sendLock.current = true; const epoch = generation.current;
    const previous = messages; setMessages([...previous, { id: crypto.randomUUID(), role: 'user', text: question }]); setDraft(''); setBusy(true); setError(''); setView('chat');
    try {
      const data = await request<{ answer: string; sources: Source[]; thought_process: string[]; conversation_id: string; failure_reason?: string | null }>('/api/query', { method: 'POST', signal: AbortSignal.timeout(executionMode === 'api' ? 430000 : 250000), body: JSON.stringify({ query: question, tenant_id: tenant || null, conversation_id: active, mode, model_profile: modelProfile }) });
      if (epoch === generation.current) { setActive(data.conversation_id); if (data.failure_reason) setNotice(data.failure_reason + ' Có thể chọn provider khác.'); setMessages(prev => [...prev, { id: crypto.randomUUID(), role: 'assistant', text: data.answer, sources: data.sources, steps: data.thought_process }]); void refresh().catch(() => setNotice('Câu trả lời đã lưu. Chưa tải lại được danh sách hội thoại.')); }
    } catch (e) { if (epoch === generation.current) { setMessages(previous); setDraft(question); setError(e instanceof Error ? e.message : 'Không nhận được câu trả lời.'); } }
    finally { setBusy(false); sendLock.current = false; input.current?.focus(); }
  };
  const upload = async (f: File) => {
    if (pending) return;
    if (!/\.(txt|md)$/i.test(f.name)) { setError('Hãy chọn tệp văn bản .txt hoặc .md.'); return; }
    if (f.size > 1000000) { setError('Tệp vượt quá giới hạn 1 MB.'); return; }
    setUploading(true); setError('');
    try {
      const content = await f.text(); if (!content.trim() || content.includes('\u0000')) throw new Error('Tệp rỗng hoặc không phải văn bản UTF-8.');
      await request('/api/ingest', { method: 'POST', body: JSON.stringify({ title: f.name, content, metadata: { tenant_id: tenant || null } }) });
      await refresh(); setNotice(`Đã lưu ${f.name}. Đang tạo chỉ mục vector và đồ thị.`);
    } catch (e) { setError(e instanceof Error ? e.message : 'Không tải được tài liệu.'); }
    finally { setUploading(false); if (file.current) file.current.value = ''; }
  };
  const remove = async () => {
    if (!confirm || pending) return; setLoading(true);
    try { await request(`/api/${confirm.kind === 'chat' ? 'conversations' : 'documents'}/${confirm.id}${workspace(tenant)}`, { method: 'DELETE' }); if (confirm.kind === 'chat' && active === confirm.id) { setActive(null); setMessages([]); } setConfirm(null); await refresh(); setNotice('Đã xóa.'); }
    catch (e) { setError(e instanceof Error ? e.message : 'Không xóa được.'); setConfirm(null); }
    finally { setLoading(false); }
  };
  const copy = async (m: Message) => { try { await navigator.clipboard.writeText(m.text); setCopied(m.id); setTimeout(() => setCopied(null), 1800); } catch { setError('Trình duyệt chưa cho phép sao chép.'); } };
  const prompts = docs.length ? [ { title: 'Tóm tắt tài liệu', detail: 'Nắm bắt những ý chính', icon: FileText, query: `Tóm tắt những nội dung chính của tài liệu ${docs[0].title}` }, { title: 'Khám phá kiến thức', detail: 'Đi sâu vào điều bạn quan tâm', icon: Sparkles, query: `Các khái niệm quan trọng trong tài liệu ${docs[0].title} là gì?` }, { title: 'Kết nối thông tin', detail: 'Tìm các mối liên hệ', icon: BookOpen, query: `Phân tích các mối quan hệ được đề cập trong tài liệu ${docs[0].title}` } ] : [];
  return <div className="app-shell">
    {mobile && <button className="scrim" onClick={() => setMobile(false)} aria-label="Đóng thanh bên"/>}
    <aside className={`sidebar ${mobile ? 'mobile-open' : ''}`}>
      <div className="brand"><button className="brand-name" onClick={newChat}><Mark small/><span>nori<span className="brand-dot">.</span></span></button><button className="icon sidebar-close" onClick={() => setMobile(false)} aria-label="Đóng thanh bên"><PanelLeftClose size={18}/></button></div>
      <button className="new-chat" onClick={newChat} disabled={pending}><Plus size={18}/>Cuộc trò chuyện mới<span className="shortcut">＋</span></button>
      <nav><button className={view === 'chat' ? 'nav-item selected' : 'nav-item'} onClick={() => { setView('chat'); setMobile(false); }}><MessageSquare size={18}/>Trò chuyện</button><button className={view === 'library' ? 'nav-item selected' : 'nav-item'} onClick={() => { setView('library'); setMobile(false); }}><FolderOpen size={18}/>Thư viện tài liệu<span className="count">{docs.length}</span></button></nav>
      <div className="history-label">GẦN ĐÂY <span>{chats.length}</span></div>
      <div className="history">{chats.length ? chats.map(c => <div key={c.id} className={`history-row ${active === c.id ? 'active' : ''}`}><button onClick={() => void openChat(c.id)} disabled={pending}><MessageSquare size={15}/><span>{c.title}</span></button><button className="delete-chat icon" onClick={() => setConfirm({ kind: 'chat', id: c.id, title: c.title })} disabled={pending} aria-label={`Xóa hội thoại ${c.title}`}><Trash2 size={14}/></button></div>) : <p className="history-empty">Một ý tưởng hay bắt đầu<br/>từ một câu hỏi.</p>}</div>
      <div className="sidebar-bottom"><div className="workspace-card"><span className="workspace-icon"><Leaf size={18}/></span><div><strong>Không gian của bạn</strong><span>Kiến thức, ở ngay đây.</span></div><span className={`connection-dot ${health?.services.postgres ? 'online' : ''}`}/></div><button className="profile" onClick={() => setSettings(true)}><span className="avatar">B</span><div><strong>Bạn</strong><span>Không gian cá nhân</span></div><Settings2 size={17}/></button></div>
    </aside>
    <main className="main">
      <header className="topbar"><div className="topbar-left"><button className="icon mobile-menu" onClick={() => setMobile(true)} aria-label="Mở thanh bên"><Menu size={20}/></button><span className="product-name">Nori</span><span className="topbar-divider">/</span><label className="workspace-select"><select aria-label="Chọn không gian tài liệu" value={tenant} disabled={pending} onChange={e => { generation.current++; setTenant(e.target.value); try { localStorage.setItem('nori-workspace', e.target.value); } catch { /* Storage may be disabled. */ } setDocs([]); setChats([]); setMessages([]); setActive(null); setSourceMessage(null); setError(''); }}>{tenants.map(t => <option key={t || 'global'} value={t || ''}>{workspaceName(t || '')}</option>)}</select><ChevronDown size={14}/></label></div><div className="topbar-actions"><span className={`local-status ${health?.services.llm && health.services.postgres ? '' : 'offline'}`}><span className="connection-dot online"/>{executionMode === 'api' ? selectedModel?.configured ? 'API · Đã cấu hình' : 'API · Chưa cấu hình' : health?.services.llm && health.services.postgres ? 'Local · Đã kết nối' : 'Local · Chưa sẵn sàng'}</span><button className="icon" onClick={() => setDark(!dark)} aria-label={dark ? 'Bật giao diện sáng' : 'Bật giao diện tối'}>{dark ? <Sun size={18}/> : <Moon size={18}/>}</button></div></header>
      <input type="file" hidden ref={file} accept=".txt,.md" onChange={e => { if (e.target.files?.[0]) void upload(e.target.files[0]); }}/>
      {(error || notice) && <div className={`toast ${error ? 'error' : ''}`} role={error ? 'alert' : 'status'}><span>{error || notice}</span><button className="icon" onClick={() => { setError(''); setNotice(''); }} aria-label="Đóng thông báo"><X size={16}/></button></div>}
      {view === 'library' ? <section className="library" onDragOver={e => e.preventDefault()} onDrop={e => { e.preventDefault(); if (e.dataTransfer.files[0]) void upload(e.dataTransfer.files[0]); }}><div className="page-eyebrow"><FolderOpen size={16}/>KIẾN THỨC CỦA BẠN</div><div className="library-heading"><div><h1>Thư viện tài liệu<span>.</span></h1><p>{workspaceName(tenant)} · {docs.length} tài liệu trong không gian này.</p></div><button className="primary-button" disabled={pending} onClick={() => file.current?.click()}>{uploading ? <LoaderCircle className="spin" size={17}/> : <Plus size={17}/>}Thêm tài liệu</button></div><label className="search-field"><Search size={18}/><input value={search} onChange={e => setSearch(e.target.value)} placeholder="Tìm trong thư viện…" aria-label="Tìm tài liệu"/></label><div className="document-list">{docs.filter(d => d.title.toLowerCase().includes(search.toLowerCase())).map(d => <article className="document-row" key={d.id}><span className="document-icon"><FileText size={22}/></span><button className="document-info" onClick={() => setPreview(d)}><strong>{d.title}</strong><span>{d.characters.toLocaleString('vi-VN')} ký tự · {new Date(d.created_at).toLocaleDateString('vi-VN')}</span></button><span className={`document-status ${d.metadata?.status === 'processing' ? 'processing' : ''}`}>{d.metadata?.status === 'processing' ? 'Đang lập chỉ mục' : d.metadata?.status === 'text_only' ? 'Tìm kiếm văn bản' : 'Sẵn sàng'}</span><button className="icon" disabled={pending} onClick={() => setConfirm({ kind: 'document', id: d.id, title: d.title })} aria-label={`Xóa tài liệu ${d.title}`}><Trash2 size={17}/></button></article>)}</div>{!docs.length && <div className="empty-library"><BookOpen size={36}/><h2>Góc kiến thức đang chờ bạn.</h2><p>Thả một tệp .txt hoặc .md vào đây để bắt đầu.</p></div>}{docs.length > 0 && search && !docs.some(d => d.title.toLowerCase().includes(search.toLowerCase())) && <p className="no-results">Không có tài liệu phù hợp.</p>}<div className="upload-note"><Upload size={16}/>Kéo thả tệp vào đây · TXT, Markdown · Tối đa 1 MB</div></section> : <>
      <section className={`chat-scroll ${messages.length ? 'has-messages' : ''}`}>
        {!messages.length && !loading ? <div className="welcome"><div className="welcome-mark"><Mark/></div><div className="eyebrow">MỘT CHÚT TÒ MÒ. THẬT NHIỀU KHẢ NĂNG.</div><h1>Chào bạn,<br/>hôm nay ta khám phá gì<span>?</span></h1><p>Hỏi, tìm hiểu và kết nối những điều bạn biết.<br/>Nori cùng bạn tìm câu trả lời từ tài liệu của mình.</p><div className="suggestions">{prompts.map(p => <button key={p.title} disabled={pending} onClick={() => void send(p.query)}><div className="suggestion-top"><p.icon size={20}/><ArrowUpRight size={15}/></div><strong>{p.title}</strong><span>{p.detail}</span></button>)}{!docs.length && <button className="first-upload" disabled={pending} onClick={() => file.current?.click()}><Upload size={20}/><strong>Thêm tài liệu đầu tiên</strong><span>Bắt đầu từ kiến thức của bạn</span></button>}</div><button className="welcome-library" onClick={() => setView('library')}><span className="mini-files"><FileText size={14}/></span>{docs.length ? `${docs.length} tài liệu trong không gian này` : 'Thư viện của bạn đang trống'}<ChevronRight size={14}/></button></div> : <div className="message-list">{messages.map(m => <article className={`message ${m.role}`} key={m.id}>{m.role === 'assistant' && <div className="assistant-heading"><Mark small/><strong>Nori</strong></div>}<div className="message-body"><RichText text={m.text} onSource={() => setSourceMessage(m)}/></div>{m.role === 'assistant' && <div className="message-tools">{!!m.sources?.length && <button className="source-button" onClick={() => setSourceMessage(m)}><BookOpen size={14}/>{m.sources.length} nguồn tham khảo<ChevronRight size={14}/></button>}<button className="icon" onClick={() => void copy(m)} aria-label="Sao chép câu trả lời">{copied === m.id ? <Check size={15}/> : <Copy size={15}/>}</button>{!!m.steps?.length && <details className="steps"><summary>Quá trình xử lý</summary><ol>{m.steps.map((step, i) => <li key={i}>{step}</li>)}</ol></details>}</div>}</article>)}{busy && <div className="thinking" role="status"><Mark small/><span>Nori đang tìm và tổng hợp thông tin</span><span className="thinking-dots"><i/><i/><i/></span></div>}{loading && <div className="thinking" role="status"><LoaderCircle className="spin" size={18}/>Đang mở hội thoại…</div>}<div ref={bottom}/></div>}
      </section>
      <div className="composer-wrap"><div className="model-controls"><div className="execution-toggle" role="group" aria-label="Chọn hướng chạy"><button type="button" className={executionMode === 'local' ? 'selected' : ''} disabled={pending || !modelCatalog} onClick={() => changeExecution('local')}>Local</button><button type="button" className={executionMode === 'api' ? 'selected' : ''} disabled={pending || !modelCatalog?.api_default_id} onClick={() => changeExecution('api')}>API</button></div><label className="model-picker"><select aria-label="Chọn mô hình" value={modelProfile} disabled={pending || !modelCatalog} onChange={e => changeModel(e.target.value)}>{!modelCatalog && <option value="">Đang tải mô hình…</option>}{Array.from(new Set(modelCatalog?.profiles.filter(p => p.mode === executionMode).map(p => p.label))).map(label => <optgroup key={label} label={label}>{modelCatalog?.profiles.filter(p => p.mode === executionMode && p.label === label).map(p => <option key={p.id} value={p.id} disabled={!p.configured || p.available === false}>{p.model}{!p.configured ? ' · chưa có khóa' : p.available === false ? ' · không còn trong danh sách' : p.available === null ? ' · chưa xác minh' : ''}</option>)}</optgroup>)}</select><ChevronDown size={13}/></label></div><form className="composer" onSubmit={e => { e.preventDefault(); void send(); }}><textarea ref={input} value={draft} maxLength={8000} onChange={e => setDraft(e.target.value)} placeholder="Hỏi Nori bất cứ điều gì từ tài liệu của bạn…" aria-label="Nhập câu hỏi" rows={2} disabled={pending} onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); void send(); } }}/><div className="composer-toolbar"><div className="composer-options"><button type="button" className="icon attach" onClick={() => file.current?.click()} disabled={pending} aria-label="Đính kèm tài liệu">{uploading ? <LoaderCircle className="spin" size={18}/> : <Paperclip size={19}/>}</button><span className="toolbar-divider"/><label className="mode-select"><Sparkles size={14}/><select value={mode} disabled={pending} onChange={e => setMode(e.target.value)} aria-label="Chế độ truy xuất"><option value="hybrid">Tìm kiếm kết hợp</option><option value="documents">Chỉ tài liệu</option></select><ChevronDown size={13}/></label></div><button className="send-button" type="submit" disabled={!draft.trim() || pending || !selectedModel?.configured} aria-label="Gửi câu hỏi">{busy ? <LoaderCircle size={19} className="spin"/> : <ArrowUp size={20}/>}</button></div></form><div className="composer-footer"><span>Nori có thể mắc lỗi. Hãy kiểm tra các nguồn tham khảo.</span><button onClick={() => setSettings(true)}><span className={`connection-dot ${health?.services.llm ? 'online' : ''}`}/>{selectedModel ? `${selectedModel.label} · ${selectedModel.model}` : 'Đang tải mô hình'}<ChevronDown size={11}/></button></div></div>
      </>}
    </main>
    {sourceMessage && <Dialog title="Nguồn tham khảo" close={() => setSourceMessage(null)}><p className="dialog-description">Các đoạn thông tin được truy xuất cho câu trả lời này.</p><div className="sources-list">{sourceMessage.sources?.map((s, i) => <article key={i}><div className="source-title"><span>{i+1}</span><strong>{s.title}</strong><small>{s.source_type === 'graph' ? 'Neo4j' : s.source_type === 'vector' ? 'pgvector' : 'Văn bản'}</small></div><p>{s.content || s.context_string}</p></article>)}</div></Dialog>}
    {preview && <Dialog title={preview.title} close={() => setPreview(null)}><p className="dialog-description">Nội dung tài liệu đã lưu trong PostgreSQL.</p><pre className="document-preview">{preview.content}</pre></Dialog>}
    {settings && <Dialog title="Không gian của Nori" close={() => setSettings(false)}><p className="dialog-description">Kết nối với dữ liệu và mô hình của dự án.</p><div className="settings-section"><h3>Giao diện</h3><div className="theme-options"><button className={!dark ? 'chosen' : ''} onClick={() => setDark(false)}><Sun size={19}/>Sáng{!dark && <Check size={16}/>}</button><button className={dark ? 'chosen' : ''} onClick={() => setDark(true)}><Moon size={19}/>Tối{dark && <Check size={16}/>}</button></div></div><div className="settings-section"><h3>Kết nối hệ thống</h3>{[['PostgreSQL · tài liệu & hội thoại', health?.services.postgres], ['Neo4j · đồ thị tri thức', health?.services.neo4j], [`${health?.provider || 'Mô hình'} · ${health?.model || 'chưa kết nối'}`, health?.services.llm]].map(([label, status]) => <div className="service-row" key={String(label)}><span>{label}</span><span className={status ? 'service-ready' : 'service-offline'}>{status ? 'Sẵn sàng' : 'Chưa kết nối'}</span></div>)}</div><div className="settings-note"><Leaf size={18}/><p>{executionMode === 'api' ? 'Hướng API dùng mô hình đã chọn từ cấu hình Hermes. Các đoạn tài liệu truy xuất được gửi đến provider đó.' : 'Hướng Local dùng Ollama trên máy này. Bước tổng hợp và kiểm chứng chạy tại máy.'} Tài liệu và hội thoại vẫn lưu trong PostgreSQL; dịch vụ embedding giữ cấu hình hiện tại.</p></div></Dialog>}
    {confirm && <Dialog title="Xóa nội dung này?" close={() => setConfirm(null)}><p className="dialog-description">“{confirm.title}” sẽ được xóa khỏi không gian hiện tại. Thao tác này không thể hoàn tác.</p><div className="confirm-actions"><button className="secondary-button" disabled={loading} onClick={() => setConfirm(null)}>Giữ lại</button><button className="danger-button" disabled={loading} onClick={() => void remove()}>{loading ? 'Đang xóa…' : 'Xóa'}</button></div></Dialog>}
  </div>;
}
