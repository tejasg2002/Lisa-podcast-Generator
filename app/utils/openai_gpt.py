import openai
import logging
from app.config import settings

logger = logging.getLogger(__name__)

def generate_podcast_script(idea: str, host: str, guest: str, language: str, duration_minutes: int = 5) -> str:
    logger.info(f"Generating podcast script for topic: '{idea}'")
    logger.info(f"Target duration: {duration_minutes} minutes")
    logger.info(f"Language mode: {language}")
    logger.info(f"Using OpenAI GPT-4o-mini model")
    
    # Calculate approximate words needed (average speaking rate is 150 words per minute)
    words_per_minute = 150
    target_words = duration_minutes * words_per_minute
    
    if language == "hindi":
        # For Hindi podcasts, use modern conversational Hindi
        prompt = (
            f"Generate a podcast dialogue in MODERN HINDI between a female host named {host} "
            f"and a male guest named {guest} on the topic: '{idea}'. "
            f"The podcast should be approximately {duration_minutes} minutes long ({target_words} words).\n\n"
            f"IMPORTANT: Use MODERN, CONVERSATIONAL Hindi that people actually speak today, NOT formal/old-fashioned Hindi.\n"
            f"Use contemporary expressions, casual language, and natural speech patterns.\n\n"
            f"Examples of modern Hindi:\n"
            f"- 'यार, यह तो बहुत कूल है!' (instead of formal 'यह बहुत अच्छा है')\n"
            f"- 'मैं तो बिल्कुल agree करता हूं' (mix of Hindi-English like people actually speak)\n"
            f"- 'यह topic तो बहुत interesting है' (natural code-switching)\n"
            f"- 'बस यही तो मैं कह रहा था!' (casual, everyday Hindi)\n\n"
            f"Format the dialogue as follows (NO ASTERISKS OR MARKDOWN):\n\n"
            f"{host}: [host's dialogue in modern conversational Hindi]\n"
            f"{guest}: [guest's dialogue in modern conversational Hindi]\n"
            f"{host}: [host's dialogue in modern conversational Hindi]\n"
            f"and so on...\n\n"
            f"Keep it conversational and engaging. Alternate between {host} and {guest}. "
            f"Make sure each line starts with the speaker's name followed by a colon. "
            f"Structure the conversation with an introduction, main discussion points, and conclusion. "
            f"Use natural, modern Hindi expressions, slang, and code-switching that young people use today."
        )
    else:
        # For English podcasts, mix English with modern Hindi words in Devanagari
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
        max_tokens=min(800, target_words * 2),  # Adjust max_tokens based on target length
        temperature=0.7,
    )
    
    script = response.choices[0].message.content.strip()
    logger.info(f"OpenAI response received. Script length: {len(script)} characters")
    logger.info(f"Estimated words: {len(script.split())}")
    logger.info(f"Script preview: {script[:200]}...")
    
    return script 