import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ChatMessage as ChatMsg } from "../api/client";
import styles from "./ChatMessage.module.css";

interface Props {
  message: ChatMsg;
}

export default function ChatMessage({ message }: Props) {
  const isUser = message.role === "user";

  return (
    <div className={`${styles.row} ${isUser ? styles.user : styles.agent}`}>
      {!isUser && <div className={styles.avatar}>AI</div>}
      <div
        className={`${styles.bubble} ${isUser ? styles.userBubble : styles.agentBubble}`}
      >
        {isUser ? (
          <p>{message.content}</p>
        ) : (
          <div className={styles.markdown}>
            <Markdown remarkPlugins={[remarkGfm]}>{message.content}</Markdown>
          </div>
        )}
      </div>
    </div>
  );
}
