import type { AgentStep } from "../types";

interface Props {
  steps: AgentStep[];
  isRunning: boolean;
}

const NODE_LABELS: Record<string, string> = {
  intent_parser: "Intent Parser",
  resource_discovery: "Resource Discovery",
  dependency_mapper: "Dependency Mapper",
  iac_generator: "IaC Generator",
  hitl_gate: "Human Review Gate",
  deployment_stub: "Deployment",
  end_with_error: "Error",
};

export function StepsCard({ steps, isRunning }: Props) {
  return (
    <div className="rounded-lg border border-base-600 bg-base-800 overflow-hidden animate-slide-up">
      <div className="flex items-center gap-2 px-4 py-2.5 bg-base-700 border-b border-base-600">
        {isRunning && steps.length === 0 ? (
          <div className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse-dot" />
        ) : (
          <div className="w-1.5 h-1.5 rounded-full bg-base-500" />
        )}
        <span className="font-mono text-xs text-base-300 tracking-wide">
          Agent Pipeline
        </span>
        {isRunning && (
          <span className="ml-auto font-mono text-[10px] text-amber-400">
            running
            <span className="animate-blink">_</span>
          </span>
        )}
      </div>

      <div className="px-4 py-3 space-y-2">
        {steps.length === 0 && isRunning && (
          <div className="font-mono text-xs text-base-500">
            Starting pipeline<span className="animate-blink">_</span>
          </div>
        )}

        {steps.map((step, i) => {
          const isLast = i === steps.length - 1;
          const hasError = step.errors.length > 0;

          return (
            <div key={i} className="flex items-start gap-3">
              {/* Timeline dot + line */}
              <div className="flex flex-col items-center pt-0.5">
                <div
                  className={`w-2 h-2 rounded-full shrink-0 ${
                    hasError
                      ? "bg-rose-400"
                      : isLast && isRunning
                      ? "bg-amber-400 animate-pulse-dot"
                      : "bg-emerald-400"
                  }`}
                />
                {i < steps.length - 1 && (
                  <div className="w-px flex-1 bg-base-600 mt-1 min-h-[12px]" />
                )}
              </div>

              {/* Content */}
              <div className="pb-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-medium text-base-200">
                    {NODE_LABELS[step.node] ?? step.node}
                  </span>
                  <span className="font-mono text-[10px] text-base-500">
                    {step.step}
                  </span>
                </div>
                {hasError && (
                  <div className="mt-1 font-mono text-[10px] text-rose-400 break-all">
                    {step.errors.join(", ")}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
