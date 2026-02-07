from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class BriefingOptions(BaseModel):
    language: Literal["de", "en"] = "de"
    tone: Literal["neutral", "formal", "friendly"] = "neutral"
    max_keypoints: int = Field(default=10, ge=3, le=20)
    max_headlines: int = Field(default=5, ge=3, le=10)


class BriefingRequest(BaseModel):
    text: str = Field(min_length=10, description="Freitext, z.B. Artikel/Notizen")
    options: Optional[BriefingOptions] = None


class BriefingResponse(BaseModel):
    summary: str
    keypoints: List[str]
    headlines: List[str]
    keywords: List[str]
    risks: List[str]
    todos: List[str]
    rendered_md: str
