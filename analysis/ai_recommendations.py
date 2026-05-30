"""
AI-powered recommendations using Claude.
"""
from __future__ import annotations

import json
import os

import anthropic

from analysis.analyzer import SalesReport


def get_recommendations(report: SalesReport) -> str:
    """
    Send the sales report to Claude and get actionable business recommendations.
    Returns a formatted string of recommendations.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY not set. Add it to your .env file or export it as an environment variable."
        )

    client = anthropic.Anthropic(api_key=api_key)

    data = json.dumps(report.to_dict(), indent=2)

    prompt = f"""You are a restaurant business analyst. Below is a structured sales report extracted from a restaurant's CSV data.

{data}

Based on this data, provide exactly 5 specific, actionable recommendations to increase revenue and improve operations.

Format your response as:

**Recommendation 1: [Short Title]**
[2-3 sentences explaining what to do and why, referencing specific numbers from the data.]

**Recommendation 2: [Short Title]**
[2-3 sentences explaining what to do and why, referencing specific numbers from the data.]

...and so on.

Be concrete. Reference actual item names, dollar amounts, days, and percentages from the data. No generic advice."""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    return message.content[0].text
