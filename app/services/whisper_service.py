import whisper
from datetime import timedelta
from pathlib import Path
import logging
import os
import time
from app.config import Config
from typing import List
import types
import subprocess
import uuid
import wave
import contextlib
#import webrtcvad
import numpy as np
import soundfile as sf
import librosa
import noisereduce as nr
from app.services.translation_service import translate_text

logger = logging.getLogger(__name__)

# Global model cache with memory management
_model_cache = {}
_model_load_times = {}

# Whisper Model Seçenekleri:
#
# | Boyut   | İngilizce Model   | Çok Dilli Model | VRAM   | Hız (göreceli) |
# |---------|------------------|-----------------|--------|----------------|
# | tiny    | tiny.en          | tiny            | ~1 GB  | ~10x           |
# | base    | base.en          | base            | ~1 GB  | ~7x            |
# | small   | small.en         | small           | ~2 GB  | ~4x            |
# | medium  | medium.en        | medium          | ~5 GB  | ~2x            |
# | large   | N/A              | large           | ~10 GB | ~1x            |
# | turbo   | N/A              | turbo           | ~6 GB  | ~8x            |
#
# Not: Türkçe ve diğer diller için mutlaka çok dilli model (tiny, base, small, medium, large, turbo) seçilmelidir.
DEFAULT_WHISPER_MODEL = "large"

def format_srt_time(seconds: float) -> str:
    """Format seconds to SRT timestamp format (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def get_whisper_model(model_size=DEFAULT_WHISPER_MODEL):
    """Get or create a cached Whisper model with memory management"""
    current_time = time.time()
    
    # Check if model is already loaded and not too old
    if model_size in _model_cache:
        load_time = _model_load_times.get(model_size, 0)
        # Keep model in cache for 1 hour if caching is enabled
        if Config.ENABLE_MODEL_CACHING and (current_time - load_time) < 3600:
            logger.info(f"Using cached Whisper model: {model_size}")
            return _model_cache[model_size]
        else:
            # Remove old model from cache
            logger.info(f"Removing old Whisper model from cache: {model_size}")
            del _model_cache[model_size]
            if model_size in _model_load_times:
                del _model_load_times[model_size]
    
    # Load new model
    logger.info(f"Loading Whisper model: {model_size}")
    try:
        # Check GPU availability
        gpu_available = os.environ.get("CUDA_VISIBLE_DEVICES") is not None
        use_gpu = gpu_available and Config.ENABLE_GPU_ACCELERATION
        
        # Load model with appropriate device
        device = "cuda" if use_gpu else "cpu"
        model = whisper.load_model(model_size, device=device)
        
        _model_cache[model_size] = model
        _model_load_times[model_size] = current_time
        
        logger.info(f"Whisper model {model_size} loaded successfully on {device.upper()}")
        return model
        
    except Exception as e:
        logger.error(f"Failed to load Whisper model {model_size}: {str(e)}")
        raise

def get_attr(obj, key, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)

def transcribe(video_path: str, model_size: str = DEFAULT_WHISPER_MODEL, target_lang: str = None) -> str:
    """
    1. Orijinal dilde transkript ve segmentasyon (Whisper, task='transcribe', language=None ile otomatik tespit)
    2. Her segmentin metnini target_lang'e çevir (ör. Google Translate API, OpenAI, vs.)
    3. Segment zamanlamaları orijinalden alınır, sadece metinler çevrilir.
    """
    if target_lang is None:
        raise ValueError("target_lang parametresi zorunludur ve kullanıcıdan alınmalıdır!")
    try:
        logger.info(f"Starting transcription for video {os.path.basename(video_path)} with model {model_size}")
        video_id = os.path.splitext(os.path.basename(video_path))[0]
        wav_path = f"outputs/{video_id}_input.wav"
        cleaned_wav_path = f"outputs/{video_id}_cleaned.wav"
        subprocess.run([
            "ffmpeg", "-y", "-i", video_path, "-ar", "16000", "-ac", "1", wav_path
        ], check=True)
        y, sr = librosa.load(wav_path, sr=None)
        reduced_noise = nr.reduce_noise(y=y, sr=sr)
        sf.write(cleaned_wav_path, reduced_noise, sr)
        model = get_whisper_model(model_size)
        # 1. Orijinal dilde transkript ve segmentasyon
        result = model.transcribe(
            cleaned_wav_path,
            task="transcribe",  # Orijinal dilde transkript
            word_timestamps=True,
            temperature=0.0,
            no_speech_threshold=0.3,
            logprob_threshold=-1.0,
            compression_ratio_threshold=2.4,
            condition_on_previous_text=False
            # language parametresi verilmedi, Whisper kendi tespit edecek
        )
        segments = result.get("segments", [])
        source_lang = result.get('language', 'auto')
        logger.info(f"Whisper detected language: {source_lang}, user requested: {target_lang}")
        PROMPT_PHRASES = [
            "This is a video with speech, singing, or music that may start immediately.",
            "There might be quiet speech, background music, or singing at any time.",
            "[Background music or quiet speech]"
        ]
        valid_segments = []
        for segment in segments:
            segment_text = get_attr(segment, "text", "").strip()
            if not segment_text or all(c in '.!?,…- ' for c in segment_text) or any(phrase in segment_text for phrase in PROMPT_PHRASES):
                logger.debug(f"Skipping prompt/placeholder segment: {segment_text}")
                continue
            # Eğer kaynak dil ve hedef dil aynıysa çeviri yapmadan ekle
            if source_lang == target_lang:
                logger.info(f"No translation needed: Whisper output will be used as-is for {source_lang}")
                translated_text = segment_text
            else:
                logger.info(f"Translating segment from {source_lang} to {target_lang}")
                translated_text = translate_text(segment_text, source_lang, target_lang)
            seg_dict = {
                'start': get_attr(segment, 'start', 0),
                'end': get_attr(segment, 'end', 0),
                'text': translated_text
            }
            valid_segments.append(seg_dict)
            logger.info(f"Valid segment: {translated_text[:100]}...")
        if not valid_segments:
            logger.warning("No valid segments found in transcription. Audio might be too quiet or silent.")
            valid_segments = [{
                'start': 0.0,
                'end': 5.0,
                'text': '[No speech detected]'
            }]
        valid_segments.sort(key=lambda x: x['start'])
        final_segments = []
        for i, segment in enumerate(valid_segments):
            start_time = segment['start']
            end_time = segment['end']
            if end_time - start_time < 0.3:
                end_time = start_time + 0.3
            if final_segments:
                prev_end = final_segments[-1]['end']
                if start_time < prev_end:
                    start_time = prev_end + 0.05
                    end_time = max(end_time, start_time + 0.3)
            final_segments.append({
                'start': start_time,
                'end': end_time,
                'text': segment['text']
            })
        final_segments_with_gaps = []
        for i, segment in enumerate(final_segments):
            if i > 0:
                prev_end = final_segments[i-1]['end']
                current_start = segment['start']
                gap = current_start - prev_end
                if gap > 3.0:
                    placeholder_start = prev_end + 0.1
                    placeholder_end = current_start - 0.1
                    if placeholder_end > placeholder_start:
                        final_segments_with_gaps.append({
                            'start': placeholder_start,
                            'end': placeholder_end,
                            'text': '[Background music or quiet speech]'
                        })
            final_segments_with_gaps.append(segment)
        cleaned_segments = []
        for seg in final_segments_with_gaps:
            duration = seg['end'] - seg['start']
            text = seg['text'].strip()
            if duration < 1.0:
                continue
            if not text or all(c in '.!?,…- ' for c in text):
                continue
            cleaned_segments.append(seg)
        if not cleaned_segments:
            cleaned_segments = final_segments_with_gaps
        output_dir = os.path.join("outputs")
        os.makedirs(output_dir, exist_ok=True)
        srt_path = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(video_path))[0]}.srt")
        write_srt(cleaned_segments, srt_path)
        logger.info(f"Transcription completed and saved to {srt_path}")
        logger.info(f"Generated {len(cleaned_segments)} segments with content")
    except Exception as e:
        logger.error(f"Transcription failed for video {os.path.basename(video_path)}: {str(e)}")
        raise
    return srt_path

def reconstruct_segments_from_words(words: List[dict], max_duration: float = 2.5) -> List[dict]:
    """Reconstruct segments from word-level timestamps with improved synchronization"""
    if not words:
        return []
    
    segments = []
    current_segment = {
        'start': get_attr(words[0], 'start', 0),
        'end': get_attr(words[0], 'end', 0),
        'text': get_attr(words[0], 'text', '')
    }
    
    for i in range(1, len(words)):
        word = words[i]
        prev_word = words[i-1]
        
        # Calculate gap between words
        word_start = get_attr(word, 'start', 0)
        word_end = get_attr(word, 'end', 0)
        prev_end = get_attr(prev_word, 'end', 0)
        gap = word_start - prev_end
        
        # Start new segment if:
        # 1. Current segment is too long
        # 2. There's a significant pause between words (>0.3s)
        # 3. Current word starts with sentence-ending punctuation
        word_text = get_attr(word, 'text', '')
        if (word_end - current_segment['start'] > max_duration or
            gap > 0.3 or
            any(word_text.strip().startswith(p) for p in ['.', '!', '?', '...'])):
            
            # Add small buffer to segment timing
            current_segment['start'] = max(0, current_segment['start'] - 0.1)
            current_segment['end'] = min(current_segment['end'] + 0.1, word_start - 0.05)
            
            # Ensure minimum segment duration
            if current_segment['end'] - current_segment['start'] < 0.3:
                current_segment['end'] = current_segment['start'] + 0.3
            
            segments.append(current_segment)
            current_segment = {
                'start': word_start,
                'end': word_end,
                'text': word_text
            }
        else:
            # Add word to current segment with proper spacing
            if not current_segment['text'].endswith(('(', '[', '{', '-', "'", '"')):
                current_segment['text'] += ' '
            current_segment['text'] += word_text
            current_segment['end'] = word_end
    
    # Add the last segment
    if current_segment:
        # Add small buffer to final segment
        current_segment['start'] = max(0, current_segment['start'] - 0.1)
        current_segment['end'] = current_segment['end'] + 0.1
        
        # Ensure minimum segment duration
        if current_segment['end'] - current_segment['start'] < 0.3:
            current_segment['end'] = current_segment['start'] + 0.3
            
        segments.append(current_segment)
    
    return segments

def cleanup_model_cache():
    """Clean up old models from cache"""
    if not Config.ENABLE_MODEL_CACHING:
        return
    
    current_time = time.time()
    models_to_remove = []
    
    for model_size, load_time in _model_load_times.items():
        if (current_time - load_time) > 3600:  # Remove models older than 1 hour
            models_to_remove.append(model_size)
    
    for model_size in models_to_remove:
        logger.info(f"Cleaning up old model from cache: {model_size}")
        if model_size in _model_cache:
            del _model_cache[model_size]
        if model_size in _model_load_times:
            del _model_load_times[model_size]

def write_srt(segments: List[dict], output_path: str):
    """Write segments to SRT file format"""
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, segment in enumerate(segments, 1):
            start_time = format_srt_time(segment['start'])
            end_time = format_srt_time(segment['end'])
            text = segment['text'].strip()
            
            f.write(f"{i}\n")
            f.write(f"{start_time} --> {end_time}\n")
            f.write(f"{text}\n\n")

def transcribe_with_openai_whisper(video_path: str, target_lang: str, model_size: str = DEFAULT_WHISPER_MODEL) -> str:
    """OpenAI Whisper ile transkripsiyon ve çeviri"""
    return transcribe(video_path, model_size=model_size, target_lang=target_lang)

def transcribe_with_faster_whisper(video_path: str, target_lang: str, model_size: str = DEFAULT_WHISPER_MODEL) -> str:
    """Faster-Whisper ile transkripsiyon ve çeviri (otomatik GPU/CPU fallback ve compute_type seçimi ile)"""
    from faster_whisper import WhisperModel
    import numpy as np
    import soundfile as sf
    import librosa
    import noisereduce as nr
    import os
    import torch

    # Otomatik cihaz ve compute_type seçimi
    if torch.cuda.is_available() and Config.ENABLE_GPU_ACCELERATION:
        device = "cuda"
        compute_type = "float16"
    else:
        device = "cpu"
        compute_type = "int8"  # CPU için en hızlı ve düşük bellekli seçenek
    logger.info(f"[Faster-Whisper] Using device: {device}, compute_type: {compute_type}")

    logger.info(f"[Faster-Whisper] Starting transcription for {video_path} with model {model_size}")
    video_id = os.path.splitext(os.path.basename(video_path))[0]
    wav_path = f"outputs/{video_id}_input.wav"
    cleaned_wav_path = f"outputs/{video_id}_cleaned.wav"
    # Sesi wav'a çevir
    subprocess.run([
        "ffmpeg", "-y", "-i", video_path, "-ar", "16000", "-ac", "1", wav_path
    ], check=True)
    y, sr = librosa.load(wav_path, sr=None)
    reduced_noise = nr.reduce_noise(y=y, sr=sr)
    sf.write(cleaned_wav_path, reduced_noise, sr)
    # Model yükle
    model = WhisperModel(model_size, device=device, compute_type=compute_type)
    segments, info = model.transcribe(
        cleaned_wav_path,
        beam_size=5,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500),
        word_timestamps=True,
        language=None,
        task="transcribe"
    )
    source_lang = info.get('language', 'auto')
    logger.info(f"[Faster-Whisper] Detected language: {source_lang}, user requested: {target_lang}")
    PROMPT_PHRASES = [
        "This is a video with speech, singing, or music that may start immediately.",
        "There might be quiet speech, background music, or singing at any time.",
        "[Background music or quiet speech]"
    ]
    valid_segments = []
    for segment in segments:
        segment_text = segment.text.strip() if hasattr(segment, 'text') else str(segment)
        if not segment_text or all(c in '.!?,…- ' for c in segment_text) or any(phrase in segment_text for phrase in PROMPT_PHRASES):
            logger.debug(f"[Faster-Whisper] Skipping prompt/placeholder segment: {segment_text}")
            continue
        # Eğer kaynak dil ve hedef dil aynıysa çeviri yapmadan ekle
        if source_lang == target_lang:
            logger.info(f"[Faster-Whisper] No translation needed: output will be used as-is for {source_lang}")
            translated_text = segment_text
        else:
            logger.info(f"[Faster-Whisper] Translating segment from {source_lang} to {target_lang}")
            translated_text = translate_text(segment_text, source_lang, target_lang)
        seg_dict = {
            'start': segment.start,
            'end': segment.end,
            'text': translated_text
        }
        valid_segments.append(seg_dict)
        logger.info(f"[Faster-Whisper] Valid segment: {translated_text[:100]}...")
    if not valid_segments:
        logger.warning("[Faster-Whisper] No valid segments found in transcription. Audio might be too quiet or silent.")
        valid_segments = [{
            'start': 0.0,
            'end': 5.0,
            'text': '[No speech detected]'
        }]
    valid_segments.sort(key=lambda x: x['start'])
    final_segments = []
    for i, segment in enumerate(valid_segments):
        start_time = segment['start']
        end_time = segment['end']
        if end_time - start_time < 0.3:
            end_time = start_time + 0.3
        if final_segments:
            prev_end = final_segments[-1]['end']
            if start_time < prev_end:
                start_time = prev_end + 0.05
                end_time = max(end_time, start_time + 0.3)
        final_segments.append({
            'start': start_time,
            'end': end_time,
            'text': segment['text']
        })
    final_segments_with_gaps = []
    for i, segment in enumerate(final_segments):
        if i > 0:
            prev_end = final_segments[i-1]['end']
            current_start = segment['start']
            gap = current_start - prev_end
            if gap > 3.0:
                placeholder_start = prev_end + 0.1
                placeholder_end = current_start - 0.1
                if placeholder_end > placeholder_start:
                    final_segments_with_gaps.append({
                        'start': placeholder_start,
                        'end': placeholder_end,
                        'text': '[Background music or quiet speech]'
                    })
        final_segments_with_gaps.append(segment)
    cleaned_segments = []
    for seg in final_segments_with_gaps:
        duration = seg['end'] - seg['start']
        text = seg['text'].strip()
        if duration < 1.0:
            continue
        if not text or all(c in '.!?,…- ' for c in text):
            continue
        cleaned_segments.append(seg)
    if not cleaned_segments:
        cleaned_segments = final_segments_with_gaps
    output_dir = os.path.join("outputs")
    os.makedirs(output_dir, exist_ok=True)
    srt_path = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(video_path))[0]}.srt")
    logger.info(f"[Faster-Whisper] Transcription completed and saved to {srt_path}")
    logger.info(f"[Faster-Whisper] Generated {len(cleaned_segments)} segments with content")
    return srt_path