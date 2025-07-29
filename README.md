# LISA Podcast Generator - Modal 1.1

An AI-powered podcast generator that creates audio and video podcasts using OpenAI, ElevenLabs, and Heygen APIs.

## 🚀 Features

- **Audio Podcasts**: Generate audio-only podcasts with AI voices
- **Video Podcasts**: Create video podcasts with AI avatars
- **Multi-language Support**: English and Hindi with modern conversational dialogue
- **Concurrent Processing**: Fast generation with parallel processing
- **Cloud Deployment**: Ready for Modal 1.1 deployment with auto-scaling
- **Cost Optimized**: Idle when not in use, scales up on demand

## 📋 Prerequisites

- Python 3.10+
- FFmpeg installed (for local development)
- API keys for:
  - OpenAI
  - ElevenLabs
  - Heygen
  - AWS S3

## 🛠️ Installation

### 1. Clone and Setup
```bash
git clone <repository-url>
cd podcast-api
pip install -r requirements.txt
```

### 2. Install Modal 1.1
```bash
pip install modal>=1.1.0
modal token new
```

### 3. Set Environment Variables
Create a `.env` file:
```env
OPENAI_API_KEY=your-openai-key
ELEVENLABS_API_KEY=your-elevenlabs-key
HEYGEN_API_KEY=your-heygen-key
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_S3_BUCKET_NAME=your-s3-bucket
```

## 🚀 Modal 1.1 Deployment

### Quick Deployment
```bash
# Run the deployment script
python deploy.py
```

### Manual Deployment

#### 1. Set Modal Secrets
```bash
python -m modal secret create lisa-podcast-secrets \
  OPENAI_API_KEY="your-openai-key" \
  ELEVENLABS_API_KEY="your-elevenlabs-key" \
  HEYGEN_API_KEY="your-heygen-key" \
  AWS_ACCESS_KEY_ID="your-aws-key" \
  AWS_SECRET_ACCESS_KEY="your-aws-secret" \
  AWS_S3_BUCKET_NAME="your-s3-bucket"
```

#### 2. Deploy to Modal
```bash
# Deploy the complete FastAPI application
python -m modal deploy modal_app.py
```

#### 3. Get Deployment URL
```bash
python -m modal app list
```

## 📡 API Usage

### Audio Podcast Generation

```bash
curl -X POST "https://lu-labs--lisa-podcast-generator-fastapi-app.modal.run/v1/lisa-audio-podcast" \
  -H "Content-Type: application/json" \
  -d '{
    "input_type": "idea",
    "input_text": "The impact of AI on remote work",
    "language": "english",
    "host_name": "Aarohi",
    "guest_name": "Ravi",
    "host_voice_id": "female_voice_01",
    "guest_voice_id": "male_voice_02",
    "elevenlabs_config": {
      "stability": 0.7,
      "similarity_boost": 0.9,
      "style": 0.5,
      "model_id": "eleven_monolingual_v1"
    },
    "duration_minutes": 5
  }'
```

### Video Podcast Generation

```bash
curl -X POST "https://lu-labs--lisa-podcast-generator-fastapi-app.modal.run/v1/lisa-video-podcast" \
  -H "Content-Type: application/json" \
  -d '{
    "input_type": "idea",
    "input_text": "The future of AI in 2024",
    "language": "english",
    "orientation": "landscape",
    "host_name": "Aarohi",
    "guest_name": "Ravi",
    "host_voice_id": "female_voice_01",
    "guest_voice_id": "male_voice_02",
    "elevenlabs_config": {
      "stability": 0.7,
      "similarity_boost": 0.9,
      "style": 0.5,
      "model_id": "eleven_monolingual_v1"
    },
    "heygen_config": {
      "host_avatar_id": "heygen_female_avatar_01",
      "guest_avatar_id": "heygen_male_avatar_01",
      "background": "#000000"
    },
    "duration_minutes": 5
  }'
```

## 🔧 Configuration

### Modal 1.1 Settings

The application is configured for Modal 1.1 with:

- **FastAPI App**: `cpu=2, memory=4096MB, timeout=300s`
- **Audio Function**: `cpu=2, memory=4096MB, max_containers=5`
- **Video Function**: `cpu=4, memory=8192MB, max_containers=3`
- **Auto-scaling**: `min_containers=0` (starts idle, scales up on demand)
- **Cost Optimization**: Only runs when requests come in

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for script generation | ✅ |
| `ELEVENLABS_API_KEY` | ElevenLabs API key for voice synthesis | ✅ |
| `HEYGEN_API_KEY` | Heygen API key for video generation | ✅ |
| `AWS_ACCESS_KEY_ID` | AWS access key for S3 uploads | ✅ |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key for S3 uploads | ✅ |
| `AWS_S3_BUCKET_NAME` | S3 bucket name for file storage | ✅ |

## 📊 Monitoring

### View Logs
```bash
python -m modal app logs lisa-podcast-generator
```

### Check Status
```bash
python -m modal app list
python -m modal app status lisa-podcast-generator
```

### Monitor Resources
```bash
python -m modal app metrics lisa-podcast-generator
```

## 🏗️ Architecture

### Modal 1.1 Functions

1. **`fastapi_app`**: Complete FastAPI application with auto-scaling
2. **`audio_podcast_function`**: Dedicated audio generation function
3. **`video_podcast_function`**: Dedicated video generation function

### Processing Flow

1. **Script Generation**: OpenAI GPT creates podcast dialogue
2. **Voice Synthesis**: ElevenLabs generates AI voices
3. **Video Generation**: Heygen creates AI avatars (video only)
4. **Media Merging**: FFmpeg combines audio/video segments
5. **Cloud Storage**: S3 uploads final files

### Concurrency

- **ElevenLabs**: Max 10 concurrent requests
- **S3 Uploads**: Max 5 concurrent uploads
- **Heygen**: Unlimited concurrent video generation
- **Modal Scaling**: Auto-scales based on demand

## 🎙️ Language Features

### English Podcasts
- Modern conversational dialogue
- Code-switching with Hindi words in Devanagari script
- Youth-friendly expressions and slang
- Natural speech patterns

### Hindi Podcasts
- Modern conversational Hindi (not formal/old-fashioned)
- Contemporary expressions and casual language
- Natural code-switching with English
- Devanagari script for proper pronunciation

## 🐛 Troubleshooting

### Common Issues

1. **FFmpeg Not Found**
   ```bash
   # Install FFmpeg
   # Windows: Download from https://ffmpeg.org/
   # macOS: brew install ffmpeg
   # Linux: sudo apt install ffmpeg
   ```

2. **API Key Errors**
   ```bash
   # Check Modal secrets
   python -m modal secret list
   
   # Update secrets
   python -m modal secret update lisa-podcast-secrets
   ```

3. **Deployment Failures**
   ```bash
   # Check Modal status
   python -m modal app list
   
   # View detailed logs
   python -m modal app logs lisa-podcast-generator
   ```

### Performance Optimization

- **Audio Podcasts**: ~30-60 seconds generation time
- **Video Podcasts**: ~2-5 minutes generation time
- **Concurrent Requests**: Up to 10 simultaneous users
- **Auto-scaling**: Handles traffic spikes automatically
- **Cost Efficiency**: Idle when not in use

## 📝 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For issues and questions:
- Check the logs: `python -m modal app logs lisa-podcast-generator`
- Review the documentation
- Open an issue on GitHub

## 🚀 Live Deployment

**Current Status**: ✅ Deployed and Running
**URL**: `https://lu-labs--lisa-podcast-generator-fastapi-app.modal.run`
**Dashboard**: `https://modal.com/apps/lu-labs/main/deployed/lisa-podcast-generator` 