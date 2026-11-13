import type { Conversation } from "../types";

interface Props {
  conversations: Conversation[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
}

const statusDot: Record<Conversation["status"], string> = {
  idle: "bg-base-500",
  running: "bg-amber-400 animate-pulse-dot",
  awaiting_human: "bg-sky-400 animate-pulse-dot",
  completed: "bg-emerald-400",
  failed: "bg-rose-400",
};

function formatTime(ts: number) {
  const d = new Date(ts);
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export function Sidebar({ conversations, activeId, onSelect, onNew }: Props) {
  return (
    <aside className="flex flex-col w-64 shrink-0 h-full bg-base-900 border-r border-base-700">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-4 border-b border-base-700">
        <div>
          <div className="font-mono text-xs text-amber-400 tracking-widest uppercase">
            Migration
          </div>
          <div className="font-sans font-semibold text-base-100 text-sm mt-0.5">
            Agent
          </div>
        </div>

        {/* AWS icon badge */}
        <div className="w-8 h-8 rounded bg-amber-400/10 border border-amber-400/30 flex items-center justify-center">
          <svg className="w-4 h-4 text-amber-400" viewBox="0 0 24 24" fill="currentColor">
            <path d="M6.763 10.036c0 .296.032.535.088.71.064.176.144.368.256.576.04.072.056.144.056.208 0 .096-.056.192-.176.288l-.584.392a.44.44 0 0 1-.24.08c-.096 0-.192-.048-.288-.136a2.964 2.964 0 0 1-.344-.448 7.408 7.408 0 0 1-.296-.56c-.744.88-1.68 1.32-2.808 1.32-.8 0-1.44-.224-1.912-.672-.472-.448-.712-1.048-.712-1.8 0-.8.28-1.448.848-1.936.568-.488 1.32-.736 2.272-.736.312 0 .64.024.984.08.344.056.696.136 1.064.232v-.672c0-.704-.144-1.192-.432-1.48-.296-.288-.8-.424-1.52-.424-.328 0-.664.04-1.008.128-.344.088-.68.2-1.008.344-.152.064-.264.104-.32.12a.552.552 0 0 1-.144.024c-.128 0-.192-.096-.192-.296v-.464c0-.152.016-.272.056-.336a.6.6 0 0 1 .224-.192 5.272 5.272 0 0 1 1.192-.424 5.76 5.76 0 0 1 1.472-.184c1.12 0 1.936.256 2.456.768.512.512.776 1.288.776 2.328v3.064zm-3.872 1.448c.304 0 .616-.056.944-.168.328-.112.616-.32.864-.6.144-.176.256-.368.312-.584.056-.216.088-.472.088-.776v-.376a7.6 7.6 0 0 0-.856-.16 6.912 6.912 0 0 0-.88-.056c-.624 0-1.08.12-1.384.368-.304.248-.456.6-.456 1.064 0 .432.112.76.344.984.224.216.544.304.952.304zm7.44.984c-.168 0-.28-.032-.352-.096-.072-.056-.136-.184-.192-.36l-2.136-7.032c-.056-.184-.088-.304-.088-.368 0-.144.072-.224.216-.224h.88c.176 0 .296.032.36.096.072.056.128.184.184.36l1.528 6.016 1.416-6.016c.048-.184.104-.304.176-.36.072-.064.2-.096.368-.096h.72c.176 0 .296.032.368.096.064.056.128.184.168.36l1.432 6.096 1.576-6.096c.056-.184.12-.304.192-.36.072-.064.192-.096.352-.096h.832c.144 0 .224.072.224.224 0 .04-.008.088-.024.144a1.232 1.232 0 0 1-.072.232l-2.192 7.032c-.056.184-.12.304-.192.36-.072.056-.184.096-.352.096h-.776c-.176 0-.296-.032-.368-.096-.072-.072-.136-.192-.176-.368l-1.408-5.864-1.4 5.856c-.048.184-.104.304-.176.368-.072.064-.2.096-.368.096zm11.672.248c-.48 0-.96-.056-1.424-.168a4.2 4.2 0 0 1-1.088-.408.68.68 0 0 1-.24-.232.6.6 0 0 1-.056-.264v-.48c0-.2.072-.296.216-.296.056 0 .112.008.168.032.056.016.136.056.232.096.312.136.648.248 1 .32.36.072.712.112 1.072.112.568 0 1.016-.104 1.328-.304.312-.2.472-.496.472-.88 0-.256-.08-.472-.248-.64-.168-.168-.48-.32-.944-.464l-1.352-.424c-.688-.216-1.192-.528-1.512-.952a2.272 2.272 0 0 1-.472-1.368c0-.392.088-.744.264-1.04.176-.296.408-.552.712-.76.296-.208.632-.36 1.016-.464.384-.104.784-.152 1.2-.152.208 0 .424.016.632.04.216.032.408.072.6.12.184.04.36.096.52.152.16.056.288.112.376.168a.76.76 0 0 1 .272.232.56.56 0 0 1 .08.304v.448c0 .2-.072.304-.208.304a.944.944 0 0 1-.344-.104 4.112 4.112 0 0 0-1.712-.352c-.52 0-.928.088-1.208.272-.28.184-.424.464-.424.848 0 .264.088.488.272.664.184.176.52.352 1.008.504l1.328.424c.68.216 1.168.52 1.464.912.296.392.44.84.44 1.336 0 .4-.08.76-.248 1.072-.168.312-.4.584-.704.808a3.12 3.12 0 0 1-1.064.496 4.728 4.728 0 0 1-1.336.192z" />
          </svg>
        </div>
      </div>

      {/* New chat button */}
      <div className="px-3 py-3 border-b border-base-700">
        <button
          onClick={onNew}
          className="w-full flex items-center gap-2 px-3 py-2 rounded
                     bg-amber-400/10 hover:bg-amber-400/20 border border-amber-400/30
                     hover:border-amber-400/60 text-amber-400 font-mono text-xs
                     tracking-wide transition-all duration-150 group"
        >
          <span className="text-base leading-none group-hover:rotate-90 transition-transform duration-200">
            +
          </span>
          <span>New Migration</span>
        </button>
      </div>

      {/* Conversation list */}
      <nav className="flex-1 overflow-y-auto scrollbar-thin py-2">
        {conversations.length === 0 && (
          <div className="px-4 py-6 text-center">
            <div className="text-base-500 text-xs font-mono">No sessions yet</div>
          </div>
        )}

        {conversations.map((conv) => (
          <button
            key={conv.id}
            onClick={() => onSelect(conv.id)}
            className={`
              w-full text-left px-3 py-2.5 mx-1 rounded
              flex items-start gap-2.5 transition-all duration-100
              ${
                conv.id === activeId
                  ? "bg-base-700 text-base-100"
                  : "hover:bg-base-800 text-base-300 hover:text-base-100"
              }
            `}
            style={{ width: "calc(100% - 8px)" }}
          >
            {/* Status dot */}
            <span
              className={`mt-1.5 w-1.5 h-1.5 rounded-full shrink-0 ${statusDot[conv.status]}`}
            />

            <div className="min-w-0 flex-1">
              <div className="font-sans text-xs font-medium truncate leading-snug">
                {conv.title}
              </div>
              <div className="font-mono text-[10px] text-base-500 mt-0.5">
                {formatTime(conv.createdAt)} · {conv.messages.length} msg
              </div>
            </div>
          </button>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-base-700">
        <div className="font-mono text-[10px] text-base-500 tracking-wide">
          v0.1.0 · Phase 1
        </div>
      </div>
    </aside>
  );
}
