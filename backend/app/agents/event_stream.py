"""Lightweight event emitter using contextvars for tool activity streaming."""

import contextvars
import queue
from typing import Optional

event_queue_var: contextvars.ContextVar[Optional[queue.Queue]] = contextvars.ContextVar(
    "event_queue", default=None
)

TOOL_LABELS: dict[str, str] = {
    "search_fda_adverse_events": "FDA 有害事象レポートを検索中",
    "count_fda_adverse_event_reactions": "FDA 有害反応の発生頻度を集計中",
    "search_fda_drug_labels": "FDA 添付文書（ラベル）を検索中",
    "search_fda_drug_approvals": "FDA 承認履歴を検索中",
    "search_fda_recalls": "FDA リコール・回収情報を検索中",
    "search_fda_shortages": "FDA 供給不足情報を取得中",
    "search_ema_medicines": "EMA 承認医薬品データベースを検索中",
    "search_ema_safety_communications": "EMA 安全性情報（DHPC）を検索中",
    "search_ema_events": "EMA 規制イベント情報を検索中",
    "search_ema_shortages": "EMA 供給不足情報を検索中",
    "search_ema_epi": "EMA 電子添文（ePI）を照会中",
}


def emit(event: dict):
    q = event_queue_var.get()
    if q is not None:
        q.put_nowait(event)


def tool_start(tool_name: str, args: dict | None = None):
    label = TOOL_LABELS.get(tool_name, tool_name)
    emit({"type": "tool_start", "tool": tool_name, "label": label, "args": args or {}})


def tool_end(tool_name: str):
    label = TOOL_LABELS.get(tool_name, tool_name)
    emit({"type": "tool_end", "tool": tool_name, "label": label})
