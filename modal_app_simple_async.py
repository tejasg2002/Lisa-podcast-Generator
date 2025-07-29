import modal
import logging
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict
from datetime import datetime
import uuid
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Modal app
app = modal.App("lisa-podcast-generator-simple")

# Create image with dependencies
image = modal.Image.debian_slim(python_version="3.10").pip_install([
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "boto3>=1.34.0",
    "requests>=2.31.0",
    "pydantic>=2.5.0",
    "python-multipart>=0.0.6",
    "openai>=1.3.0",
    "python-dotenv>=1.0.0",
    "typing-extensions>=4.8.0"
]).apt_install([
    "ffmpeg"
])

# Define models inline
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

class TaskStatus(BaseModel):
    """Task status for async operations"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: Literal["pending", "processing", "completed", "failed"] = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict] = None
    error: Optional[str] = None
    progress: Optional[int] = Field(default=0, ge=0, le=100, description="Progress percentage")

# Simple task storage (in-memory for demo)
task_storage = {}

# Create FastAPI app
web_app = FastAPI(
    title="LISA Podcast Generator - Simple Async", 
    version="1.0.0",
    description="AI Podcast Generator with simple async polling"
)

@web_app.post("/v1/lisa-audio-podcast")
async def lisa_audio_podcast(data: AudioPodcastRequest):
    """Start audio podcast generation - returns task ID for polling"""
    logger.info("=== AUDIO PODCAST REQUEST RECEIVED ===")
    logger.info(f"Request data: {data.dict()}")
    
    # Create task
    task_id = str(uuid.uuid4())
    task = TaskStatus(
        id=task_id,
        status="pending"
    )
    
    # Store task
    task_storage[task_id] = task
    
    # Start async processing (simulated for now)
    asyncio.create_task(process_audio_podcast(task_id, data))
    
    return {
        "task_id": task_id,
        "status": "pending",
        "message": "Audio podcast generation started. Use task_id to poll for status."
    }

@web_app.post("/v1/lisa-video-podcast")
async def lisa_video_podcast(data: VideoPodcastRequest):
    """Start video podcast generation - returns task ID for polling"""
    logger.info("=== VIDEO PODCAST REQUEST RECEIVED ===")
    logger.info(f"Request data: {data.dict()}")
    
    # Create task
    task_id = str(uuid.uuid4())
    task = TaskStatus(
        id=task_id,
        status="pending"
    )
    
    # Store task
    task_storage[task_id] = task
    
    # Start async processing (simulated for now)
    asyncio.create_task(process_video_podcast(task_id, data))
    
    return {
        "task_id": task_id,
        "status": "pending",
        "message": "Video podcast generation started. Use task_id to poll for status."
    }

@web_app.get("/v1/status/{task_id}")
async def get_task_status(task_id: str):
    """Get status of a specific task"""
    if task_id not in task_storage:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = task_storage[task_id]
    return task

@web_app.get("/v1/tasks")
async def get_all_tasks():
    """Get all tasks (for monitoring)"""
    return {
        "tasks": [task.dict() for task in task_storage.values()],
        "total": len(task_storage)
    }

@web_app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "LISA Podcast Generator - Simple Async",
        "version": "1.0.0",
        "status": "✅ Async system is working!",
        "features": [
            "Audio podcast generation with async polling",
            "Video podcast generation with async polling",
            "Real-time status tracking",
            "Simple task management"
        ],
        "endpoints": {
            "audio": "/v1/lisa-audio-podcast",
            "video": "/v1/lisa-video-podcast",
            "status": "/v1/status/{task_id}",
            "all_tasks": "/v1/tasks"
        },
        "usage": "POST to start generation, GET /status/{task_id} to poll for results"
    }

@web_app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "active_tasks": len(task_storage),
        "version": "1.0.0"
    }

# Simulated async processing functions
async def process_audio_podcast(task_id: str, data: AudioPodcastRequest):
    """Simulate audio podcast processing"""
    try:
        task = task_storage[task_id]
        task.status = "processing"
        task.started_at = datetime.utcnow()
        task.progress = 10
        
        logger.info(f"Processing audio podcast task: {task_id}")
        
        # Simulate processing steps
        await asyncio.sleep(2)  # Step 1: Generate script
        task.progress = 30
        
        await asyncio.sleep(2)  # Step 2: Generate audio
        task.progress = 60
        
        await asyncio.sleep(2)  # Step 3: Merge audio
        task.progress = 90
        
        await asyncio.sleep(1)  # Step 4: Upload to S3
        task.progress = 100
        
        # Mark as completed
        task.status = "completed"
        task.completed_at = datetime.utcnow()
        task.result = {
            "s3_url": f"https://s3.amazonaws.com/your-bucket/audio_{task_id}.mp3",
            "duration": 300,
            "type": "audio"
        }
        
        logger.info(f"Completed audio podcast task: {task_id}")
        
    except Exception as e:
        logger.error(f"Error processing audio podcast task {task_id}: {e}")
        task = task_storage[task_id]
        task.status = "failed"
        task.error = str(e)
        task.completed_at = datetime.utcnow()

async def process_video_podcast(task_id: str, data: VideoPodcastRequest):
    """Simulate video podcast processing"""
    try:
        task = task_storage[task_id]
        task.status = "processing"
        task.started_at = datetime.utcnow()
        task.progress = 10
        
        logger.info(f"Processing video podcast task: {task_id}")
        
        # Simulate processing steps
        await asyncio.sleep(3)  # Step 1: Generate script
        task.progress = 20
        
        await asyncio.sleep(3)  # Step 2: Generate audio
        task.progress = 40
        
        await asyncio.sleep(3)  # Step 3: Generate video
        task.progress = 70
        
        await asyncio.sleep(2)  # Step 4: Merge video
        task.progress = 90
        
        await asyncio.sleep(1)  # Step 5: Upload to S3
        task.progress = 100
        
        # Mark as completed
        task.status = "completed"
        task.completed_at = datetime.utcnow()
        task.result = {
            "s3_url": f"https://s3.amazonaws.com/your-bucket/video_{task_id}.mp4",
            "duration": 300,
            "type": "video"
        }
        
        logger.info(f"Completed video podcast task: {task_id}")
        
    except Exception as e:
        logger.error(f"Error processing video podcast task {task_id}: {e}")
        task = task_storage[task_id]
        task.status = "failed"
        task.error = str(e)
        task.completed_at = datetime.utcnow()

# Deploy as web endpoint
@app.function(
    image=image,
    cpu=4,
    memory=8192,
    timeout=600,
    max_containers=20,
    min_containers=2
)
@modal.asgi_app()
def fastapi_app():
    """Deploy the complete FastAPI application with async polling"""
    return web_app 