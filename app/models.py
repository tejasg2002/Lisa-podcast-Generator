from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict

class ElevenLabsConfig(BaseModel):
    stability: float = Field(ge=0.0, le=1.0, description="Stability setting (0.0 to 1.0)")
    similarity_boost: float = Field(ge=0.0, le=1.0, description="Similarity boost setting (0.0 to 1.0)")
    style: float = Field(ge=0.0, le=1.0, description="Style setting (0.0 to 1.0)")
    model_id: str
    speed: float = Field(default=1.0, ge=0.25, le=4.0, description="Speed setting (0.25 to 4.0)")

class HeygenConfig(BaseModel):
    host_avatar_id: str
    guest_avatar_id: str
    background: Optional[str] = Field(default=None, description="Background URL or color (optional)")

class AudioPodcastRequest(BaseModel):
    input_type: Literal["idea", "script"]
    input_text: str
    language: Literal["english", "hindi"]
    host_name: str
    guest_name: str
    host_voice_id: str
    guest_voice_id: str
    elevenlabs_config: ElevenLabsConfig
    duration_minutes: int = Field(default=5, ge=1, le=60, description="Desired podcast duration in minutes (1-60)")

class VideoPodcastRequest(BaseModel):
    input_type: Literal["idea", "script"]
    input_text: str
    language: Literal["english", "hindi"]
    orientation: Literal["landscape", "portrait"]
    host_name: str
    guest_name: str
    host_voice_id: str
    guest_voice_id: str
    elevenlabs_config: ElevenLabsConfig
    heygen_config: HeygenConfig
    duration_minutes: int = Field(default=5, ge=1, le=60, description="Desired podcast duration in minutes (1-60)")

class PodcastResponse(BaseModel):
    status: str
    type: Literal["audio", "video"]
    language: str
    s3_url: str
    duration_seconds: int
    host: str
    guest: str 