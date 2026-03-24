import styles from "./AgentActivity.module.css";

export interface ToolStep {
  tool: string;
  label: string;
  status: "running" | "done";
}

interface Props {
  steps: ToolStep[];
  statusMessage: string | null;
}

export default function AgentActivity({ steps, statusMessage }: Props) {
  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.spinner} />
        <span className={styles.title}>
          {statusMessage || "エージェントが処理中..."}
        </span>
      </div>

      {steps.length > 0 && (
        <div className={styles.steps}>
          {steps.map((step, i) => (
            <div
              key={`${step.tool}-${i}`}
              className={`${styles.step} ${step.status === "done" ? styles.done : styles.running}`}
            >
              <span className={styles.icon}>
                {step.status === "done" ? (
                  <svg viewBox="0 0 16 16" width="14" height="14" fill="currentColor">
                    <path d="M13.78 4.22a.75.75 0 010 1.06l-7.25 7.25a.75.75 0 01-1.06 0L2.22 9.28a.75.75 0 011.06-1.06L6 10.94l6.72-6.72a.75.75 0 011.06 0z" />
                  </svg>
                ) : (
                  <div className={styles.stepSpinner} />
                )}
              </span>
              <span className={styles.label}>{step.label}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
