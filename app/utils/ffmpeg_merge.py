import subprocess
import os
import logging

logger = logging.getLogger(__name__)

def merge_audio_clips(audio_paths, output_path):
    logger.info(f"Merging {len(audio_paths)} audio clips")
    logger.info(f"Output path: {output_path}")
    
    # Verify all input files exist
    for path in audio_paths:
        if not os.path.exists(path):
            logger.error(f"Input file does not exist: {path}")
            raise FileNotFoundError(f"Input file does not exist: {path}")
        logger.info(f"Verified input file exists: {path}")
    
    # Create inputs.txt in the same directory as output_path
    output_dir = os.path.dirname(output_path)
    inputs_file = os.path.join(output_dir, "inputs.txt")
    
    logger.info(f"Creating inputs file: {inputs_file}")
    with open(inputs_file, "w") as f:
        for path in audio_paths:
            # Use absolute paths and proper escaping for Windows
            abs_path = os.path.abspath(path)
            f.write(f"file '{abs_path}'\n")
            logger.info(f"Added to inputs: {abs_path}")
    
    # Use re-encoding instead of copy to handle different MP3 encodings
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
    
    # Clean up inputs.txt
    try:
        os.remove(inputs_file)
        logger.info(f"Cleaned up inputs file: {inputs_file}")
    except:
        logger.warning(f"Could not remove inputs file: {inputs_file}")
    
    return output_path

def merge_video_clips(video_paths, output_path):
    logger.info(f"Merging {len(video_paths)} video clips")
    logger.info(f"Output path: {output_path}")
    
    # Verify all input files exist
    for path in video_paths:
        if not os.path.exists(path):
            logger.error(f"Input file does not exist: {path}")
            raise FileNotFoundError(f"Input file does not exist: {path}")
        logger.info(f"Verified input file exists: {path}")
    
    # Create inputs.txt in the same directory as output_path
    output_dir = os.path.dirname(output_path)
    inputs_file = os.path.join(output_dir, "inputs.txt")
    
    logger.info(f"Creating inputs file: {inputs_file}")
    with open(inputs_file, "w") as f:
        for path in video_paths:
            # Use absolute paths and proper escaping for Windows
            abs_path = os.path.abspath(path)
            f.write(f"file '{abs_path}'\n")
            logger.info(f"Added to inputs: {abs_path}")
    
    # For video, we can use copy since video files are usually more consistent
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
    
    # Clean up inputs.txt
    try:
        os.remove(inputs_file)
        logger.info(f"Cleaned up inputs file: {inputs_file}")
    except:
        logger.warning(f"Could not remove inputs file: {inputs_file}")
    
    return output_path 

def crop_video_to_portrait(input_path, output_path):
    """
    Crop a landscape video (1280x720) to portrait (720x1280) by cropping from the center.
    """
    logger.info(f"Cropping video from landscape to portrait")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")
    
    # Method: Crop to square, then pad to portrait
    # This should definitely create 720x1280 portrait videos
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-vf", "crop=720:720:280:0,scale=720:720,pad=720:1280:0:280:black",  # Crop square, scale, then pad to portrait
        "-c:v", "libx264",
        "-c:a", "copy",
        output_path
    ]
    
    logger.info(f"Running FFmpeg crop and pad command")
    logger.info(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info("Portrait video created successfully")
        
        # Verify the output dimensions
        verify_cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", output_path
        ]
        verify_result = subprocess.run(verify_cmd, check=True, capture_output=True, text=True)
        logger.info(f"Output video info: {verify_result.stdout}")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Portrait creation failed: {e.stderr}")
        raise
    
    return output_path 