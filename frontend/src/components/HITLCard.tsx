import { useState } from "react";

interface Props {
  sessionId: string;
  awaitingDecision: boolean;
  onDecide: (sessionId: string, decision: "approve" | "reject", feedback?: string) => void;
}

export function HITLCard({ sessionId, awaitingDecision, onDecide }: Props) {
  const [mode, setMode] = useState<"idle" | "rejecting">("idle");
  const [feedback, setFeedback] = useState("");

  if (!awaitingDecision) {
    return (
      <div className="rounded-lg border border-base-600 bg-base-800 px-4 py-3 animate-slide-up">
        <span className="font-mono text-xs text-base-400">Decision submitted ✓</span>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-sky-400/40 bg-base-800 overflow-hidden animate-slide-up">
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-2.5 bg-sky-400/5 border-b border-sky-400/20">
        <div className="w-1.5 h-1.5 rounded-full bg-sky-400 animate-pulse-dot" />
        <span className="font-mono text-xs text-sky-400 tracking-wide">
          Human Review Required
        </span>
      </div>

      <div className="px-4 py-3">
        <p className="font-sans text-sm text-base-200 mb-3">
          Review the generated Terraform above. Approve to continue, or reject with feedback to regenerate.
        </p>

        {mode === "rejecting" ? (
          <div className="space-y-2">
            <textarea
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              placeholder="What should be changed? (e.g. add server-side encryption to S3, change IAM policy…)"
              className="w-full bg-base-900 border border-base-600 focus:border-sky-400
                         rounded px-3 py-2 font-mono text-xs text-base-200
                         placeholder:text-base-500 outline-none resize-none
                         transition-colors duration-150"
              rows={3}
              autoFocus
            />
            <div className="flex gap-2">
              <button
                onClick={() => {
                  if (feedback.trim()) {
                    onDecide(sessionId, "reject", feedback.trim());
                  }
                }}
                disabled={!feedback.trim()}
                className="px-3 py-1.5 rounded bg-rose-400/10 hover:bg-rose-400/20
                           border border-rose-400/40 hover:border-rose-400/70
                           text-rose-400 font-mono text-xs transition-all duration-150
                           disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Submit Feedback
              </button>
              <button
                onClick={() => { setMode("idle"); setFeedback(""); }}
                className="px-3 py-1.5 rounded bg-base-700 hover:bg-base-600
                           border border-base-600 text-base-300 font-mono text-xs
                           transition-all duration-150"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <div className="flex gap-2">
            <button
              onClick={() => onDecide(sessionId, "approve")}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded
                         bg-emerald-400/10 hover:bg-emerald-400/20
                         border border-emerald-400/30 hover:border-emerald-400/60
                         text-emerald-400 font-mono text-xs transition-all duration-150"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
              Approve & Deploy
            </button>

            <button
              onClick={() => setMode("rejecting")}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded
                         bg-rose-400/10 hover:bg-rose-400/20
                         border border-rose-400/30 hover:border-rose-400/60
                         text-rose-400 font-mono text-xs transition-all duration-150"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
              Reject with Feedback
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
