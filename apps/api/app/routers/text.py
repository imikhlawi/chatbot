import json
from fastapi import APIRouter, HTTPException
from app.schemas.briefing import BriefingRequest, BriefingResponse
from app.services.llm_client import LLMClient

router = APIRouter(prefix="/api/text", tags=["text"])
llm = LLMClient()

SYSTEM_RULES = """
You are a strict JSON generator.
Return ONLY valid JSON that matches the schema.
No markdown, no explanations, no extra keys.
All strings must be plain text (no code fences).
"""


def build_prompt(req: BriefingRequest) -> str:
    schema = {
        "summary": "string (exactly 3 sentences in the requested language)",
        "keypoints": ["string (max N items)"],
        "headlines": ["string (max M items)"],
        "keywords": ["string"],
        "risks": ["string"],
        "todos": ["string"],
    }

    language = (
        getattr(req.options, "language", "de") if req.options else "de"
    )
    tone = getattr(req.options, "tone", "neutral") if req.options else "neutral"
    max_kp = (
        getattr(req.options, "max_keypoints", 10) if req.options else 10
    )
    max_hl = (
        getattr(req.options, "max_headlines", 5) if req.options else 5
    )

    return f"""{SYSTEM_RULES}

Language: {language}
Tone: {tone}
Keypoints max: {max_kp}
Headlines max: {max_hl}

JSON schema (informal):
{json.dumps(schema, ensure_ascii=False, indent=2)}

Text input:
{req.text}
"""


@router.post("/briefing", response_model=BriefingResponse)
async def briefing(req: BriefingRequest):
    try:
        raw = await llm.completion(
            build_prompt(req), n_predict=700, temperature=0.2
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM request failed: {e}")

    raw_str = raw.strip()
    try:
        data = json.loads(raw_str)
    except Exception:
        start = raw_str.find("{")
        end = raw_str.rfind("}")
        if start >= 0 and end > start:
            try:
                data = json.loads(raw_str[start : end + 1])
            except Exception:
                raise HTTPException(
                    status_code=500,
                    detail=f"LLM output is not valid JSON. Output starts with: {raw_str[:200]}",
                )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"LLM output is not valid JSON. Output starts with: {raw_str[:200]}",
            )

    rendered_md = (
        f"## Summary\n{data.get('summary', '')}\n\n"
        f"## Keypoints\n"
        + "\n".join([f"- {x}" for x in data.get("keypoints", [])])
        + "\n\n"
        f"## Headlines\n"
        + "\n".join([f"- {x}" for x in data.get("headlines", [])])
        + "\n\n"
        f"## Keywords\n"
        + ", ".join(data.get("keywords", []))
        + "\n\n"
        f"## Risks\n"
        + "\n".join([f"- {x}" for x in data.get("risks", [])])
        + "\n\n"
        f"## To-Dos\n"
        + "\n".join([f"- {x}" for x in data.get("todos", [])])
    )

    data["rendered_md"] = rendered_md

    return BriefingResponse(**data)
