import { useState, useRef, useEffect, useCallback } from "react";
import type { ChatMessage as ChatMsg, AgentEvent } from "./api/client";
import { streamChat, deleteSession } from "./api/client";
import Header from "./components/Header";
import ChatMessage from "./components/ChatMessage";
import ChatInput from "./components/ChatInput";
import SuggestedQueries from "./components/SuggestedQueries";
import type { QueryTemplate } from "./components/SuggestedQueries";
import SubjectModal from "./components/SubjectModal";
import AgentActivity from "./components/AgentActivity";
import type { ToolStep } from "./components/AgentActivity";
import styles from "./App.module.css";

export default function App() {
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTemplate, setActiveTemplate] = useState<QueryTemplate | null>(
    null,
  );
  const [toolSteps, setToolSteps] = useState<ToolStep[]>([]);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, toolSteps]);

  const handleSend = useCallback(
    (content: string) => {
      const userMsg: ChatMsg = { role: "user", content };
      setMessages((prev) => [...prev, userMsg]);
      setLoading(true);
      setToolSteps([]);
      setStatusMessage(null);

      const allMessages = [...messages, userMsg];

      const controller = streamChat(
        allMessages,
        sessionId,
        (event: AgentEvent) => {
          switch (event.type) {
            case "status":
              setStatusMessage(event.message ?? null);
              break;

            case "tool_start":
              setToolSteps((prev) => [
                ...prev,
                {
                  tool: event.tool!,
                  label: event.label!,
                  status: "running",
                },
              ]);
              setStatusMessage(event.label ?? null);
              break;

            case "tool_end":
              setToolSteps((prev) =>
                prev.map((s) =>
                  s.tool === event.tool && s.status === "running"
                    ? { ...s, status: "done" }
                    : s,
                ),
              );
              break;

            case "response":
              if (event.session_id) setSessionId(event.session_id);
              setMessages((prev) => [
                ...prev,
                { role: "assistant", content: event.content! },
              ]);
              break;

            case "error":
              setMessages((prev) => [
                ...prev,
                {
                  role: "assistant",
                  content: `エラー: ${event.message}`,
                },
              ]);
              break;

            case "done":
              if (event.session_id) setSessionId(event.session_id);
              setLoading(false);
              setToolSteps([]);
              setStatusMessage(null);
              break;
          }
        },
      );

      abortRef.current = controller;
    },
    [messages, sessionId],
  );

  const handleNewChat = useCallback(() => {
    if (abortRef.current) abortRef.current.abort();
    if (sessionId) deleteSession(sessionId);
    setMessages([]);
    setSessionId(null);
    setLoading(false);
    setToolSteps([]);
    setStatusMessage(null);
  }, [sessionId]);

  const handleTemplateSelect = useCallback((template: QueryTemplate) => {
    setActiveTemplate(template);
  }, []);

  const handleModalSubmit = useCallback(
    (query: string) => {
      setActiveTemplate(null);
      handleSend(query);
    },
    [handleSend],
  );

  const hasMessages = messages.length > 0 || loading;

  return (
    <div className={styles.app}>
      <Header onNewChat={handleNewChat} />
      <main className={styles.main}>
        {hasMessages ? (
          <div className={styles.messages}>
            {messages.map((msg, i) => (
              <ChatMessage key={i} message={msg} />
            ))}
            {loading && (
              <AgentActivity steps={toolSteps} statusMessage={statusMessage} />
            )}
            <div ref={bottomRef} />
          </div>
        ) : (
          <SuggestedQueries onSelectTemplate={handleTemplateSelect} />
        )}
      </main>
      <ChatInput onSend={handleSend} disabled={loading} />

      {activeTemplate && (
        <SubjectModal
          template={activeTemplate}
          onSubmit={handleModalSubmit}
          onClose={() => setActiveTemplate(null)}
        />
      )}
    </div>
  );
}
