"""Turn a benchmark `Comparison` into a short plain-English summary via Gemini.

Single API call, no tools. If no API key is configured or the call fails,
`explain_comparison` returns None and the caller shows the stats without a blurb.

Uses the Google AI Studio (Gemini API) via the `google-genai` SDK.
"""

from __future__ import annotations

import dataclasses
import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

from app.core.benchmark import Comparison

logger = logging.getLogger(__name__)

# Quiet the SDK's "AFC is not recommended" notice - we pass no tools.
logging.getLogger("google_genai.models").setLevel(logging.ERROR)

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

API_KEY = os.getenv("GEMINI_API_KEY", "")
# flash-lite has a much larger free-tier daily quota than the full flash models
# (gemini-3.6-flash free tier is only ~20 requests/day - too tight for a team).
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")

_SYSTEM = """You explain agricultural water-use benchmark results to Australian \
farmers in a risk-assessment tool.

Write 2-3 short sentences of plain English. No bullet points, no headings, no \
jargon, no markdown. Speak to the farmer directly ("your farm", "you used").

Rules:
- Only use the numbers in the data provided. Never invent or estimate figures.
- "water intensity" means megalitres of water applied per hectare (ML/ha).
- sample_size is the number of regional benchmark data points, not a count of \
farms - don't call it "farms".
- percentile is where this farm ranks (lower = uses less water).
- A negative delta_pct or z_score means the farm uses LESS water than the \
benchmark - that is good news; say so plainly.
- If allocation_factor is greater than 1.0, say the region is facing tighter \
water allocation than usual and this is increasing operational risk.
- If rainfall_factor is greater than 1.0, say rainfall is running short or \
conditions are dry and that is adding pressure to water use.
- Never advise the farmer to relocate, stop irrigating, or switch crops.
- If benchmark figures are null, say a like-for-like benchmark wasn't available \
and keep it brief.
- Explain what the comparison means for them, not how it was calculated."""


def _thinking_config() -> types.ThinkingConfig:
    """Minimise reasoning - this is a short mechanical summary.

    Gemini 3.x flash uses `thinking_level` and rejects `thinking_budget=0`;
    Gemini 2.5 and earlier use `thinking_budget` (0 disables it).
    """
    if "gemini-3" in MODEL or "gemini-4" in MODEL:
        return types.ThinkingConfig(thinking_level=types.ThinkingLevel.MINIMAL)
    return types.ThinkingConfig(thinking_budget=0)


_client: genai.Client | None = None


def _get_client() -> genai.Client | None:
    global _client
    if _client is None and API_KEY:
        _client = genai.Client(api_key=API_KEY)
    return _client


def explain_comparison(comparison: Comparison) -> str | None:
    """Return a 2-3 sentence explanation, or None if unavailable."""
    client = _get_client()
    if client is None:
        logger.info("GEMINI_API_KEY not set - skipping explanation")
        return None

    payload = json.dumps(dataclasses.asdict(comparison), indent=2)

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=payload,
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM,
                max_output_tokens=1500,   # headroom: thinking tokens count toward this
                temperature=0.4,
                thinking_config=_thinking_config(),
            ),
        )
    except Exception:  # noqa: BLE001 - the summary is optional; never fail the request
        logger.exception("LLM explanation request failed")
        return None

    text = (response.text or "").strip()
    return text or None
