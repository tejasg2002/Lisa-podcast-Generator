import os
import logging
import re
from app.utils.openai_gpt import generate_podcast_script
from app.utils.elevenlabs import synthesize_voice
from app.utils.heygen import generate_avatar_video
from app.utils.ffmpeg_merge import merge_audio_clips, merge_video_clips
from app.utils.s3 import upload_to_s3
from app.config import settings
from concurrent.futures import ThreadPoolExecutor, as_completed

# Get logger for this module
logger = logging.getLogger(__name__)

def process_dialogue(script, host, guest):
    logger.info(f"Processing dialogue script for {host} and {guest}")
    logger.info(f"Script preview: {script[:200]}...")
    
    # Split into lines and clean up
    lines = [line.strip() for line in script.split("\n") if line.strip()]
    logger.info(f"Total lines in script: {len(lines)}")
    
    segments = []
    for i, line in enumerate(lines):
        logger.info(f"Processing line {i+1}: {line[:100]}...")
        
        # Try different patterns for dialogue
        # Pattern 1: "Name:" or "**Name:**" (with asterisks)
        if re.match(f"^\\*?\\*?{re.escape(host)}\\*?\\*?:", line, re.IGNORECASE):
            # Remove asterisks and extract text after colon
            text = re.sub(f"^\\*?\\*?{re.escape(host)}\\*?\\*?:\\s*", "", line, flags=re.IGNORECASE).strip()
            if text:
                segments.append(("host", text))
                logger.info(f"Found host dialogue: {text[:50]}...")
        elif re.match(f"^\\*?\\*?{re.escape(guest)}\\*?\\*?:", line, re.IGNORECASE):
            # Remove asterisks and extract text after colon
            text = re.sub(f"^\\*?\\*?{re.escape(guest)}\\*?\\*?:\\s*", "", line, flags=re.IGNORECASE).strip()
            if text:
                segments.append(("guest", text))
                logger.info(f"Found guest dialogue: {text[:50]}...")
        
        # Pattern 2: "Name - text"
        elif re.match(f"^{re.escape(host)} -", line, re.IGNORECASE):
            text = line[len(host):].strip(" -").strip()
            if text:
                segments.append(("host", text))
                logger.info(f"Found host dialogue (dash): {text[:50]}...")
        elif re.match(f"^{re.escape(guest)} -", line, re.IGNORECASE):
            text = line[len(guest):].strip(" -").strip()
            if text:
                segments.append(("guest", text))
                logger.info(f"Found guest dialogue (dash): {text[:50]}...")
        
        # Pattern 3: "Name (speaking): text" or "**Name (speaking):** text"
        elif re.match(f"^\\*?\\*?{re.escape(host)}.*:", line, re.IGNORECASE):
            # Extract text after the first colon
            parts = line.split(":", 1)
            if len(parts) > 1:
                text = parts[1].strip()
                if text:
                    segments.append(("host", text))
                    logger.info(f"Found host dialogue (colon): {text[:50]}...")
        elif re.match(f"^\\*?\\*?{re.escape(guest)}.*:", line, re.IGNORECASE):
            # Extract text after the first colon
            parts = line.split(":", 1)
            if len(parts) > 1:
                text = parts[1].strip()
                if text:
                    segments.append(("guest", text))
                    logger.info(f"Found guest dialogue (colon): {text[:50]}...")
    
    logger.info(f"Extracted {len(segments)} dialogue segments")
    
    # If no segments found, create a fallback
    if len(segments) == 0:
        logger.warning("No dialogue segments found! Creating fallback segments...")
        # Split the script into sentences and alternate between host and guest
        sentences = re.split(r'[.!?]+', script)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        for i, sentence in enumerate(sentences[:10]):  # Limit to 10 sentences
            speaker = "host" if i % 2 == 0 else "guest"
            segments.append((speaker, sentence))
            logger.info(f"Created fallback {speaker} segment: {sentence[:50]}...")
    
    return segments

def create_audio_podcast(data):
    logger.info("=== STARTING AUDIO PODCAST GENERATION ===")
    logger.info(f"Input type: {data.input_type}")
    logger.info(f"Language: {data.language}")
    logger.info(f"Target duration: {data.duration_minutes} minutes")
    logger.info(f"Host: {data.host_name} (Voice ID: {data.host_voice_id})")
    logger.info(f"Guest: {data.guest_name} (Voice ID: {data.guest_voice_id})")
    
    # Step 1: Generate or use script
    if data.input_type == "idea":
        logger.info("Generating podcast script from idea...")
        script = generate_podcast_script(data.input_text, data.host_name, data.guest_name, data.language, data.duration_minutes)
        logger.info(f"Generated script length: {len(script)} characters")
    else:
        logger.info("Using provided script...")
        script = data.input_text
        logger.info(f"Script length: {len(script)} characters")
    
    # Step 2: Process dialogue
    logger.info("Processing dialogue into segments...")
    segments = process_dialogue(script, data.host_name, data.guest_name)
    logger.info(f"Created {len(segments)} audio segments")
    
    # Step 3: Generate audio files
    audio_paths = []
    logger.info("Generating audio files for each segment...")
    for idx, (speaker, text) in enumerate(segments):
        logger.info(f"Processing segment {idx + 1}/{len(segments)} - {speaker}: {text[:50]}...")
        voice_id = data.host_voice_id if speaker == "host" else data.guest_voice_id
        out_path = os.path.join(settings.TMP_DIR, f"audio_{idx}.mp3")
        logger.info(f"Generating audio for {speaker} using voice ID: {voice_id}")
        synthesize_voice(text, voice_id, data.elevenlabs_config, out_path)
        audio_paths.append(out_path)
        logger.info(f"Audio segment {idx + 1} saved to: {out_path}")
    
    # Step 4: Merge audio files
    logger.info("Merging audio segments...")
    merged_audio = os.path.join(settings.TMP_DIR, "final_podcast.mp3")
    merge_audio_clips(audio_paths, merged_audio)
    logger.info(f"Audio merged successfully: {merged_audio}")
    
    # Step 5: Upload to S3
    logger.info("Uploading final audio to S3...")
    s3_key = f"podcasts/audio/final_{os.path.basename(merged_audio)}"
    s3_url = upload_to_s3(merged_audio, s3_key)
    logger.info(f"Audio uploaded to S3: {s3_url}")
    
    # Step 6: Cleanup
    logger.info("Cleaning up temporary files...")
    for path in audio_paths:
        try:
            os.remove(path)
            logger.info(f"Removed: {path}")
        except:
            pass
    try:
        os.remove(merged_audio)
        logger.info(f"Removed: {merged_audio}")
    except:
        pass
    
    duration = len(segments) * 30  # Dummy duration
    logger.info(f"=== AUDIO PODCAST GENERATION COMPLETE ===")
    logger.info(f"Final duration: {duration} seconds")
    logger.info(f"S3 URL: {s3_url}")
    
    return s3_url, duration

def create_video_podcast(data):
    logger.info("=== STARTING VIDEO PODCAST GENERATION ===")
    logger.info(f"Input type: {data.input_type}")
    logger.info(f"Language: {data.language}")
    logger.info(f"Orientation: {data.orientation}")
    logger.info(f"Target duration: {data.duration_minutes} minutes")
    logger.info(f"Host: {data.host_name} (Voice ID: {data.host_voice_id}, Avatar ID: {data.heygen_config.host_avatar_id})")
    logger.info(f"Guest: {data.guest_name} (Voice ID: {data.guest_voice_id}, Avatar ID: {data.heygen_config.guest_avatar_id})")
    logger.info(f"Background: {data.heygen_config.background}")
    
    # Step 1: Generate or use script
    if data.input_type == "idea":
        logger.info("Generating podcast script from idea...")
        script = generate_podcast_script(data.input_text, data.host_name, data.guest_name, data.language, data.duration_minutes)
        logger.info(f"Generated script length: {len(script)} characters")
    else:
        logger.info("Using provided script...")
        script = data.input_text
        logger.info(f"Script length: {len(script)} characters")
    
    # Step 2: Process dialogue
    logger.info("Processing dialogue into segments...")
    segments = process_dialogue(script, data.host_name, data.guest_name)
    logger.info(f"Created {len(segments)} video segments")
    
    # Step 3: Generate audio and video files with concurrency
    video_paths = []
    logger.info("Generating audio and video files for each segment with concurrency...")
    
    # Step 3a: Generate all audio files concurrently
    logger.info("Starting concurrent audio generation (all requests at once)...")
    
    def generate_audio_segment(args):
        idx, speaker, text, voice_id = args
        out_audio = os.path.join(settings.TMP_DIR, f"audio_{idx}.mp3")
        
        logger.info(f"Generating audio for segment {idx + 1} - {speaker} using voice ID: {voice_id}")
        synthesize_voice(text, voice_id, data.elevenlabs_config, out_audio)
        logger.info(f"Audio segment {idx + 1} saved to: {out_audio}")
        return idx, out_audio
    
    # Prepare arguments for concurrent audio generation
    audio_args = []
    for idx, (speaker, text) in enumerate(segments):
        voice_id = data.host_voice_id if speaker == "host" else data.guest_voice_id
        audio_args.append((idx, speaker, text, voice_id))
    
    # Execute audio generation with ElevenLabs concurrency limit (max 10 concurrent)
    audio_files = {}  # {idx: file_path}
    max_concurrent = min(10, len(segments))  # Respect ElevenLabs limit of 10
    logger.info(f"Using max {max_concurrent} concurrent audio generation requests (ElevenLabs limit)")
    
    with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
        # Submit all audio generation tasks
        future_to_idx = {executor.submit(generate_audio_segment, args): args[0] for args in audio_args}
        
        # Collect results as they complete
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                segment_idx, audio_path = future.result()
                audio_files[segment_idx] = audio_path
                logger.info(f"Completed audio generation for segment {idx + 1}")
            except Exception as exc:
                logger.error(f"Audio generation for segment {idx + 1} generated an exception: {exc}")
                raise
    
    # Step 3b: Upload all audio files to S3 concurrently
    logger.info("Starting concurrent S3 uploads for audio files (all requests at once)...")
    
    def upload_audio_to_s3(args):
        idx, audio_path = args
        s3_audio_key = f"podcasts/video/audio_{idx}.mp3"
        
        logger.info(f"Uploading audio segment {idx + 1} to S3...")
        s3_audio_url = upload_to_s3(audio_path, s3_audio_key)
        logger.info(f"Audio segment {idx + 1} uploaded to S3: {s3_audio_url}")
        return idx, s3_audio_url
    
    # Prepare arguments for concurrent S3 uploads
    upload_args = [(idx, audio_path) for idx, audio_path in audio_files.items()]
    
    # Execute S3 uploads with reasonable concurrency limit (max 5 concurrent)
    audio_urls = {}  # {idx: s3_url}
    max_s3_concurrent = min(5, len(segments))  # Reasonable S3 concurrency limit
    logger.info(f"Using max {max_s3_concurrent} concurrent S3 upload requests")
    
    with ThreadPoolExecutor(max_workers=max_s3_concurrent) as executor:
        # Submit all S3 upload tasks
        future_to_idx = {executor.submit(upload_audio_to_s3, args): args[0] for args in upload_args}
        
        # Collect results as they complete
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                segment_idx, s3_url = future.result()
                audio_urls[segment_idx] = s3_url
                logger.info(f"Completed S3 upload for segment {idx + 1}")
            except Exception as exc:
                logger.error(f"S3 upload for segment {idx + 1} generated an exception: {exc}")
                raise
    
    # Step 3c: Generate videos concurrently using ThreadPoolExecutor
    logger.info("Starting concurrent Heygen video generation (all requests at once)...")
    
    def generate_video_segment(args):
        idx, speaker, audio_url, avatar_id = args
        out_video = os.path.join(settings.TMP_DIR, f"video_{idx}.mp4")
        
        # Always generate landscape videos (1280x720) for better compatibility
        width, height = 1280, 720  # Always landscape for Heygen
        
        logger.info(f"Generating video for segment {idx + 1} - {speaker} using avatar ID: {avatar_id}")
        logger.info(f"Video dimensions: {width}x{height} (landscape - will crop to {data.orientation} if needed)")
        generate_avatar_video(audio_url, avatar_id, data.heygen_config.background, out_video, width=width, height=height)
        logger.info(f"Video segment {idx + 1} saved to: {out_video}")
        
        # Crop to portrait if needed
        if data.orientation == "portrait":
            logger.info(f"Cropping video segment {idx + 1} to portrait orientation...")
            cropped_video = os.path.join(settings.TMP_DIR, f"video_{idx}_cropped.mp4")
            from app.utils.ffmpeg_merge import crop_video_to_portrait
            crop_video_to_portrait(out_video, cropped_video)
            # Replace original with cropped version
            os.remove(out_video)
            os.rename(cropped_video, out_video)
            logger.info(f"Video segment {idx + 1} cropped to portrait: {out_video}")
        
        return idx, out_video
    
    # Prepare arguments for concurrent video generation
    video_args = []
    for idx, (speaker, text) in enumerate(segments):
        avatar_id = data.heygen_config.host_avatar_id if speaker == "host" else data.heygen_config.guest_avatar_id
        video_args.append((idx, speaker, audio_urls[idx], avatar_id))
    
    # Execute video generation with unlimited concurrent workers (all at once for Heygen)
    video_files = {}  # {idx: file_path}
    logger.info(f"Using unlimited concurrent Heygen video generation requests (all {len(segments)} at once)")
    
    with ThreadPoolExecutor(max_workers=len(segments)) as executor:
        # Submit all video generation tasks at once
        future_to_idx = {executor.submit(generate_video_segment, args): args[0] for args in video_args}
        
        # Collect results as they complete
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                segment_idx, video_path = future.result()
                video_files[segment_idx] = video_path
                logger.info(f"Completed video generation for segment {idx + 1}")
            except Exception as exc:
                logger.error(f"Video generation for segment {idx + 1} generated an exception: {exc}")
                raise
    
    # Step 4: Merge video files in correct sequence
    logger.info("Preparing video files for merging in correct sequence...")
    # Create ordered list of video paths based on segment indices
    ordered_video_paths = []
    for idx in range(len(segments)):
        if idx in video_files:
            ordered_video_paths.append(video_files[idx])
            logger.info(f"Added video segment {idx + 1} to merge sequence: {video_files[idx]}")
        else:
            logger.error(f"Missing video segment {idx + 1} for merging!")
            raise Exception(f"Missing video segment {idx + 1}")
    
    logger.info(f"Merging {len(ordered_video_paths)} video segments in sequence...")
    merged_video = os.path.join(settings.TMP_DIR, "final_podcast.mp4")
    merge_video_clips(ordered_video_paths, merged_video)
    logger.info(f"Video merged successfully: {merged_video}")
    
    # Step 5: Upload to S3
    logger.info("Uploading final video to S3...")
    s3_key = f"podcasts/video/final_{os.path.basename(merged_video)}"
    s3_url = upload_to_s3(merged_video, s3_key)
    logger.info(f"Video uploaded to S3: {s3_url}")
    
    # Step 6: Cleanup
    logger.info("Cleaning up temporary files...")
    for idx in range(len(segments)):
        try:
            os.remove(os.path.join(settings.TMP_DIR, f"audio_{idx}.mp3"))
            logger.info(f"Removed: audio_{idx}.mp3")
        except:
            pass
        try:
            os.remove(os.path.join(settings.TMP_DIR, f"video_{idx}.mp4"))
            logger.info(f"Removed: video_{idx}.mp4")
        except:
            pass
    try:
        os.remove(merged_video)
        logger.info(f"Removed: {merged_video}")
    except:
        pass
    
    duration = len(video_paths) * 30  # Dummy duration
    logger.info(f"=== VIDEO PODCAST GENERATION COMPLETE ===")
    logger.info(f"Final duration: {duration} seconds")
    logger.info(f"S3 URL: {s3_url}")
    
    return s3_url, duration 