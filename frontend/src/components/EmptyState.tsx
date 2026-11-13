export function EmptyState({ onNew }: { onNew: () => void }) {
  const examples = [
    "Migrate app=n8n-csp-host from ap-south-1 to us-east-1",
    "Migrate env=production tagged resources from eu-west-1 to ap-southeast-1 using cloudformation",
    "Move all project=backend-api resources from us-east-1 to us-west-2",
  ];

  return (
    <div className="flex flex-col items-center justify-center h-full text-center px-8 select-none">
      {/* Grid decoration */}
      <div className="relative mb-8">
        <div
          className="w-20 h-20 rounded-2xl bg-base-800 border border-base-600
                     flex items-center justify-center"
        >
          <svg className="w-8 h-8 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round"
              d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23-.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5"
            />
          </svg>
        </div>
        {/* Corner accents */}
        <div className="absolute -top-1 -left-1 w-3 h-3 border-t-2 border-l-2 border-amber-400/40 rounded-tl" />
        <div className="absolute -top-1 -right-1 w-3 h-3 border-t-2 border-r-2 border-amber-400/40 rounded-tr" />
        <div className="absolute -bottom-1 -left-1 w-3 h-3 border-b-2 border-l-2 border-amber-400/40 rounded-bl" />
        <div className="absolute -bottom-1 -right-1 w-3 h-3 border-b-2 border-r-2 border-amber-400/40 rounded-br" />
      </div>

      <h2 className="font-sans font-semibold text-base-100 text-lg mb-1">
        AWS Migration Agent
      </h2>
      <p className="font-sans text-sm text-base-400 mb-6 max-w-sm leading-relaxed">
        Describe your migration in plain English. The agent will discover
        resources, map dependencies, and generate Terraform for you.
      </p>

      <button
        onClick={onNew}
        className="mb-8 px-4 py-2 rounded-lg bg-amber-400/10 hover:bg-amber-400/20
                   border border-amber-400/30 hover:border-amber-400/60
                   text-amber-400 font-mono text-xs tracking-wide
                   transition-all duration-150"
      >
        + Start New Migration
      </button>

      <div className="w-full max-w-sm space-y-2">
        <div className="font-mono text-[10px] text-base-600 tracking-widest uppercase mb-3">
          Example prompts
        </div>
        {examples.map((ex, i) => (
          <div
            key={i}
            className="text-left px-3 py-2.5 rounded-lg border border-base-700
                       bg-base-800 font-mono text-[11px] text-base-400
                       leading-relaxed"
          >
            {ex}
          </div>
        ))}
      </div>
    </div>
  );
}
