import whisper
from datetime import timedelta
from pathlib import Path
import logging
import os
import time
from app.config import Config
from typing import List
import types

logger = logging.getLogger(__name__)

# Global model cache with memory management
_model_cache = {}
_model_load_times = {}

def format_srt_time(seconds: float) -> str:
    """Format seconds to SRT timestamp format (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def get_whisper_model(model_size="base"):
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

def transcribe(video_path: str, model_name: str = "small.en") -> str:
    """Transcribe video using Whisper model"""
    try:
        logger.info(f"Starting transcription for video {os.path.basename(video_path)} with model {model_name}")
        
        # Load model
        model = get_whisper_model(model_name)
        
        # Transcribe with maximum sensitivity settings for better audio detection
        # OpenAI Whisper compatible parameters with ultra-low thresholds
        result = model.transcribe(
            video_path,
            language=None,  # Auto-detect language
            word_timestamps=True,
            condition_on_previous_text=False,
            initial_prompt="This is a video with speech, singing, or music that may start immediately. There might be quiet speech, background music, or singing at any time.",
            temperature=0.0,
            no_speech_threshold=0.01,  # Ultra-low threshold for maximum sensitivity
            compression_ratio_threshold=3.0,  # Higher threshold to allow more variations
            logprob_threshold=-2.0  # Lower threshold to catch more speech
        )

        # Extract segments from result
        segments = result.get("segments", [])
        
        logger.info(f"Raw transcription result - segments found: {len(segments)}")
        logger.info(f"Transcription text: {result.get('text', '')[:200]}...")
        
        if not segments:
            logger.warning("No segments found in transcription. Audio might be too quiet or silent.")
            # Create a minimal segment to avoid empty SRT
            segments = [{
                'start': 0.0,
                'end': 5.0,
                'text': '[No speech detected]'
            }]

        # Filter out empty segments and validate content
        valid_segments = []
        for segment in segments:
            segment_text = get_attr(segment, "text", "").strip()
            if segment_text and len(segment_text) > 0:
                # Convert segment to dict format
                seg_dict = {
                    'start': get_attr(segment, 'start', 0),
                    'end': get_attr(segment, 'end', 0),
                    'text': segment_text
                }
                valid_segments.append(seg_dict)
                logger.info(f"Valid segment: {segment_text[:100]}...")
            else:
                logger.debug(f"Skipping empty segment: {segment_text}")

        if not valid_segments:
            logger.warning("No valid segments found in transcription. Audio might be too quiet or silent.")
            # Create a minimal segment to avoid empty SRT
            valid_segments = [{
                'start': 0.0,
                'end': 5.0,
                'text': '[No speech detected]'
            }]
        
        # Sort segments by start time and fix overlapping
        valid_segments.sort(key=lambda x: x['start'])
        
        # Fix overlapping segments with more aggressive gap filling
        final_segments = []
        for i, segment in enumerate(valid_segments):
            start_time = segment['start']
            end_time = segment['end']
            
            # Ensure minimum duration (reduced for better sensitivity)
            if end_time - start_time < 0.3:
                end_time = start_time + 0.3
            
            # Check for overlap with previous segment
            if final_segments:
                prev_end = final_segments[-1]['end']
                if start_time < prev_end:
                    # Adjust start time to avoid overlap (reduced gap)
                    start_time = prev_end + 0.05
                    end_time = max(end_time, start_time + 0.3)
            
            final_segments.append({
                'start': start_time,
                'end': end_time,
                'text': segment['text']
            })
        
        # Check for large gaps and add placeholder segments for quiet periods
        final_segments_with_gaps = []
        for i, segment in enumerate(final_segments):
            if i > 0:
                prev_end = final_segments[i-1]['end']
                current_start = segment['start']
                gap = current_start - prev_end
                
                # If there's a gap larger than 3 seconds, add a placeholder
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
        
        output_dir = os.path.join("outputs")
        os.makedirs(output_dir, exist_ok=True)
        
        srt_path = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(video_path))[0]}.srt")
        write_srt(final_segments_with_gaps, srt_path)
        
        logger.info(f"Transcription completed and saved to {srt_path}")
        logger.info(f"Generated {len(final_segments_with_gaps)} segments with content")
        
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