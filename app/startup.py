import subprocess
import sys
import logging

logger = logging.getLogger(__name__)

def check_ffmpeg():
    """Check if FFmpeg is installed and accessible"""
    try:
        result = subprocess.run(["ffmpeg", "-version"], 
                              capture_output=True, text=True, check=True)
        logger.info("FFmpeg is available")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("FFmpeg is not installed or not in PATH")
        return False

def check_dependencies():
    """Check all required dependencies"""
    checks = [
        ("FFmpeg", check_ffmpeg),
    ]
    
    failed_checks = []
    for name, check_func in checks:
        if not check_func():
            failed_checks.append(name)
    
    if failed_checks:
        logger.error(f"Missing dependencies: {failed_checks}")
        logger.error("Please install the missing dependencies and try again")
        return False
    
    logger.info("All dependencies are available")
    return True 