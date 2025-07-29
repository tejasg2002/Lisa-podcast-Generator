import modal
import logging
import os
import tempfile
import requests
import boto3
import subprocess
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Literal, Dict
from pydantic import BaseModel, Field
import openai

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Modal app
app = modal.App("lisa-podcast-generator")

# Create image with dependencies for Modal 1.1
image = (
    modal.Image.debian_slim(python_version="3.10")
    .pip_install([
        "fastapi>=0.104.0",
        "uvicorn[standard]>=0.24.0",
        "boto3>=1.34.0",
        "requests>=2.31.0",
        "pydantic>=2.5.0",
        "python-multipart>=0.0.6",
        "openai>=1.3.0",
        "python-dotenv>=1.0.0",
        "typing-extensions>=4.8.0",
        "modal>=1.1.0"
    ])
    .apt_install([
        "ffmpeg"
    ])
)

# Pydantic Models
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

# Settings
class Settings:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-openai-key")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "your-elevenlabs-key")
    HEYGEN_API_KEY = os.getenv("HEYGEN_API_KEY", "your-heygen-key")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "your-aws-access-key")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "your-aws-secret-key")
    AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET_NAME", "your-s3-bucket")
    TMP_DIR = tempfile.gettempdir()

settings = Settings()

# Utility Functions
def generate_podcast_script(idea: str, host: str, guest: str, language: str, duration_minutes: int = 5) -> str:
    logger.info(f"Generating podcast script for topic: '{idea}'")
    logger.info(f"Target duration: {duration_minutes} minutes")
    logger.info(f"Language mode: {language}")
    logger.info(f"Using OpenAI GPT-4o-mini model")

    words_per_minute = 150
    target_words = duration_minutes * words_per_minute

    if language == "english":
        prompt = (
            f"Generate a podcast dialogue in MODERN ENGLISH between a female host named {host} "
            f"and a male guest named {guest} on the topic: '{idea}'. "
            f"The podcast should be approximately {duration_minutes} minutes long ({target_words} words).\n\n"
            f"IMPORTANT: Use MODERN, CONVERSATIONAL ENGLISH that people actually speak today, NOT formal/old-fashioned English.\n"
            f"Use contemporary expressions, casual language, and natural speech patterns.\n\n"
            f"Examples of modern English:\n"
            f"Format the dialogue as follows (NO ASTERISKS OR MARKDOWN):\n\n"
            f"{host}: [host's dialogue in modern conversational English]\n"
            f"{guest}: [guest's dialogue in modern conversational English]\n"
            f"{host}: [host's dialogue in modern conversational English]\n"
            f"and so on...\n\n"
            f"Keep it conversational and engaging. Alternate between {host} and {guest}. "
            f"Make sure each line starts with the speaker's name followed by a colon. "
            f"Structure the conversation with an introduction, main discussion points, and conclusion. "
            f"Use natural, modern English expressions, slang, and code-switching that young people use today."
        )
    else:
        prompt = (
            f"Generate a podcast dialogue in English between a female host named {host} "
            f"and a male guest named {guest} on the topic: '{idea}'. "
            f"The podcast should be approximately {duration_minutes} minutes long ({target_words} words).\n\n"
            f"IMPORTANT: Mix English with MODERN Hindi words/phrases that people actually use today. Use Devanagari script (हिंदी) for Hindi words, NOT Roman script (Hinglish).\n"
            f"Examples of modern mixed language:\n"
            f"- 'That's so cool! यार, यह तो बहुत कूल है!'\n"
            f"- 'I totally agree with you. मैं तो बिल्कुल agree करता हूं।'\n"
            f"- 'This topic is really interesting. यह topic तो बहुत interesting है।'\n"
            f"- 'Exactly what I was thinking! बस यही तो मैं सोच रहा था!'\n"
            f"- 'That's amazing! वाह, यह तो बहुत बढ़िया है!'\n\n"
            f"Format the dialogue as follows (NO ASTERISKS OR MARKDOWN):\n\n"
            f"{host}: [host's dialogue in English with modern Hindi words in Devanagari]\n"
            f"{guest}: [guest's dialogue in English with modern Hindi words in Devanagari]\n"
            f"{host}: [host's dialogue in English with modern Hindi words in Devanagari]\n"
            f"and so on...\n\n"
            f"Keep it conversational and engaging. Alternate between {host} and {guest}. "
            f"Make sure each line starts with the speaker's name followed by a colon. "
            f"Structure the conversation with an introduction, main discussion points, and conclusion. "
            f"Include modern Hindi words naturally in the conversation - use contemporary expressions, slang, and code-switching that young people use today."
        )

    logger.info("Sending request to OpenAI API...")
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful podcast script generator. Always format dialogue with speaker names followed by colons. DO NOT use asterisks, markdown, or any special formatting. For Hindi words, use Devanagari script (हिंदी) not Roman script (Hinglish). Use MODERN, CONVERSATIONAL Hindi that people actually speak today - casual, contemporary expressions, natural code-switching, and everyday language patterns."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=min(800, target_words * 2),
        temperature=0.7,
    )

    script = response.choices[0].message.content.strip()
    logger.info(f"OpenAI response received. Script length: {len(script)} characters")
    logger.info(f"Estimated words: {len(script.split())}")
    logger.info(f"Script preview: {script[:200]}...")

    return script

def synthesize_voice(text, voice_id, config, output_path):
    logger.info(f"ElevenLabs: Synthesizing voice for text (length: {len(text)})")
    logger.info(f"Voice ID: {voice_id}")
    logger.info(f"Output path: {output_path}")
    logger.info(f"Voice settings: stability={config.stability}, similarity_boost={config.similarity_boost}, style={config.style}")
    logger.info(f"Text preview: {text[:100]}...")

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

def generate_avatar_video(audio_url, avatar_id, background, output_path, voice_id=None, width=1280, height=720):
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

    if background and background.strip():
        if background.startswith('#'):
            video_inputs[0]["background"] = {
                "type": "color",
                "value": background
            }
        else:
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

    import json
    logger.info("=== COMPLETE HEYGEN API PAYLOAD ===")
    logger.info(json.dumps(payload, indent=2))
    logger.info("=== END HEYGEN API PAYLOAD ===")

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

    logger.info("Starting polling for video completion...")
    max_attempts = 60
    attempts = 0

    while attempts < max_attempts:
        attempts += 1
        logger.info(f"Polling attempt {attempts}/{max_attempts}")

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

    logger.info("Downloading video...")
    video_content = requests.get(video_url).content
    with open(output_path, "wb") as f:
        f.write(video_content)

    logger.info(f"Video saved to: {output_path}")
    return output_path

def merge_audio_clips(audio_paths, output_path):
    logger.info(f"Merging {len(audio_paths)} audio clips")
    logger.info(f"Output path: {output_path}")

    for path in audio_paths:
        if not os.path.exists(path):
            logger.error(f"Input file does not exist: {path}")
            raise FileNotFoundError(f"Input file does not exist: {path}")
        logger.info(f"Verified input file exists: {path}")

    output_dir = os.path.dirname(output_path)
    inputs_file = os.path.join(output_dir, "inputs.txt")

    logger.info(f"Creating inputs file: {inputs_file}")
    with open(inputs_file, "w") as f:
        for path in audio_paths:
            abs_path = os.path.abspath(path)
            f.write(f"file '{abs_path}'\n")
            logger.info(f"Added to inputs: {abs_path}")

    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", inputs_file,
        "-acodec", "libmp3lame", "-ar", "44100", "-ab", "128k", output_path
    ]

    logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info("FFmpeg audio merge completed successfully")
        logger.info(f"FFmpeg stdout: {result.stdout}")
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg failed with return code: {e.returncode}")
        logger.error(f"FFmpeg stderr: {e.stderr}")
        logger.error(f"FFmpeg stdout: {e.stdout}")
        raise

    try:
        os.remove(inputs_file)
        logger.info(f"Cleaned up inputs file: {inputs_file}")
    except:
        logger.warning(f"Could not remove inputs file: {inputs_file}")

    return output_path

def merge_video_clips(video_paths, output_path):
    logger.info(f"Merging {len(video_paths)} video clips")
    logger.info(f"Output path: {output_path}")

    for path in video_paths:
        if not os.path.exists(path):
            logger.error(f"Input file does not exist: {path}")
            raise FileNotFoundError(f"Input file does not exist: {path}")
        logger.info(f"Verified input file exists: {path}")

    output_dir = os.path.dirname(output_path)
    inputs_file = os.path.join(output_dir, "inputs.txt")

    logger.info(f"Creating inputs file: {inputs_file}")
    with open(inputs_file, "w") as f:
        for path in video_paths:
            abs_path = os.path.abspath(path)
            f.write(f"file '{abs_path}'\n")
            logger.info(f"Added to inputs: {abs_path}")

    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", inputs_file,
        "-c", "copy", output_path
    ]

    logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info("FFmpeg video merge completed successfully")
        logger.info(f"FFmpeg stdout: {result.stdout}")
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg failed with return code: {e.returncode}")
        logger.error(f"FFmpeg stderr: {e.stderr}")
        logger.error(f"FFmpeg stdout: {e.stdout}")
        raise

    try:
        os.remove(inputs_file)
        logger.info(f"Cleaned up inputs file: {inputs_file}")
    except:
        logger.warning(f"Could not remove inputs file: {inputs_file}")

    return output_path

def crop_video_to_portrait(input_path, output_path):
    logger.info(f"Cropping video from landscape to portrait")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")

    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-vf", "crop=720:720:280:0,scale=720:720,pad=720:1280:0:280:black",
        "-c:v", "libx264",
        "-c:a", "copy",
        output_path
    ]

    logger.info(f"Running FFmpeg crop and pad command")
    logger.info(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info("Portrait video created successfully")

        verify_cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", output_path
        ]
        verify_result = subprocess.run(verify_cmd, check=True, capture_output=True, text=True)
        logger.info(f"Output video info: {verify_result.stdout}")

    except subprocess.CalledProcessError as e:
        logger.error(f"Portrait creation failed: {e.stderr}")
        raise
    return output_path

def upload_to_s3(file_path, s3_key):
    logger.info(f"Uploading file to S3: {file_path}")
    logger.info(f"S3 key: {s3_key}")
    logger.info(f"S3 bucket: {settings.AWS_S3_BUCKET}")

    try:
        s3 = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        s3.upload_file(file_path, settings.AWS_S3_BUCKET, s3_key)
        url = f"https://{settings.AWS_S3_BUCKET}.s3.amazonaws.com/{s3_key}"
        logger.info(f"File uploaded successfully to: {url}")
        return url
    except Exception as e:
        error_msg = f"S3 upload failed: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)

def process_dialogue(script, host, guest):
    logger.info(f"Processing dialogue with {host} (host) and {guest} (guest)")
    
    segments = []
    lines = script.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Look for speaker pattern: "Speaker: dialogue"
        if ':' in line:
            speaker_part, dialogue_part = line.split(':', 1)
            speaker = speaker_part.strip()
            dialogue = dialogue_part.strip()
            
            if speaker and dialogue:
                if speaker.lower() == host.lower():
                    segments.append({
                        'speaker': 'host',
                        'text': dialogue,
                        'voice_id': 'host_voice_id',  # Will be replaced
                        'avatar_id': 'host_avatar_id'  # Will be replaced
                    })
                elif speaker.lower() == guest.lower():
                    segments.append({
                        'speaker': 'guest',
                        'text': dialogue,
                        'voice_id': 'guest_voice_id',  # Will be replaced
                        'avatar_id': 'guest_avatar_id'  # Will be replaced
                    })
                else:
                    logger.warning(f"Unknown speaker: {speaker}")
    
    logger.info(f"Processed {len(segments)} dialogue segments")
    return segments

def create_audio_podcast(data):
    logger.info("=== STARTING AUDIO PODCAST GENERATION ===")
    
    # Step 1: Generate script
    if data.input_type == "idea":
        logger.info("Generating script from idea...")
        script = generate_podcast_script(data.input_text, data.host_name, data.guest_name, data.language, data.duration_minutes)
    else:
        logger.info("Using provided script...")
        script = data.input_text
    
    # Step 2: Process dialogue
    logger.info("Processing dialogue into segments...")
    segments = process_dialogue(script, data.host_name, data.guest_name)
    
    if not segments:
        raise Exception("No dialogue segments found in script")
    
    logger.info(f"Found {len(segments)} dialogue segments")
    
    # Step 3: Generate audio files concurrently
    logger.info("Generating audio files concurrently...")
    audio_files = []
    max_concurrent = min(10, len(segments))
    
    with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
        futures = []
        for i, segment in enumerate(segments):
            voice_id = data.host_voice_id if segment['speaker'] == 'host' else data.guest_voice_id
            output_path = os.path.join(settings.TMP_DIR, f"audio_segment_{i}.mp3")
            
            future = executor.submit(
                synthesize_voice,
                segment['text'],
                voice_id,
                data.elevenlabs_config,
                output_path
            )
            futures.append((future, output_path))
        
        for future, output_path in futures:
            try:
                result = future.result()
                audio_files.append(output_path)
                logger.info(f"Audio segment generated: {output_path}")
            except Exception as e:
                logger.error(f"Failed to generate audio segment: {e}")
                raise
    
    # Step 4: Merge audio files
    logger.info("Merging audio files...")
    merged_audio = os.path.join(settings.TMP_DIR, "merged_audio.mp3")
    merge_audio_clips(audio_files, merged_audio)
    
    # Step 5: Upload to S3
    logger.info("Uploading to S3...")
    s3_key = f"podcasts/audio/{int(time.time())}.mp3"
    s3_url = upload_to_s3(merged_audio, s3_key)
    
    # Step 6: Cleanup
    logger.info("Cleaning up temporary files...")
    for audio_file in audio_files:
        try:
            os.remove(audio_file)
        except:
            pass
    try:
        os.remove(merged_audio)
    except:
        pass
    
    duration = len(segments) * 10  # Rough estimate
    logger.info(f"Audio podcast generation completed. S3 URL: {s3_url}")
    return s3_url, duration

def create_video_podcast(data):
    logger.info("=== STARTING VIDEO PODCAST GENERATION ===")
    
    # Step 1: Generate script
    if data.input_type == "idea":
        logger.info("Generating script from idea...")
        script = generate_podcast_script(data.input_text, data.host_name, data.guest_name, data.language, data.duration_minutes)
    else:
        logger.info("Using provided script...")
        script = data.input_text
    
    # Step 2: Process dialogue
    logger.info("Processing dialogue into segments...")
    segments = process_dialogue(script, data.host_name, data.guest_name)
    
    if not segments:
        raise Exception("No dialogue segments found in script")
    
    logger.info(f"Found {len(segments)} dialogue segments")
    
    # Step 3a: Generate all audio files concurrently
    logger.info("Generating audio files concurrently...")
    audio_files = []
    max_concurrent_audio = min(10, len(segments))
    
    with ThreadPoolExecutor(max_workers=max_concurrent_audio) as executor:
        futures = []
        for i, segment in enumerate(segments):
            voice_id = data.host_voice_id if segment['speaker'] == 'host' else data.guest_voice_id
            output_path = os.path.join(settings.TMP_DIR, f"audio_segment_{i}.mp3")
            
            future = executor.submit(
                synthesize_voice,
                segment['text'],
                voice_id,
                data.elevenlabs_config,
                output_path
            )
            futures.append((future, output_path, i))
        
        for future, output_path, i in futures:
            try:
                result = future.result()
                audio_files.append((output_path, i))
                logger.info(f"Audio segment {i} generated: {output_path}")
            except Exception as e:
                logger.error(f"Failed to generate audio segment {i}: {e}")
                raise
    
    # Step 3b: Upload all audio files to S3 concurrently
    logger.info("Uploading audio files to S3 concurrently...")
    audio_urls = []
    max_s3_concurrent = min(5, len(segments))
    
    with ThreadPoolExecutor(max_workers=max_s3_concurrent) as executor:
        futures = []
        for audio_path, i in audio_files:
            s3_key = f"podcasts/temp/audio_{int(time.time())}_{i}.mp3"
            future = executor.submit(upload_to_s3, audio_path, s3_key)
            futures.append((future, i))
        
        for future, i in futures:
            try:
                audio_url = future.result()
                audio_urls.append((audio_url, i))
                logger.info(f"Audio segment {i} uploaded: {audio_url}")
            except Exception as e:
                logger.error(f"Failed to upload audio segment {i}: {e}")
                raise
    
    # Step 3c: Generate videos concurrently
    logger.info("Generating videos concurrently...")
    video_files = []
    
    def generate_video_segment(audio_url, avatar_id, segment_index):
        out_video = os.path.join(settings.TMP_DIR, f"video_segment_{segment_index}.mp4")
        cropped_video = os.path.join(settings.TMP_DIR, f"video_segment_{segment_index}_cropped.mp4")
        
        # Always generate landscape videos (1280x720) for better compatibility
        width, height = 1280, 720
        generate_avatar_video(audio_url, avatar_id, data.heygen_config.background, out_video, width=width, height=height)
        
        # Crop to portrait if needed
        if data.orientation == "portrait":
            crop_video_to_portrait(out_video, cropped_video)
            # Replace original with cropped version
            os.remove(out_video)
            os.rename(cropped_video, out_video)
        
        return out_video, segment_index
    
    with ThreadPoolExecutor(max_workers=len(segments)) as executor:
        futures = []
        for audio_url, i in audio_urls:
            avatar_id = data.heygen_config.host_avatar_id if segments[i]['speaker'] == 'host' else data.heygen_config.guest_avatar_id
            future = executor.submit(generate_video_segment, audio_url, avatar_id, i)
            futures.append(future)
        
        for future in futures:
            try:
                video_path, segment_index = future.result()
                video_files.append((video_path, segment_index))
                logger.info(f"Video segment {segment_index} generated: {video_path}")
            except Exception as e:
                logger.error(f"Failed to generate video segment: {e}")
                raise
    
    # Step 4: Merge video files in correct sequence
    logger.info("Merging video files in sequence...")
    ordered_video_paths = [path for path, _ in sorted(video_files, key=lambda x: x[1])]
    merged_video = os.path.join(settings.TMP_DIR, "merged_video.mp4")
    merge_video_clips(ordered_video_paths, merged_video)
    
    # Step 5: Upload final video to S3
    logger.info("Uploading final video to S3...")
    s3_key = f"podcasts/video/{int(time.time())}.mp4"
    s3_url = upload_to_s3(merged_video, s3_key)
    
    # Step 6: Cleanup
    logger.info("Cleaning up temporary files...")
    for audio_path, _ in audio_files:
        try:
            os.remove(audio_path)
        except:
            pass
    for video_path, _ in video_files:
        try:
            os.remove(video_path)
        except:
            pass
    try:
        os.remove(merged_video)
    except:
        pass
    
    duration = len(segments) * 10  # Rough estimate
    logger.info(f"Video podcast generation completed. S3 URL: {s3_url}")
    return s3_url, duration

# Create FastAPI app
from fastapi import FastAPI

web_app = FastAPI(title="LISA Podcast Generator", version="1.1.0")

@web_app.post("/v1/lisa-audio-podcast")
def lisa_audio_podcast(data: AudioPodcastRequest):
    logger.info("=== AUDIO PODCAST REQUEST RECEIVED ===")
    logger.info(f"Request data: {data}")
    s3_url, duration = create_audio_podcast(data)
    logger.info(f"Audio podcast completed. S3 URL: {s3_url}")
    return {"status": "success", "s3_url": s3_url, "duration": duration}

@web_app.post("/v1/lisa-video-podcast")
def lisa_video_podcast(data: VideoPodcastRequest):
    logger.info("=== VIDEO PODCAST REQUEST RECEIVED ===")
    logger.info(f"Request data: {data}")
    s3_url, duration = create_video_podcast(data)
    logger.info(f"Video podcast completed. S3 URL: {s3_url}")
    return {"status": "success", "s3_url": s3_url, "duration": duration}

# Deploy the complete FastAPI application with Modal 1.1
@app.function(
    image=image,
    cpu=2,
    memory=4096,
    timeout=300,
    min_containers=0,  # Start idle, scale up when needed
    max_containers=10,
    secrets=[modal.Secret.from_name("lisa-podcast-secrets")]
)
@modal.asgi_app()
def fastapi_app():
    """Deploy the complete FastAPI application"""
    return web_app

# Individual endpoint functions for specific use cases
@app.function(
    image=image,
    cpu=2,
    memory=4096,
    timeout=300,
    min_containers=0,  # Start idle, scale up when needed
    max_containers=5,
    secrets=[modal.Secret.from_name("lisa-podcast-secrets")]
)
def audio_podcast_function(data: AudioPodcastRequest):
    """Audio podcast generation function"""
    return lisa_audio_podcast(data)

@app.function(
    image=image,
    cpu=4,
    memory=8192,
    timeout=600,
    min_containers=0,  # Start idle, scale up when needed
    max_containers=3,
    secrets=[modal.Secret.from_name("lisa-podcast-secrets")]
)
def video_podcast_function(data: VideoPodcastRequest):
    """Video podcast generation function"""
    return lisa_video_podcast(data)