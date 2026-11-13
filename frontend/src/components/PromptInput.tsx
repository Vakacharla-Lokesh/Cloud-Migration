import { useRef, useState } from "react";

interface Props {
  onSubmit: (prompt: string) => void;
  disabled: boolean;
  placeholder?: string;
}

export function PromptInput({ onSubmit, disabled, placeholder }: Props) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSubmit(trimmed);
    setValue("");
    // Reset height
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setValue(e.target.value);
    // Auto-resize
    const el = e.target;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  };

  return (
    <div className="border-t border-base-700 bg-base-900 px-4 py-4">
      <div
        className={`
          flex items-end gap-3 rounded-xl border
          bg-base-800 px-4 py-3 transition-all duration-150
          ${
            disabled
              ? "border-base-600 opacity-60"
              : "border-base-600 hover:border-base-500 focus-within:border-amber-400/60"
          }
        `}
      >
        <textarea
          ref={textareaRef}
          value={value}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          rows={1}
          placeholder={
            placeholder ??
            'Describe the migration — e.g. "Migrate all resources tagged app=n8n-csp-host from ap-south-1 to us-east-1"'
          }
          className="flex-1 bg-transparent font-sans text-sm text-base-100
                     placeholder:text-base-500 outline-none resize-none
                     leading-relaxed max-h-40 scrollbar-thin"
        />

        <button
          onClick={handleSubmit}
          disabled={disabled || !value.trim()}
          className={`
            shrink-0 w-8 h-8 rounded-lg flex items-center justify-center
            transition-all duration-150
            ${
              !disabled && value.trim()
                ? "bg-amber-400 hover:bg-amber-500 text-base-950"
                : "bg-base-700 text-base-500 cursor-not-allowed"
            }
          `}
        >
          {disabled ? (
            <svg className="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
            </svg>
          ) : (
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
            </svg>
          )}
        </button>
      </div>

      <div className="mt-2 flex items-center justify-between px-1">
        <div className="font-mono text-[10px] text-base-600">
          Enter to send · Shift+Enter for newline
        </div>
        {disabled && (
          <div className="font-mono text-[10px] text-amber-400">
            Agent running<span className="animate-blink">_</span>
          </div>
        )}
      </div>
    </div>
  );
}
