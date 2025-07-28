import requests
import logging
from app.config import settings

logger = logging.getLogger(__name__)

def synthesize_voice(text, voice_id, config, output_path):
    logger.info(f"ElevenLabs: Synthesizing voice for text (length: {len(text)})")
    logger.info(f"Voice ID: {voice_id}")
    logger.info(f"Output path: {output_path}")
    logger.info(f"Voice settings: stability={config.stability}, similarity_boost={config.similarity_boost}, style={config.style}")
    logger.info(f"Text preview: {text[:100]}...")
    
    # Check if text contains Devanagari script
    devanagari_chars = [char for char in text if '\u0900' <= char <= '\u097F']
    if devanagari_chars:
        logger.info(f"Detected {len(devanagari_chars)} Devanagari characters in text")
        logger.info(f"Devanagari characters: {devanagari_chars[:10]}...")
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": settings.ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "voice_settings": {
            "stability": config.stability,
            "similarity_boost": config.similarity_boost,
            "style": config.style,
            "speed": getattr(config, "speed", 1.0)
        },
        "model_id": config.model_id,
        "output_format": "mp3_44100_128"
    }
    
    logger.info("Sending request to ElevenLabs API...")
    response = requests.post(url, json=payload, stream=True, headers=headers)
    
    if response.status_code == 200:
        logger.info("ElevenLabs API response successful")
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logger.info(f"Audio file saved to: {output_path}")
        return output_path
    else:
        error_msg = f"ElevenLabs error: {response.text}"
        logger.error(error_msg)
        raise Exception(error_msg) 