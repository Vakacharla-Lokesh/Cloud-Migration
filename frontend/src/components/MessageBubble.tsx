import { ArtifactCard } from "./ArtifactCard";
import { HITLCard } from "./HITLCard";
import { StepsCard } from "./StepsCard";
import type { Conversation, Message } from "../types";

interface Props {
  message: Message;
  conv: Conversation;
  onDecide: (sessionId: string, decision: "approve" | "reject", feedback?: string) => void;
}

export function MessageBubble({ message, conv, onDecide }: Props) {
  const isUser = message.role === "user";

  if (message.kind === "steps") {
    return (
      <div className="w-full max-w-2xl">
        <StepsCard
          steps={message.steps ?? []}
          isRunning={conv.status === "running"}
        />
      </div>
    );
  }

  if (message.kind === "artifact") {
    return (
      <div className="w-full max-w-2xl">
        <ArtifactCard
          iac={message.iac ?? ""}
          iacPath={message.iacPath ?? ""}
          sessionId={message.sessionId ?? conv.sessionId ?? ""}
        />
      </div>
    );
  }

  if (message.kind === "hitl") {
    return (
      <div className="w-full max-w-2xl">
        <HITLCard
          sessionId={message.sessionId ?? conv.sessionId ?? ""}
          awaitingDecision={message.awaitingDecision ?? false}
          onDecide={onDecide}
        />
      </div>
    );
  }

  if (message.kind === "error") {
    return (
      <div className="w-full max-w-2xl animate-slide-up">
        <div className="rounded-lg border border-rose-400/40 bg-rose-400/5 px-4 py-3">
          <div className="flex items-center gap-2 mb-1">
            <div className="w-1.5 h-1.5 rounded-full bg-rose-400" />
            <span className="font-mono text-xs text-rose-400 tracking-wide">Error</span>
          </div>
          <p className="font-mono text-xs text-rose-300 break-words">{message.content}</p>
        </div>
      </div>
    );
  }

  // Plain text — user or agent
  return (
    <div
      className={`animate-slide-up ${
        isUser ? "flex justify-end w-full" : "w-full max-w-2xl"
      }`}
    >
      {isUser ? (
        // User bubble
        <div
          className="max-w-lg px-4 py-2.5 rounded-2xl rounded-br-sm
                     bg-amber-400/10 border border-amber-400/25
                     font-sans text-sm text-base-100 leading-relaxed"
        >
          {message.content}
        </div>
      ) : (
        // Agent text
        <div className="font-sans text-sm text-base-200 leading-relaxed px-1">
          {message.content}
        </div>
      )}
    </div>
  );
}
