import React, { useEffect, useState } from 'react';

interface ThoughtProcessProps {
  thoughts: string[];
}

export const ThoughtProcess: React.FC<ThoughtProcessProps> = ({ thoughts }) => {
  const [visibleThoughts, setVisibleThoughts] = useState<string[]>([]);

  useEffect(() => {
    if (thoughts.length === 0) {
      setVisibleThoughts([]);
      return;
    }

    setVisibleThoughts([]);
    thoughts.forEach((thought, idx) => {
      setTimeout(() => {
        setVisibleThoughts((prev) => [...prev, thought]);
      }, idx * 600); // 600ms stagger delay
    });
  }, [thoughts]);

  const parseThought = (thought: string) => {
    if (thought.includes('->')) {
      const parts = thought.split('->');
      return {
        title: parts[0].trim(),
        desc: parts.slice(1).join(' -> ').trim()
      };
    }
    return { title: 'Agent Step', desc: thought };
  };

  const getStepColor = (title: string) => {
    const lower = title.toLowerCase();
    if (lower.includes('phân tích') || lower.includes('routing')) return 'bg-secondary cyan-glow';
    if (lower.includes('tìm thấy') || lower.includes('truy xuất') || lower.includes('retrieval')) return 'bg-tertiary emerald-glow';
    if (lower.includes('đánh giá') || lower.includes('critic') || lower.includes('hợp lệ: true')) return 'bg-emerald-400 emerald-glow';
    if (lower.includes('vòng') || lower.includes('dự thảo')) return 'bg-amber-400';
    return 'bg-secondary';
  };

  return (
    <div className="flex-1 flex flex-col gap-4 overflow-hidden">
      <h3 className="font-label-md text-label-md font-semibold text-secondary flex items-center gap-2">
        <span className="material-symbols-outlined text-sm">psychology</span>
        AGENT THOUGHT PROCESS
      </h3>
      <div className="flex-1 overflow-y-auto pr-2 flex flex-col gap-6 relative">
        <div className="absolute left-2.5 top-2 bottom-2 w-px bg-white/10"></div>

        {visibleThoughts.length === 0 ? (
          <div className="text-on-surface-variant/40 text-center font-label-md mt-10">
            Chưa thực thi truy vấn nào.
          </div>
        ) : (
          visibleThoughts.map((thought, idx) => {
            const { title, desc } = parseThought(thought);
            const dotColor = getStepColor(title);
            return (
              <div
                key={idx}
                className="relative flex gap-4 pl-8 transition-all duration-500 transform translate-x-0 opacity-100 animate-in fade-in slide-in-from-left-4"
              >
                <div className={`absolute left-1 top-1 w-3 h-3 rounded-full z-10 ${dotColor}`}></div>
                <div className="flex flex-col">
                  <span className="font-label-md text-label-md font-medium text-secondary">
                    {title}
                  </span>
                  <span className="font-code-sm text-code-sm text-on-surface-variant leading-relaxed">
                    {desc}
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
