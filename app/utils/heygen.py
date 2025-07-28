import requests
import time
import logging
from app.config import settings

logger = logging.getLogger(__name__)

def generate_avatar_video(audio_url, avatar_id, background, output_path, voice_id=None, width=1280, height=720):
    """
    Generate a Heygen talking photo video using a public audio URL.
    - audio_url: Public URL to the audio file (e.g., S3)
    - avatar_id: Heygen talking photo ID
    - background: Background config (string or dict) - optional
    - output_path: Where to save the final video
    - voice_id: Optional Heygen voice ID (if using text input)
    - width, height: Video dimensions
    """
    logger.info(f"Heygen: Generating talking photo video")
    logger.info(f"Audio URL: {audio_url}")
    logger.info(f"Talking Photo ID: {avatar_id}")
    logger.info(f"Background: {background} (type: {type(background)})")
    logger.info(f"Output path: {output_path}")
    
    api_key = settings.HEYGEN_API_KEY
    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json"
    }
    
    # Prepare video_inputs for audio - using the correct Heygen API structure
    video_inputs = [{
        "character": {
            "type": "talking_photo",
            "talking_photo_id": avatar_id,
            "scale": 1,
            "talking_style": "stable",
            "expression": "default",
            "avatar_style": "circle"
        },
        "voice": {
            "type": "audio",
            "audio_url": audio_url
        }
    }]
    
    # Add background only if provided and not None
    if background and background.strip():
        if background.startswith('#'):
            # Color background - use simple structure
            video_inputs[0]["background"] = {
                "type": "color",
                "value": background
            }
        else:
            # Image background - use nested structure
            video_inputs[0]["background"] = {
                "type": "image",
                "image": {
                    "url": background
                }
            }
    
    payload = {
        "video_inputs": video_inputs,
        "dimension": {
            "width": width,
            "height": height
        }
    }
    
    logger.info(f"Heygen payload: {payload}")
    
    # Log the complete JSON payload in a readable format
    logger.info("=== COMPLETE HEYGEN API PAYLOAD ===")
    import json
    logger.info(json.dumps(payload, indent=2))
    logger.info("=== END HEYGEN API PAYLOAD ===")
    
    # 1. Submit video generation request
    logger.info("Sending request to Heygen API...")
    resp = requests.post(
        "https://api.heygen.com/v2/video/generate",
        headers=headers,
        json=payload
    )
    
    logger.info(f"Heygen response status: {resp.status_code}")
    logger.info(f"Heygen response: {resp.text}")
    
    if resp.status_code != 200:
        raise Exception(f"Heygen video generation error: {resp.text}")
    
    response_data = resp.json()
    if response_data.get("error"):
        raise Exception(f"Heygen video generation error: {response_data['error']}")
    
    video_id = response_data["data"]["video_id"]
    logger.info(f"Video ID: {video_id}")
    
    # 2. Poll for video status using the correct polling endpoint
    logger.info("Starting polling for video completion...")
    max_attempts = 60  # 5 minutes max (60 * 5 seconds)
    attempts = 0
    
    while attempts < max_attempts:
        attempts += 1
        logger.info(f"Polling attempt {attempts}/{max_attempts}")
        
        # Use the correct polling endpoint
        status_resp = requests.get(
            f"https://api.heygen.com/v1/video_status.get",
            headers=headers,
            params={"video_id": video_id}
        )
        
        if status_resp.status_code != 200:
            logger.error(f"Status check failed: {status_resp.text}")
            time.sleep(5)
            continue
            
        status_data = status_resp.json()
        if status_data.get("error"):
            logger.error(f"Status check error: {status_data['error']}")
            time.sleep(5)
            continue
            
        video_status = status_data["data"]["status"]
        logger.info(f"Video status: {video_status}")
        
        if video_status == "completed":
            video_url = status_data["data"]["video_url"]
            logger.info(f"Video completed successfully: {video_url}")
            break
        elif video_status in ("processing", "pending", "started"):
            logger.info(f"Video still {video_status}, waiting 5 seconds...")
            time.sleep(5)
        elif video_status == "failed":
            raise Exception(f"Heygen video generation failed: {status_data['data']}")
        else:
            logger.warning(f"Unknown status: {video_status}, waiting 5 seconds...")
            time.sleep(5)
    else:
        raise Exception(f"Video generation timed out after {max_attempts} attempts")
    
    # 3. Download the video
    logger.info("Downloading video...")
    video_content = requests.get(video_url).content
    with open(output_path, "wb") as f:
        f.write(video_content)
    
    logger.info(f"Video saved to: {output_path}")
    return output_path 