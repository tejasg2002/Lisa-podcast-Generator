import logging
from fastapi import FastAPI
from app.models import (
    AudioPodcastRequest, VideoPodcastRequest
)
from app.services.podcast import create_audio_podcast, create_video_podcast

# Configure logging at application level
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console handler
        logging.FileHandler('app.log')  # File handler
    ]
)

# Create logger for this module
logger = logging.getLogger(__name__)

app = FastAPI()

@app.post("/v1/lisa-audio-podcast")
def lisa_audio_podcast(data: AudioPodcastRequest):
    logger.info("=== AUDIO PODCAST REQUEST RECEIVED ===")
    logger.info(f"Request data: {data}")
    s3_url, duration = create_audio_podcast(data)
    logger.info(f"Audio podcast completed. S3 URL: {s3_url}")
    return {"status": "success", "s3_url": s3_url, "duration": duration}

@app.post("/v1/lisa-video-podcast")
def lisa_video_podcast(data: VideoPodcastRequest):
    logger.info("=== VIDEO PODCAST REQUEST RECEIVED ===")
    logger.info(f"Request data: {data}")
    s3_url, duration = create_video_podcast(data)
    logger.info(f"Video podcast completed. S3 URL: {s3_url}")
    return {"status": "success", "s3_url": s3_url, "duration": duration} 