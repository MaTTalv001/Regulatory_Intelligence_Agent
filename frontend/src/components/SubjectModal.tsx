import { useState, useRef, useEffect } from "react";
import type { QueryTemplate } from "./SuggestedQueries";
import styles from "./SubjectModal.module.css";

interface Props {
  template: QueryTemplate;
  onSubmit: (query: string) => void;
  onClose: () => void;
}

export default function SubjectModal({ template, onSubmit, onClose }: Props) {
  const [value, setValue] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = () => {
    const trimmed = value.trim();
    if (!trimmed) return;
    onSubmit(template.buildQuery(trimmed));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleSubmit();
    }
    if (e.key === "Escape") {
      onClose();
    }
  };

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <h3 className={styles.title}>{template.title}</h3>
        <label className={styles.label}>{template.inputLabel}</label>
        <input
          ref={inputRef}
          className={styles.input}
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={template.inputPlaceholder}
        />
        <div className={styles.actions}>
          <button className={styles.cancel} onClick={onClose}>
            キャンセル
          </button>
          <button
            className={styles.submit}
            onClick={handleSubmit}
            disabled={!value.trim()}
          >
            実行
          </button>
        </div>
      </div>
    </div>
  );
}
