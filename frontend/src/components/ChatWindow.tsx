import React, { useState, useRef, useEffect } from 'react';
import { marked } from 'marked';

interface Message {
  role: 'user' | 'assistant';
  text: string;
  sources?: any[];
  latency?: number;
}

interface ChatWindowProps {
  messages: Message[];
  onSendMessage: (text: string) => void;
  isQuerying: boolean;
  latency: number | string;
  onAttachClick: () => void;
}

export const ChatWindow: React.FC<ChatWindowProps> = ({
  messages,
  onSendMessage,
  isQuerying,
  latency,
  onAttachClick
}) => {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom of chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isQuerying]);

  // Auto-resize input textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`;
    }
  }, [input]);

  const handleSend = () => {
    if (!input.trim() || isQuerying) return;
    onSendMessage(input.trim());
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Helper to safely render Markdown
  const renderMarkdown = (text: string) => {
    try {
      const html = marked.parse(text) as string;
      return { __html: html };
    } catch (e) {
      return { __html: text };
    }
  };

  return (
    <section className="flex-1 flex flex-col h-[calc(100vh-64px)] relative bg-surface-container/20">
      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-8 space-y-8">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
            {msg.role === 'assistant' && (
              <div className="flex items-center gap-3 mb-2">
                <div className="w-6 h-6 rounded-md bg-secondary flex items-center justify-center">
                  <span className="material-symbols-outlined text-on-secondary text-[16px]" style={{ fontVariationSettings: "'FILL' 1" }}>
                    auto_awesome
                  </span>
                </div>
                <span className="font-label-md text-label-md font-bold text-secondary">Aetheris Agent</span>
              </div>
            )}
            
            <div
              className={`max-w-[85%] p-5 rounded-2xl ${
                msg.role === 'user'
                  ? 'rounded-tr-none bg-secondary/10 border border-secondary/20 text-on-surface shadow-sm'
                  : 'rounded-tl-none glass-panel text-on-surface leading-relaxed'
              }`}
            >
              {msg.role === 'user' ? (
                <p className="whitespace-pre-wrap text-sm">{msg.text}</p>
              ) : (
                <div 
                  className="prose prose-invert max-w-none text-on-surface text-sm leading-relaxed space-y-2"
                  dangerouslySetInnerHTML={renderMarkdown(msg.text)} 
                />
              )}

              {/* Source Citations */}
              {msg.sources && msg.sources.length > 0 && (
                <div className="pt-4 mt-4 border-t border-white/10 flex flex-wrap gap-2">
                  {msg.sources.map((src, sIdx) => {
                    const isVector = src.source_type === 'vector';
                    return (
                      <div
                        key={sIdx}
                        className="source-chip flex items-center gap-2 px-3 py-1.5 rounded-full cursor-pointer hover:scale-105 transition-all text-[11px] text-on-tertiary-container font-code-sm"
                        title={isVector ? src.title : src.fact}
                      >
                        <span className="material-symbols-outlined text-[14px] text-tertiary">
                          {isVector ? 'database' : 'hub'}
                        </span>
                        <span>
                          {isVector 
                            ? `Postgres: ${src.title.length > 15 ? src.title.slice(0, 15) + '...' : src.title}`
                            : `Neo4j: ${src.source_node_name || 'Entity'}`}
                        </span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Loading Bubble */}
        {isQuerying && (
          <div className="flex flex-col items-start animate-pulse">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-6 h-6 rounded-md bg-secondary flex items-center justify-center">
                <span className="material-symbols-outlined text-on-secondary text-[16px]" style={{ fontVariationSettings: "'FILL' 1" }}>
                  auto_awesome
                </span>
              </div>
              <span className="font-label-md text-label-md font-bold text-secondary">Aetheris Thinking...</span>
            </div>
            <div className="max-w-[70%] p-6 rounded-2xl rounded-tl-none glass-panel text-on-surface flex items-center gap-2">
              <span className="w-2 h-2 bg-secondary rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
              <span className="w-2 h-2 bg-secondary rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
              <span className="w-2 h-2 bg-secondary rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Form Bar */}
      <div className="p-8">
        <div className="relative max-w-4xl mx-auto">
          <div className="chat-input-container glass-panel rounded-2xl p-2 flex items-end gap-2 border border-secondary/30 focus-within:border-secondary transition-all">
            <button
              onClick={onAttachClick}
              className="p-3 text-on-surface-variant hover:text-secondary transition-colors"
              title="Upload tài liệu"
            >
              <span className="material-symbols-outlined">attach_file</span>
            </button>
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={1}
              className="flex-1 bg-transparent border-none focus:ring-0 text-on-surface font-body-md py-3 resize-none min-h-[56px] placeholder:text-on-surface-variant/40 outline-none"
              placeholder="Ask anything about the workspace documents..."
            />
            <button
              onClick={handleSend}
              disabled={isQuerying || !input.trim()}
              className={`p-3 rounded-xl flex items-center justify-center transition-all ${
                isQuerying || !input.trim()
                  ? 'bg-secondary/20 text-on-secondary/50 cursor-not-allowed'
                  : 'bg-secondary text-on-secondary cyan-glow hover:scale-105 active:scale-95'
              }`}
            >
              <span className="material-symbols-outlined">send</span>
            </button>
          </div>
          
          <div className="mt-2 flex justify-center gap-6">
            <span className="text-[11px] text-on-surface-variant/60 flex items-center gap-1.5 uppercase tracking-widest">
              <span className={`w-1.5 h-1.5 rounded-full ${isQuerying ? 'bg-amber-400' : 'bg-tertiary animate-pulse'}`}></span> 
              {isQuerying ? 'Agent Loop Running' : 'Engine Active'}
            </span>
            <span className="text-[11px] text-on-surface-variant/60 flex items-center gap-1.5 uppercase tracking-widest">
              <span className="material-symbols-outlined text-[12px]">bolt</span> 
              {latency} Latency
            </span>
          </div>
        </div>
      </div>
    </section>
  );
};
