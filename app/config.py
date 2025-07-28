from dotenv import load_dotenv
load_dotenv()

import os
import tempfile
import logging

logger = logging.getLogger(__name__)

class Settings:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-openai-key")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "your-elevenlabs-key")
    HEYGEN_API_KEY = os.getenv("HEYGEN_API_KEY", "your-heygen-key")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "your-aws-access-key")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "your-aws-secret-key")
    AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET_NAME", "your-s3-bucket")
    TMP_DIR = tempfile.gettempdir()  # Use system temp directory

settings = Settings()

# Debug: Log the loaded environment variables (masked for security)
logger.info("Environment variables loaded:")
logger.info(f"OPENAI_API_KEY: {settings.OPENAI_API_KEY[:10]}..." if settings.OPENAI_API_KEY != "your-openai-key" else "OPENAI_API_KEY: Not set")
logger.info(f"ELEVENLABS_API_KEY: {settings.ELEVENLABS_API_KEY[:10]}..." if settings.ELEVENLABS_API_KEY != "your-elevenlabs-key" else "ELEVENLABS_API_KEY: Not set")
logger.info(f"HEYGEN_API_KEY: {settings.HEYGEN_API_KEY[:10]}..." if settings.HEYGEN_API_KEY != "your-heygen-key" else "HEYGEN_API_KEY: Not set")
logger.info(f"AWS_ACCESS_KEY_ID: {settings.AWS_ACCESS_KEY_ID[:10]}..." if settings.AWS_ACCESS_KEY_ID != "your-aws-access-key" else "AWS_ACCESS_KEY_ID: Not set")
logger.info(f"AWS_S3_BUCKET: {settings.AWS_S3_BUCKET}") 