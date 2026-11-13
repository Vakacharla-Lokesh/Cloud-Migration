const BASE = "/api/migration";

export async function startMigration(
  prompt: string,
  sessionId?: string
): Promise<{ session_id: string }> {
  const res = await fetch(`${BASE}/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt, session_id: sessionId }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Failed to start migration");
  }
  return res.json();
}

export async function submitDecision(
  sessionId: string,
  decision: "approve" | "reject",
  feedback = ""
): Promise<void> {
  const res = await fetch(`${BASE}/${sessionId}/decision`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ decision, feedback }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Failed to submit decision");
  }
}

export function getIaCDownloadUrl(sessionId: string): string {
  return `${BASE}/${sessionId}/iac`;
}

export function openSSEStream(
  sessionId: string,
  onEvent: (raw: string) => void,
  onError: (e: Event) => void
): EventSource {
  const es = new EventSource(`${BASE}/${sessionId}/stream`);
  es.onmessage = (e) => onEvent(e.data);
  es.onerror = onError;
  return es;
}
