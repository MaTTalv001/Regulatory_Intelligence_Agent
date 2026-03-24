import styles from "./SuggestedQueries.module.css";

export interface QueryTemplate {
  title: string;
  description: string;
  inputLabel: string;
  inputPlaceholder: string;
  buildQuery: (subject: string) => string;
}

export const SUGGESTIONS: QueryTemplate[] = [
  {
    title: "安全性シグナル分析",
    description: "FAERS有害事象データの分析",
    inputLabel: "分析対象の医薬品名を入力してください",
    inputPlaceholder: "例: XGEVA, keytruda, opdivo",
    buildQuery: (name) =>
      `${name}の有害事象報告を分析して、主要な安全性シグナルを特定してください。重篤な事象を中心にまとめてください。`,
  },
  {
    title: "FDA / EMA 承認比較",
    description: "日米欧の承認状況・適応症を比較",
    inputLabel: "比較対象の医薬品名（または有効成分名）を入力してください",
    inputPlaceholder: "例: denosumab, pembrolizumab",
    buildQuery: (name) =>
      `${name}のFDAとEMAでの承認状況と適応症を比較してください。承認日、適応の違い、安全性情報の差異があれば指摘してください。`,
  },
  {
    title: "リコール・回収情報",
    description: "FDA enforcement actionsの検索",
    inputLabel: "調査対象の医薬品名または企業名を入力してください",
    inputPlaceholder: "例: metformin, Pfizer",
    buildQuery: (name) =>
      `${name}に関連するFDAリコール・回収情報を調べてください。Class分類ごとに整理し、回収理由と状況を教えてください。`,
  },
  {
    title: "供給不足モニタリング",
    description: "FDA / EMA 医薬品供給状況の確認",
    inputLabel: "確認したい医薬品名または薬効分類を入力してください",
    inputPlaceholder: "例: morphine, opioid, antibiotics",
    buildQuery: (name) =>
      `${name}に関連する医薬品の供給不足状況をFDA・EMA両方で確認してください。入手可能性と代替品の情報も含めてください。`,
  },
];

interface Props {
  onSelectTemplate: (template: QueryTemplate) => void;
}

export default function SuggestedQueries({ onSelectTemplate }: Props) {
  return (
    <div className={styles.container}>
      <h2 className={styles.heading}>Regulatory Intelligence Agent</h2>
      <p className={styles.subheading}>
        FDA / EMA の当局データを AI エージェントが横断分析します
      </p>
      <div className={styles.grid}>
        {SUGGESTIONS.map((s) => (
          <button
            key={s.title}
            className={styles.card}
            onClick={() => onSelectTemplate(s)}
          >
            <span className={styles.cardTitle}>{s.title}</span>
            <span className={styles.cardDesc}>{s.description}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
