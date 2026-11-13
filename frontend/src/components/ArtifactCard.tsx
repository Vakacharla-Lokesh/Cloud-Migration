import { useState } from "react";
import { getIaCDownloadUrl } from "../lib/api";

interface Props {
  iac: string;
  iacPath: string;
  sessionId: string;
}

export function ArtifactCard({ iac, sessionId }: Props) {
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(false);

  const lines = iac.split("\n");
  const preview = lines.slice(0, 18).join("\n");
  const hasMore = lines.length > 18;

  const handleCopy = async () => {
    await navigator.clipboard.writeText(iac);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const fileName = `${sessionId}.tf`;
  const downloadUrl = getIaCDownloadUrl(sessionId);

  return (
    <div className="rounded-lg border border-base-600 bg-base-800 overflow-hidden animate-slide-up">
      {/* Header bar */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-base-700 border-b border-base-600">
        <div className="flex items-center gap-2.5">
          {/* File icon */}
          <div className="w-6 h-6 rounded bg-emerald-400/10 border border-emerald-400/30 flex items-center justify-center">
            <svg className="w-3 h-3 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>

          <div>
            <div className="font-mono text-xs text-emerald-400 font-medium">{fileName}</div>
            <div className="font-mono text-[10px] text-base-400 mt-0.5">
              Terraform · {lines.length} lines
            </div>
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded
                       bg-base-600 hover:bg-base-500 border border-base-500
                       hover:border-base-400 text-base-200 font-mono text-[10px]
                       transition-all duration-150"
          >
            {copied ? (
              <>
                <svg className="w-3 h-3 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
                <span className="text-emerald-400">Copied</span>
              </>
            ) : (
              <>
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                Copy
              </>
            )}
          </button>

          <a
            href={downloadUrl}
            download={fileName}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded
                       bg-emerald-400/10 hover:bg-emerald-400/20 border border-emerald-400/30
                       hover:border-emerald-400/60 text-emerald-400 font-mono text-[10px]
                       transition-all duration-150"
          >
            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Download .tf
          </a>
        </div>
      </div>

      {/* Code block */}
      <div className="relative">
        <pre
          className="font-mono text-[11px] leading-relaxed text-base-200 p-4
                     overflow-x-auto scrollbar-thin"
        >
          <code>{expanded ? iac : preview}</code>
        </pre>

        {/* Expand / collapse */}
        {hasMore && (
          <div
            className={`${
              !expanded ? "absolute bottom-0 left-0 right-0" : ""
            }`}
          >
            {!expanded && (
              <div className="h-12 bg-gradient-to-t from-base-800 to-transparent pointer-events-none" />
            )}
            <button
              onClick={() => setExpanded((p) => !p)}
              className="w-full py-2 font-mono text-[10px] text-base-400
                         hover:text-base-200 hover:bg-base-700 transition-colors
                         border-t border-base-700 tracking-wide"
            >
              {expanded
                ? "▲ Show less"
                : `▼ Show all ${lines.length} lines`}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
