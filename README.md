# LISA - AI Podcast Generator

A FastAPI-based AI podcast generator that creates audio and video podcasts using OpenAI GPT-4o-mini for script generation, ElevenLabs for voice synthesis, and Heygen for video generation.

## Features

### 🎙️ Audio Podcasts
- Generate podcast scripts from ideas or use custom scripts
- Support for English and Hindi languages
- Modern conversational dialogue with natural code-switching
- ElevenLabs voice synthesis with customizable settings
- Concurrent audio processing for faster generation

### 🎥 Video Podcasts
- Talking photo avatars using Heygen API
- Support for both landscape (1280x720) and portrait (720x1280) orientations
- Background customization (colors or images)
- Concurrent video generation for optimal performance
- Automatic video cropping and merging

### 🚀 Performance Features
- Concurrent processing using ThreadPoolExecutor
- Rate limit management for external APIs
- Efficient S3 uploads with concurrent processing
- Detailed logging for debugging and monitoring

## Prerequisites

### Required Software
- **Python 3.8+**
- **FFmpeg** - For video/audio processing
  - Download from: https://ffmpeg.org/download.html
  - Add to system PATH
- **Git** - For version control

### Required APIs
- **OpenAI API Key** - For GPT-4o-mini script generation
- **ElevenLabs API Key** - For voice synthesis
- **Heygen API Key** - For video generation
- **AWS S3** - For file storage (Access Key, Secret Key, Bucket Name)

## Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd podcast-api
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Setup
Create a `.env` file in the root directory:
```env
# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key

# ElevenLabs Configuration
ELEVENLABS_API_KEY=your-elevenlabs-api-key

# Heygen Configuration
HEYGEN_API_KEY=your-heygen-api-key

# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_S3_BUCKET_NAME=your-s3-bucket-name
```

### 4. Verify FFmpeg Installation
```bash
ffmpeg -version
```

## Usage

### Start the Server
```bash
python -m uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### API Endpoints

#### 1. Audio Podcast Generation
**Endpoint:** `POST /v1/lisa-audio-podcast`

**Request Body:**
```json
{
  "input_type": "idea",
  "input_text": "AI in healthcare",
  "language": "english",
  "host_name": "Sarah",
  "guest_name": "Dr. Mike",
  "host_voice_id": "your-host-voice-id",
  "guest_voice_id": "your-guest-voice-id",
  "elevenlabs_config": {
    "stability": 0.5,
    "similarity_boost": 0.75,
    "style": 0.0,
    "model_id": "eleven_monolingual_v1",
    "speed": 1.0
  },
  "duration_minutes": 5
}
```

**Response:**
```json
{
  "status": "success",
  "s3_url": "https://your-bucket.s3.amazonaws.com/podcasts/audio/final_podcast.mp3",
  "duration": 150
}
```

#### 2. Video Podcast Generation
**Endpoint:** `POST /v1/lisa-video-podcast`

**Request Body:**
```json
{
  "input_type": "idea",
  "input_text": "AI in healthcare",
  "language": "english",
  "orientation": "portrait",
  "host_name": "Sarah",
  "guest_name": "Dr. Mike",
  "host_voice_id": "your-host-voice-id",
  "guest_voice_id": "your-guest-voice-id",
  "elevenlabs_config": {
    "stability": 0.5,
    "similarity_boost": 0.75,
    "style": 0.0,
    "model_id": "eleven_monolingual_v1",
    "speed": 1.0
  },
  "heygen_config": {
    "host_avatar_id": "your-host-avatar-id",
    "guest_avatar_id": "your-guest-avatar-id",
    "background": "#000000"
  },
  "duration_minutes": 5
}
```

**Response:**
```json
{
  "status": "success",
  "s3_url": "https://your-bucket.s3.amazonaws.com/podcasts/video/final_podcast.mp4",
  "duration": 150
}
```

## Configuration Options

### ElevenLabs Settings
- **stability**: 0.0-1.0 (voice consistency)
- **similarity_boost**: 0.0-1.0 (voice similarity)
- **style**: 0.0-1.0 (speaking style)
- **speed**: 0.25-4.0 (speech speed)
- **model_id**: Voice model identifier

### Heygen Settings
- **host_avatar_id**: Talking photo ID for host
- **guest_avatar_id**: Talking photo ID for guest
- **background**: Color (e.g., "#000000") or image URL

### Language Support
- **English**: Standard English dialogue
- **Hindi**: Modern conversational Hindi with Devanagari script
- **Mixed**: English with Hindi words in Devanagari

## Architecture

### Project Structure
```
podcast-api/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── models.py            # Pydantic models
│   ├── services/
│   │   └── podcast.py       # Core podcast generation logic
│   └── utils/
│       ├── openai_gpt.py    # OpenAI script generation
│       ├── elevenlabs.py    # ElevenLabs voice synthesis
│       ├── heygen.py        # Heygen video generation
│       ├── ffmpeg_merge.py  # Video/audio processing
│       └── s3.py           # S3 upload utilities
├── requirements.txt
├── README.md
└── .env
```

### Processing Flow

#### Audio Podcasts:
1. **Script Generation**: OpenAI GPT-4o-mini creates dialogue
2. **Dialogue Processing**: Parse speaker segments
3. **Voice Synthesis**: ElevenLabs generates audio for each segment
4. **Audio Merging**: FFmpeg combines all segments
5. **S3 Upload**: Final audio uploaded to S3

#### Video Podcasts:
1. **Script Generation**: OpenAI GPT-4o-mini creates dialogue
2. **Dialogue Processing**: Parse speaker segments
3. **Concurrent Audio**: ElevenLabs generates audio segments
4. **S3 Upload**: Audio segments uploaded to S3
5. **Concurrent Video**: Heygen generates video segments
6. **Video Cropping**: FFmpeg crops to portrait if needed
7. **Video Merging**: FFmpeg combines all video segments
8. **Final Upload**: Complete video uploaded to S3

## Performance Features

### Concurrency Management
- **ElevenLabs**: Max 10 concurrent requests
- **S3 Uploads**: Max 5 concurrent uploads
- **Heygen**: Unlimited concurrent video generation
- **ThreadPoolExecutor**: Efficient resource management

### Rate Limiting
- Respects API rate limits
- Automatic retry mechanisms
- Detailed error logging

## Troubleshooting

### Common Issues

#### 1. FFmpeg Not Found
```bash
# Install FFmpeg and add to PATH
# Windows: Download from https://ffmpeg.org/download.html
# macOS: brew install ffmpeg
# Linux: sudo apt install ffmpeg
```

#### 2. API Key Errors
- Verify all API keys are set in `.env`
- Check API key permissions and quotas
- Ensure proper key format

#### 3. Video Cropping Issues
- Ensure FFmpeg is properly installed
- Check video dimensions in logs
- Verify orientation parameter is set correctly

#### 4. S3 Upload Errors
- Verify AWS credentials
- Check S3 bucket permissions
- Ensure bucket name is correct

### Logging
The application provides detailed logging for debugging:
- API request/response logging
- FFmpeg command execution
- File processing status
- Error details with stack traces

## Development

### Local Development
```bash
# Install development dependencies
pip install -r requirements.txt

# Start development server
python -m uvicorn app.main:app --reload

# Run tests (if available)
python -m pytest
```

### Code Style
- Follow PEP 8 guidelines
- Use type hints
- Add docstrings for functions
- Maintain consistent logging

## License

[Your License Here]

## Support

For issues and questions:
- Check the troubleshooting section
- Review API documentation
- Check application logs for detailed error messages 