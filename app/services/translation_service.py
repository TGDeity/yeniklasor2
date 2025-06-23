from pathlib import Path
import logging
import time
from transformers import MarianMTModel, MarianTokenizer
import re
from app.config import Config
import os
from langdetect import detect
from deep_translator import GoogleTranslator

logger = logging.getLogger(__name__)

# Global model cache for translation with memory management
_translation_models = {}
_model_load_times = {}

# Extended fallback translations for more languages
FALLBACK_TRANSLATIONS = {
    'tr': {
        'hello': 'merhaba',
        'world': 'dünya',
        'thank you': 'teşekkür ederim',
        'goodbye': 'güle güle',
        'yes': 'evet',
        'no': 'hayır',
        'please': 'lütfen',
        'sorry': 'özür dilerim',
        'excuse me': 'affedersiniz',
        'good morning': 'günaydın',
        'good evening': 'iyi akşamlar',
        'good night': 'iyi geceler',
        'welcome': 'hoş geldiniz',
        'how are you': 'nasılsınız',
        'fine': 'iyi',
        'name': 'isim',
        'time': 'zaman',
        'today': 'bugün',
        'tomorrow': 'yarın',
        'yesterday': 'dün'
    },
    'es': {
        'hello': 'hola',
        'world': 'mundo',
        'thank you': 'gracias',
        'goodbye': 'adiós',
        'yes': 'sí',
        'no': 'no',
        'please': 'por favor',
        'sorry': 'lo siento',
        'excuse me': 'disculpe',
        'good morning': 'buenos días',
        'good evening': 'buenas tardes',
        'good night': 'buenas noches'
    },
    'fr': {
        'hello': 'bonjour',
        'world': 'monde',
        'thank you': 'merci',
        'goodbye': 'au revoir',
        'yes': 'oui',
        'no': 'non',
        'please': 's\'il vous plaît',
        'sorry': 'désolé',
        'excuse me': 'excusez-moi',
        'good morning': 'bonjour',
        'good evening': 'bonsoir',
        'good night': 'bonne nuit'
    },
    'de': {
        'hello': 'hallo',
        'world': 'welt',
        'thank you': 'danke',
        'goodbye': 'auf wiedersehen',
        'yes': 'ja',
        'no': 'nein',
        'please': 'bitte',
        'sorry': 'entschuldigung',
        'excuse me': 'entschuldigen sie',
        'good morning': 'guten morgen',
        'good evening': 'guten abend',
        'good night': 'gute nacht'
    },
    'it': {
        'hello': 'ciao',
        'world': 'mondo',
        'thank you': 'grazie',
        'goodbye': 'arrivederci',
        'yes': 'sì',
        'no': 'no',
        'please': 'per favore',
        'sorry': 'mi dispiace',
        'excuse me': 'scusi',
        'good morning': 'buongiorno',
        'good evening': 'buonasera',
        'good night': 'buonanotte'
    },
    'pt': {
        'hello': 'olá',
        'world': 'mundo',
        'thank you': 'obrigado',
        'goodbye': 'adeus',
        'yes': 'sim',
        'no': 'não',
        'please': 'por favor',
        'sorry': 'desculpe',
        'excuse me': 'com licença',
        'good morning': 'bom dia',
        'good evening': 'boa tarde',
        'good night': 'boa noite'
    },
    'ru': {
        'hello': 'привет',
        'world': 'мир',
        'thank you': 'спасибо',
        'goodbye': 'до свидания',
        'yes': 'да',
        'no': 'нет',
        'please': 'пожалуйста',
        'sorry': 'извините',
        'excuse me': 'извините',
        'good morning': 'доброе утро',
        'good evening': 'добрый вечер',
        'good night': 'спокойной ночи'
    },
    'ja': {
        'hello': 'こんにちは',
        'world': '世界',
        'thank you': 'ありがとう',
        'goodbye': 'さようなら',
        'yes': 'はい',
        'no': 'いいえ',
        'please': 'お願いします',
        'sorry': 'すみません',
        'excuse me': 'すみません',
        'good morning': 'おはよう',
        'good evening': 'こんばんは',
        'good night': 'おやすみ'
    },
    'ko': {
        'hello': '안녕하세요',
        'world': '세계',
        'thank you': '감사합니다',
        'goodbye': '안녕히 가세요',
        'yes': '네',
        'no': '아니요',
        'please': '부탁합니다',
        'sorry': '죄송합니다',
        'excuse me': '실례합니다',
        'good morning': '좋은 아침',
        'good evening': '좋은 저녁',
        'good night': '좋은 밤'
    },
    'zh': {
        'hello': '你好',
        'world': '世界',
        'thank you': '谢谢',
        'goodbye': '再见',
        'yes': '是',
        'no': '不',
        'please': '请',
        'sorry': '对不起',
        'excuse me': '打扰了',
        'good morning': '早上好',
        'good evening': '晚上好',
        'good night': '晚安'
    }
}

def get_translation_model(source_lang="en", target_lang="tr"):
    """Get or create a cached translation model with memory management"""
    current_time = time.time()
    model_key = f"{source_lang}-{target_lang}"
    
    # Check if model is already loaded and not too old
    if model_key in _translation_models:
        load_time = _model_load_times.get(model_key, 0)
        if Config.ENABLE_MODEL_CACHING and (time.time() - load_time) < 1800:
            logger.info(f"Using cached translation model: {model_key}")
            return _translation_models[model_key]
        else:
            logger.info(f"Removing old translation model from cache: {model_key}")
            del _translation_models[model_key]
            if model_key in _model_load_times:
                del _model_load_times[model_key]

    # Define the local path for the model
    local_model_path = f"/app/models/translation/{source_lang}-{target_lang}"
    
    # Always try to load from the local path first
    logger.info(f"Attempting to load translation model from local path: {local_model_path}")
    
    try:
        if os.path.exists(local_model_path):
            tokenizer = MarianTokenizer.from_pretrained(local_model_path)
            model = MarianMTModel.from_pretrained(local_model_path)
            
            _translation_models[model_key] = {'model': model, 'tokenizer': tokenizer}
            _model_load_times[model_key] = time.time()
            
            logger.info(f"Translation model {model_key} loaded successfully from {local_model_path}")
            return _translation_models[model_key]
        else:
            # This part will now act as a fallback if the local model is missing
            logger.warning(f"Local model not found at {local_model_path}. Using fallback translation.")
            return None

    except Exception as e:
        logger.error(f"Failed to load translation model {model_key}: {str(e)}")
        # Fallback to simple replacement for common phrases
        return None

def translate_text(text: str, source_lang="en", target_lang="tr") -> str:
    """Translate text using MarianMT model with timeout"""
    try:
        start_time = time.time()
        
        model_data = get_translation_model(source_lang, target_lang)
        if model_data is None:
            # Fallback translation for common phrases
            return fallback_translate(text, target_lang)
        
        model = model_data['model']
        tokenizer = model_data['tokenizer']
        
        # Check timeout
        if time.time() - start_time > Config.TRANSLATION_TIMEOUT:
            raise RuntimeError(f"Translation timeout after {Config.TRANSLATION_TIMEOUT} seconds")
        
        # Tokenize and translate
        inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
        translated = model.generate(**inputs)
        translated_text = tokenizer.decode(translated[0], skip_special_tokens=True)
        
        # Check final timeout
        if time.time() - start_time > Config.TRANSLATION_TIMEOUT:
            raise RuntimeError(f"Translation timeout after {Config.TRANSLATION_TIMEOUT} seconds")
        
        return translated_text
        
    except Exception as e:
        logger.error(f"Translation failed: {str(e)}")
        # Fallback to simple replacement
        return fallback_translate(text, target_lang)

def fallback_translate(text: str, target_lang: str) -> str:
    """Fallback translation using predefined phrases"""
    if target_lang in FALLBACK_TRANSLATIONS:
        fallback_dict = FALLBACK_TRANSLATIONS[target_lang]
        for english, translated in fallback_dict.items():
            text = re.sub(r'\b' + re.escape(english) + r'\b', translated, text, flags=re.IGNORECASE)
    return text

def parse_srt_content(content: str) -> list:
    """Parse SRT content into segments"""
    segments = []
    lines = content.strip().split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
            
        # Check if this is a segment number
        if line.isdigit():
            # Get timestamp line
            if i + 1 < len(lines):
                timestamp_line = lines[i + 1].strip()
                # Get text lines
                text_lines = []
                j = i + 2
                while j < len(lines) and lines[j].strip():
                    text_lines.append(lines[j].strip())
                    j += 1
                
                if timestamp_line and text_lines:
                    segments.append({
                        'number': int(line),
                        'timestamp': timestamp_line,
                        'text': ' '.join(text_lines)
                    })
                i = j
            else:
                i += 1
        else:
            i += 1
    
    return segments

def translate_subtitles(srt_file: str, target_lang: str = "tr") -> str:
    """Translate subtitles from source language to target language"""
    try:
        with open(srt_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Split into blocks (each subtitle segment)
        blocks = content.strip().split('\n\n')
        translated_blocks = []
        
        # Detect source language from first non-empty subtitle text with sufficient length
        source_lang = "en"  # Default fallback
        for block in blocks:
            lines = block.split('\n')
            if len(lines) >= 3:  # Valid subtitle block
                text = ' '.join(lines[2:]).strip()  # Get all text lines
                # Only try language detection for texts with sufficient length (at least 10 characters)
                if len(text) >= 10:
                    try:
                        detected_lang = detect(text)
                        if detected_lang and detected_lang != 'un':
                            source_lang = detected_lang
                            logger.info(f"Detected source language: {source_lang}")
                            break
                    except Exception as e:
                        logger.debug(f"Language detection failed for text '{text[:50]}...': {str(e)}")
                        continue
        
        # Skip translation if source and target languages are the same
        if source_lang == target_lang:
            logger.info("Source and target languages are the same, skipping translation")
            return srt_file
            
        # Initialize translator
        translator = GoogleTranslator(source=source_lang, target=target_lang)
        
        # Process each subtitle block
        for i, block in enumerate(blocks, 1):
            lines = block.split('\n')
            if len(lines) >= 3:  # Valid subtitle block
                index = lines[0]
                timing = lines[1]
                text = ' '.join(lines[2:]).strip()  # Join all text lines
                
                # Skip translation for empty or very short texts
                if not text or len(text) < 2:
                    logger.debug(f"Skipping translation for empty/short text in block {i}")
                    translated_text = text
                else:
                    try:
                        # Translate text
                        translated_text = translator.translate(text)
                        if not translated_text:
                            logger.warning(f"Translation returned empty for block {i}, using original text")
                            translated_text = text
                    except Exception as e:
                        logger.warning(f"Translation error in block {i}: {str(e)}")
                        translated_text = text  # Fallback to original text
                
                # Reconstruct subtitle block
                translated_block = f"{index}\n{timing}\n{translated_text}\n"
                translated_blocks.append(translated_block)
            else:
                logger.debug(f"Invalid subtitle block {i}: {block}")
                translated_blocks.append(block)  # Keep invalid blocks as is
        
        # Write translated subtitles
        output_path = os.path.join(os.path.dirname(srt_file), f"{os.path.splitext(os.path.basename(srt_file))[0]}_translated.srt")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n\n'.join(translated_blocks))
        
        logger.info(f"Translation completed: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Translation failed: {str(e)}")
        return srt_file  # Return original file on error

def cleanup_translation_cache():
    """Clean up old translation models from cache"""
    if not Config.ENABLE_MODEL_CACHING:
        return
    
    current_time = time.time()
    models_to_remove = []
    
    for model_key, load_time in _model_load_times.items():
        if (current_time - load_time) > 1800:  # Remove models older than 30 minutes
            models_to_remove.append(model_key)
    
    for model_key in models_to_remove:
        logger.info(f"Cleaning up old translation model from cache: {model_key}")
        if model_key in _translation_models:
            del _translation_models[model_key]
        if model_key in _model_load_times:
            del _model_load_times[model_key] 