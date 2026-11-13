import { useCallback, useRef, useState } from "react";
import { openSSEStream, startMigration, submitDecision } from "../lib/api";
import type {
  AgentStep,
  Conversation,
  IaCData,
  Message,
  SSEEvent,
} from "../types";

function uid() {
  return Math.random().toString(36).slice(2, 10);
}

function isIaCData(data: unknown): data is IaCData {
  if (typeof data !== "object" || data === null) return false;
  const candidate = data as Record<string, unknown>;
  return (
    typeof candidate.generated_iac === "string" &&
    typeof candidate.iac_file_path === "string"
  );
}

function makeMessage(partial: Omit<Message, "id" | "timestamp">): Message {
  return { id: uid(), timestamp: Date.now(), ...partial };
}

export function useConversations() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const esRef = useRef<EventSource | null>(null);

  const activeConv = conversations.find((c) => c.id === activeId) ?? null;

  // ── Helpers ───────────────────────────────────────────────────────────────

  const patchConv = useCallback((id: string, patch: Partial<Conversation>) => {
    setConversations((prev) =>
      prev.map((c) => (c.id === id ? { ...c, ...patch } : c))
    );
  }, []);

  const appendMsg = useCallback(
    (convId: string, msg: Message) => {
      setConversations((prev) =>
        prev.map((c) =>
          c.id === convId ? { ...c, messages: [...c.messages, msg] } : c
        )
      );
    },
    []
  );

  const patchLastStepsMsg = useCallback(
    (convId: string, step: AgentStep) => {
      setConversations((prev) =>
        prev.map((c) => {
          if (c.id !== convId) return c;
          const msgs = [...c.messages];
          const lastIdx = msgs.length - 1;
          if (lastIdx >= 0 && msgs[lastIdx].kind === "steps") {
            msgs[lastIdx] = {
              ...msgs[lastIdx],
              steps: [...(msgs[lastIdx].steps ?? []), step],
            };
            return { ...c, messages: msgs };
          }
          // No existing steps message — create one
          return {
            ...c,
            messages: [
              ...msgs,
              makeMessage({ role: "agent", kind: "steps", content: "", steps: [step] }),
            ],
          };
        })
      );
    },
    []
  );

  // ── SSE handler ───────────────────────────────────────────────────────────

  const handleSSEEvent = useCallback(
    (convId: string, raw: string) => {
      let evt: SSEEvent;
      try {
        evt = JSON.parse(raw) as SSEEvent;
      } catch {
        return;
      }

      switch (evt.event) {
        case "step_update": {
          const d = evt.data as { node: string; step: string; errors: string[] };
          patchLastStepsMsg(convId, {
            node: d.node,
            step: d.step,
            errors: d.errors ?? [],
            timestamp: Date.now(),
          });
          break;
        }

        case "iac_ready": {
          if (!isIaCData(evt.data)) {
            appendMsg(
              convId,
              makeMessage({
                role: "agent",
                kind: "error",
                content: "Received an invalid IaC artifact from the server.",
              })
            );
            patchConv(convId, { status: "failed" });
            break;
          }
          const d = evt.data;
          appendMsg(
            convId,
            makeMessage({
              role: "agent",
              kind: "artifact",
              content: "IaC generated successfully.",
              iac: d.generated_iac,
              iacPath: d.iac_file_path,
              sessionId: evt.session_id,
            })
          );
          break;
        }

        case "hitl_required": {
          appendMsg(
            convId,
            makeMessage({
              role: "agent",
              kind: "hitl",
              content: "Review the generated IaC above before deployment.",
              sessionId: evt.session_id,
              awaitingDecision: true,
            })
          );
          patchConv(convId, { status: "awaiting_human" });
          esRef.current?.close();
          break;
        }

        case "hitl_resumed": {
          appendMsg(
            convId,
            makeMessage({
              role: "agent",
              kind: "text",
              content: `Decision submitted. Resuming pipeline…`,
            })
          );
          patchConv(convId, { status: "running" });
          break;
        }

        case "completed": {
          appendMsg(
            convId,
            makeMessage({
              role: "agent",
              kind: "text",
              content: "✓ Migration pipeline completed.",
            })
          );
          patchConv(convId, { status: "completed" });
          esRef.current?.close();
          break;
        }

        case "error": {
          const d = evt.data as { detail: string };
          appendMsg(
            convId,
            makeMessage({
              role: "agent",
              kind: "error",
              content: d.detail ?? "An unknown error occurred.",
            })
          );
          patchConv(convId, { status: "failed" });
          esRef.current?.close();
          break;
        }
      }
    },
    [appendMsg, patchConv, patchLastStepsMsg]
  );

  // ── Public actions ────────────────────────────────────────────────────────

  const newConversation = useCallback(() => {
    const id = uid();
    const conv: Conversation = {
      id,
      title: "New migration",
      createdAt: Date.now(),
      messages: [],
      status: "idle",
    };
    setConversations((prev) => [conv, ...prev]);
    setActiveId(id);
    esRef.current?.close();
  }, []);

  const selectConversation = useCallback((id: string) => {
    esRef.current?.close();
    setActiveId(id);
  }, []);

  const sendPrompt = useCallback(
    async (prompt: string) => {
      if (!activeId) return;

      // Add user message
      appendMsg(activeId, makeMessage({ role: "user", kind: "text", content: prompt }));

      // Update title from first prompt
      setConversations((prev) =>
        prev.map((c) =>
          c.id === activeId && c.title === "New migration"
            ? { ...c, title: prompt.slice(0, 48) + (prompt.length > 48 ? "…" : "") }
            : c
        )
      );

      patchConv(activeId, { status: "running" });

      try {
        const { session_id } = await startMigration(prompt);
        patchConv(activeId, { sessionId: session_id });

        // Add initial steps message placeholder
        appendMsg(
          activeId,
          makeMessage({ role: "agent", kind: "steps", content: "", steps: [] })
        );

        // Open SSE stream
        esRef.current?.close();
        esRef.current = openSSEStream(
          session_id,
          (raw) => handleSSEEvent(activeId, raw),
          () => {
            /* connection errors handled via error events */
          }
        );
      } catch (err) {
        appendMsg(
          activeId,
          makeMessage({
            role: "agent",
            kind: "error",
            content: err instanceof Error ? err.message : "Failed to start migration.",
          })
        );
        patchConv(activeId, { status: "failed" });
      }
    },
    [activeId, appendMsg, handleSSEEvent, patchConv]
  );

  const sendDecision = useCallback(
    async (
      sessionId: string,
      decision: "approve" | "reject",
      feedback = ""
    ) => {
      if (!activeId) return;

      // Mark hitl message as no longer awaiting
      setConversations((prev) =>
        prev.map((c) => {
          if (c.id !== activeId) return c;
          return {
            ...c,
            messages: c.messages.map((m) =>
              m.kind === "hitl" && m.awaitingDecision
                ? { ...m, awaitingDecision: false }
                : m
            ),
          };
        })
      );

      appendMsg(
        activeId,
        makeMessage({
          role: "user",
          kind: "text",
          content:
            decision === "approve"
              ? "✓ Approved — proceed with deployment."
              : `✗ Rejected — ${feedback}`,
        })
      );

      try {
        await submitDecision(sessionId, decision, feedback);
        patchConv(activeId, { status: "running" });

        // Re-open SSE stream for the resumed graph
        esRef.current?.close();
        esRef.current = openSSEStream(
          sessionId,
          (raw) => handleSSEEvent(activeId, raw),
          () => {}
        );
      } catch (err) {
        appendMsg(
          activeId,
          makeMessage({
            role: "agent",
            kind: "error",
            content: err instanceof Error ? err.message : "Decision submission failed.",
          })
        );
      }
    },
    [activeId, appendMsg, handleSSEEvent, patchConv]
  );

  return {
    conversations,
    activeConv,
    newConversation,
    selectConversation,
    sendPrompt,
    sendDecision,
  };
}
