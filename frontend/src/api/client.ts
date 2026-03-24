export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface AgentEvent {
  type: "status" | "tool_start" | "tool_end" | "response" | "done" | "error";
  tool?: string;
  label?: string;
  args?: Record<string, unknown>;
  content?: string;
  session_id?: string;
  message?: string;
}

const API_BASE = "/api";

export function streamChat(
  messages: ChatMessage[],
  sessionId: string | null,
  onEvent: (event: AgentEvent) => void,
): AbortController {
  const controller = new AbortController();

  fetch(`${API_BASE}/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages, session_id: sessionId }),
    signal: controller.signal,
  })
    .then(async (res) => {
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        onEvent({ type: "error", message: err.detail || "Request failed" });
        return;
      }

      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop()!;

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));
              onEvent(data);
            } catch {
              // skip malformed JSON
            }
          }
        }
      }
    })
    .catch((err) => {
      if (err.name !== "AbortError") {
        onEvent({ type: "error", message: err.message });
      }
    });

  return controller;
}

export async function deleteSession(sessionId: string): Promise<void> {
  await fetch(`${API_BASE}/sessions/${sessionId}`, { method: "DELETE" });
}
