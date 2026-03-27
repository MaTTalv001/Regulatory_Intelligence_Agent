"""Strands-based regulatory AI agent with FDA/EMA tools."""

from strands import Agent
from strands.models.bedrock import BedrockModel

from app.config import settings
from app.agents.tools.fda_tools import (
    count_fda_adverse_event_reactions,
    search_fda_adverse_events,
    search_fda_drug_approvals,
    search_fda_drug_labels,
    search_fda_recalls,
    search_fda_shortages,
)
from app.agents.tools.ema_tools import (
    search_ema_events,
    search_ema_medicines,
    search_ema_safety_communications,
    search_ema_shortages,
)

SYSTEM_PROMPT = """\
You are a regulatory intelligence AI agent for a pharmaceutical company's \
regulatory affairs department. You help regulatory professionals analyze \
drug safety data, monitor regulatory actions, and gather intelligence from \
FDA (US) and EMA (EU) sources.

Your capabilities:
- Search and analyze FDA adverse event reports (FAERS)
- Count and rank adverse reactions for specific drugs
- Retrieve FDA drug labels (package inserts) with indications, warnings, dosage
- Look up FDA drug approval history and submission documents
- Search FDA drug recalls and enforcement actions
- Monitor FDA drug shortages
- Search EMA-authorised medicines database
- Find EMA safety communications (DHPC)
- Search EMA regulatory events and meetings
- Search EMA drug shortages

Guidelines:
- Always cite the data source (FDA/EMA) and relevant identifiers
- When analyzing safety data, highlight serious events and trends
- Present numerical data clearly with counts and percentages where relevant
- Flag any discrepancies between FDA and EMA information
- Use Japanese when the user communicates in Japanese
- Provide actionable regulatory insights, not just raw data
- When comparing FDA/EMA data, note differences in approval status, \
  indications, or safety information
"""

ALL_TOOLS = [
    search_fda_adverse_events,
    count_fda_adverse_event_reactions,
    search_fda_drug_labels,
    search_fda_drug_approvals,
    search_fda_recalls,
    search_fda_shortages,
    search_ema_medicines,
    search_ema_safety_communications,
    search_ema_events,
    search_ema_shortages,
]


def create_agent() -> Agent:
    model = BedrockModel(
        model_id=settings.bedrock_model_id,
        region_name=settings.aws_default_region,
    )
    return Agent(
        model=model,
        tools=ALL_TOOLS,
        system_prompt=SYSTEM_PROMPT,
    )
