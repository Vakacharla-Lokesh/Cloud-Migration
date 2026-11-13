// ── SSE event types (mirror backend schemas/api.py) ──────────────────────────

export type SSEEventType =
  | "step_update"
  | "iac_ready"
  | "hitl_required"
  | "hitl_resumed"
  | "completed"
  | "error";

export interface SSEEvent {
  event: SSEEventType;
  session_id: string;
  data: Record<string, unknown>;
}

// ── Step update ───────────────────────────────────────────────────────────────

export interface StepUpdateData {
  node: string;
  step: string;
  errors: string[];
}

// ── IaC artifact ──────────────────────────────────────────────────────────────

export interface IaCData {
  generated_iac: string;
  iac_file_path: string;
}

// ── HITL ─────────────────────────────────────────────────────────────────────

export interface HITLData {
  message: string;
  interrupt_payload: {
    iac_file_path: string;
    generated_iac: string;
    resource_count: number;
  };
}

// ── Conversation ──────────────────────────────────────────────────────────────

export type MessageRole = "user" | "agent";

export type MessageKind = "text" | "steps" | "artifact" | "hitl" | "error";

export interface AgentStep {
  node: string;
  step: string;
  errors: string[];
  timestamp: number;
}

export interface Message {
  id: string;
  role: MessageRole;
  kind: MessageKind;
  content: string;
  timestamp: number;
  // artifact fields
  iac?: string;
  iacPath?: string;
  sessionId?: string;
  // steps
  steps?: AgentStep[];
  // hitl
  awaitingDecision?: boolean;
}

export interface Conversation {
  id: string;
  title: string;
  createdAt: number;
  messages: Message[];
  sessionId?: string;
  status: "idle" | "running" | "awaiting_human" | "completed" | "failed";
}
