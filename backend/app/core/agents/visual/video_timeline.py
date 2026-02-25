from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class SceneSpec(BaseModel):
    id: str
    duration: float # in seconds
    visual_prompt: str # for asset generation
    caption: Optional[str] = None
    transition_type: str = Field(default="fade", description="fade, slide, or zoom")
    audio_path: Optional[str] = None

class VideoTimeline(BaseModel):
    """Level 10 CineSovereign Schema"""
    project_name: str
    resolution: str = Field(default="1080x1920", description="Target result, e.g. 1920x1080 or 1080x1920 (Shorts)")
    fps: int = 30
    scenes: List[SceneSpec]
    background_music: Optional[str] = None
    voiceover_enabled: bool = True
    metadata: Dict[str, Any] = {}
