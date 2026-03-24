import styles from "./Header.module.css";

interface HeaderProps {
  onNewChat: () => void;
}

export default function Header({ onNewChat }: HeaderProps) {
  return (
    <header className={styles.header}>
      <div className={styles.brand}>
        <svg
          className={styles.icon}
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2" />
          <rect x="9" y="3" width="6" height="4" rx="1" />
          <path d="M9 14l2 2 4-4" />
        </svg>
        <h1 className={styles.title}>Regulatory Intelligence Agent</h1>
      </div>
      <button className={styles.newChat} onClick={onNewChat}>
        新しい会話
      </button>
    </header>
  );
}
