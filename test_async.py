import requests, json, time
print(' Testing Simplified Async API')
print('=' * 50)
data = {'input_type': 'idea', 'input_text': 'AI in healthcare', 'language': 'english', 'host_name': 'Sarah', 'guest_name': 'Dr. Mike', 'host_voice_id': 'test-host', 'guest_voice_id': 'test-guest', 'elevenlabs_config': {'stability': 0.5, 'similarity_boost': 0.75, 'style': 0.0, 'model_id': 'eleven_monolingual_v1', 'speed': 1.0}, 'duration_minutes': 5}
