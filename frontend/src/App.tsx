import { useEffect, useRef } from "react";
import { EmptyState } from "./components/EmptyState";
import { MessageBubble } from "./components/MessageBubble";
import { PromptInput } from "./components/PromptInput";
import { Sidebar } from "./components/Sidebar";
import { useConversations } from "./hooks/useConversation";

export default function App() {
  const {
    conversations,
    activeConv,
    newConversation,
    selectConversation,
    sendPrompt,
    sendDecision,
  } = useConversations();

  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [activeConv?.messages.length]);

  const isInputDisabled =
    activeConv?.status === "running" ||
    activeConv?.status === "awaiting_human";

  return (
    <div className="flex h-full bg-base-950">
      {/* Sidebar */}
      <Sidebar
        conversations={conversations}
        activeId={activeConv?.id ?? null}
        onSelect={selectConversation}
        onNew={newConversation}
      />

      {/* Main area */}
      <div className="flex flex-col flex-1 min-w-0 h-full">
        {/* Top bar */}
        <header className="flex items-center justify-between px-6 py-3
                           border-b border-base-700 bg-base-900 shrink-0">
          <div className="flex items-center gap-3">
            {activeConv ? (
              <>
                <span className="font-sans text-sm font-medium text-base-100 truncate max-w-md">
                  {activeConv.title}
                </span>
                {activeConv.sessionId && (
                  <span className="font-mono text-[10px] text-base-500 hidden md:inline">
                    {activeConv.sessionId.slice(0, 8)}
                  </span>
                )}
              </>
            ) : (
              <span className="font-sans text-sm text-base-500">
                Select or start a migration
              </span>
            )}
          </div>

          {/* Status badge */}
          {activeConv && (
            <div
              className={`
                flex items-center gap-1.5 px-2.5 py-1 rounded-full
                font-mono text-[10px] border
                ${
                  activeConv.status === "running"
                    ? "bg-amber-400/10 border-amber-400/30 text-amber-400"
                    : activeConv.status === "awaiting_human"
                    ? "bg-sky-400/10 border-sky-400/30 text-sky-400"
                    : activeConv.status === "completed"
                    ? "bg-emerald-400/10 border-emerald-400/30 text-emerald-400"
                    : activeConv.status === "failed"
                    ? "bg-rose-400/10 border-rose-400/30 text-rose-400"
                    : "bg-base-700 border-base-600 text-base-400"
                }
              `}
            >
              <span
                className={`w-1.5 h-1.5 rounded-full
                  ${
                    activeConv.status === "running"
                      ? "bg-amber-400 animate-pulse-dot"
                      : activeConv.status === "awaiting_human"
                      ? "bg-sky-400 animate-pulse-dot"
                      : activeConv.status === "completed"
                      ? "bg-emerald-400"
                      : activeConv.status === "failed"
                      ? "bg-rose-400"
                      : "bg-base-500"
                  }
                `}
              />
              {activeConv.status}
            </div>
          )}
        </header>

        {/* Messages */}
        <main className="flex-1 overflow-y-auto scrollbar-thin">
          {!activeConv ? (
            <EmptyState onNew={newConversation} />
          ) : activeConv.messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center px-8">
              <div className="font-mono text-xs text-base-500 tracking-wide">
                Type your migration prompt below to begin
              </div>
            </div>
          ) : (
            <div className="px-6 py-6 space-y-4 max-w-3xl mx-auto">
              {activeConv.messages.map((msg: any) => (
                <MessageBubble
                  key={msg.id}
                  message={msg}
                  conv={activeConv}
                  onDecide={sendDecision}
                />
              ))}
              <div ref={bottomRef} />
            </div>
          )}
        </main>

        {/* Input */}
        {activeConv && (
          <PromptInput
            onSubmit={sendPrompt}
            disabled={isInputDisabled}
            placeholder={
              activeConv.status === "awaiting_human"
                ? "Use the approval card above to continue…"
                : undefined
            }
          />
        )}
      </div>
    </div>
  );
}
