import subprocess
from pathlib import Path
import logging
import os
import shlex
from app.config import Config

logger = logging.getLogger(__name__)

def burn_subtitles(video_path: str, srt_path: str, video_id: str) -> str:
    """Burn subtitles into video using FFmpeg with GPU acceleration"""
    logger.info(f"Starting subtitle burning for video {video_id}")
    
    try:
        # Ensure input files exist
        video_path = Path(video_path).resolve()
        srt_path = Path(srt_path).resolve()
        
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        if not srt_path.exists():
            raise FileNotFoundError(f"SRT file not found: {srt_path}")
        
        # Additional debugging information
        logger.info(f"Video file: {video_path}")
        logger.info(f"Video file exists: {video_path.exists()}")
        logger.info(f"Video file size: {video_path.stat().st_size} bytes")
        logger.info(f"SRT file: {srt_path}")
        logger.info(f"SRT file exists: {srt_path.exists()}")
        logger.info(f"SRT file size: {srt_path.stat().st_size} bytes")
        logger.info(f"Current working directory: {os.getcwd()}")
        
        # Test file readability
        try:
            with open(srt_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                logger.info(f"SRT file first line: {first_line}")
        except Exception as e:
            logger.error(f"Cannot read SRT file: {str(e)}")
            raise
        
        # Create outputs directory
        outputs_dir = Path("outputs").resolve()
        outputs_dir.mkdir(exist_ok=True)
        
        output_path = outputs_dir / f"{video_id}_subtitled.mp4"
        
        # Check if GPU is available and enabled
        gpu_available = os.environ.get("CUDA_VISIBLE_DEVICES") is not None
        use_gpu = gpu_available and Config.ENABLE_GPU_ACCELERATION
        
        # Use ASS subtitle format for better compatibility
        ass_path = outputs_dir / f"{video_id}_subtitles.ass"
        
        # Convert SRT to ASS format
        try:
            convert_srt_to_ass(srt_path, ass_path)
            logger.info(f"Converted SRT to ASS: {ass_path}")
        except Exception as e:
            logger.warning(f"Failed to convert SRT to ASS, using original SRT: {str(e)}")
            ass_path = srt_path
        
        # Try GPU first, fallback to CPU if it fails
        success = False
        
        if use_gpu:
            logger.info("Attempting GPU acceleration for video processing")
            try:
                command = [
                    "ffmpeg",
                    "-y",  # Overwrite output file
                    "-i", str(video_path),
                    "-vf", f"ass={ass_path}",
                    "-c:v", "h264_nvenc",  # NVIDIA GPU encoder
                    "-preset", "fast",
                    "-c:a", "copy",  # Copy audio without re-encoding
                    str(output_path)
                ]
                
                logger.info(f"Running FFmpeg GPU command: {' '.join(command)}")
                
                result = subprocess.run(
                    command, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    timeout=Config.FFMPEG_TIMEOUT
                )
                
                if result.returncode == 0:
                    success = True
                    logger.info("GPU processing completed successfully")
                else:
                    error_msg = result.stderr.decode('utf-8', errors='ignore')
                    logger.warning(f"GPU processing failed, falling back to CPU: {error_msg}")
                    
            except Exception as e:
                logger.warning(f"GPU processing failed, falling back to CPU: {str(e)}")
        
        # Use CPU if GPU failed or not available
        if not success:
            logger.info("Using CPU for video processing")
            command = [
                "ffmpeg",
                "-y",  # Overwrite output file
                "-i", str(video_path),
                "-vf", f"ass={ass_path}",
                "-c:v", "libx264",  # CPU encoder
                "-preset", "medium",
                "-crf", "23",  # Quality setting
                "-c:a", "copy",  # Copy audio without re-encoding
                str(output_path)
            ]
            
            logger.info(f"Running FFmpeg CPU command: {' '.join(command)}")
            
            result = subprocess.run(
                command, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                timeout=Config.FFMPEG_TIMEOUT
            )

            if result.returncode != 0:
                error_msg = result.stderr.decode('utf-8', errors='ignore')
                logger.error(f"FFmpeg failed with return code {result.returncode}")
                logger.error(f"FFmpeg error: {error_msg}")
                raise RuntimeError(f"FFmpeg failed: {error_msg}")
        
        # Verify output file was created
        if not output_path.exists():
            raise RuntimeError("FFmpeg completed but output file was not created")
        
        # Get output file size
        output_size = output_path.stat().st_size / (1024 * 1024)  # MB
        logger.info(f"Subtitle burning completed: {output_path} ({output_size:.2f} MB)")

        return str(output_path)
        
    except subprocess.TimeoutExpired:
        logger.error(f"FFmpeg timeout for video {video_id} (timeout: {Config.FFMPEG_TIMEOUT}s)")
        raise RuntimeError(f"Video processing timeout after {Config.FFMPEG_TIMEOUT} seconds")
    except Exception as e:
        logger.error(f"Subtitle burning failed for video {video_id}: {str(e)}")
        raise

def convert_srt_to_ass(srt_path: Path, ass_path: Path):
    """Convert SRT subtitle to ASS format for better FFmpeg compatibility"""
    try:
        with open(srt_path, 'r', encoding='utf-8') as f:
            srt_content = f.read()
        
        # Parse SRT content
        segments = []
        lines = srt_content.strip().split('\n')
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
                            'timestamp': timestamp_line,
                            'text': ' '.join(text_lines)
                        })
                    i = j
                else:
                    i += 1
            else:
                i += 1
        
        # Create ASS header with improved style
        ass_content = """[Script Info]
Title: Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.601
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,60,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,3,2,2,20,20,60,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        
        # Convert timestamps and add events
        for segment in segments:
            start_time, end_time = parse_srt_timestamp(segment['timestamp'])
            text = segment['text'].replace('\n', '\\N')
            ass_content += f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text}\n"
        
        # Write ASS file
        with open(ass_path, 'w', encoding='utf-8') as f:
            f.write(ass_content)
            
    except Exception as e:
        logger.error(f"Failed to convert SRT to ASS: {str(e)}")
        raise

def parse_srt_timestamp(timestamp_line: str) -> tuple:
    """Parse SRT timestamp format to ASS format"""
    try:
        # SRT format: 00:00:00,000 --> 00:00:03,160
        parts = timestamp_line.split(' --> ')
        if len(parts) != 2:
            raise ValueError(f"Invalid timestamp format: {timestamp_line}")
        
        start_time = convert_time_to_ass(parts[0].strip())
        end_time = convert_time_to_ass(parts[1].strip())
        
        return start_time, end_time
    except Exception as e:
        logger.error(f"Failed to parse timestamp: {timestamp_line}, error: {str(e)}")
        raise

def convert_time_to_ass(time_str: str) -> str:
    """Convert SRT time format to ASS time format"""
    try:
        # SRT: 00:00:00,000 -> ASS: 0:00:00.00
        # Handle different SRT formats
        if ',' in time_str:
            time_str = time_str.replace(',', '.')
        elif '.' in time_str:
            # Already in correct format
            pass
        else:
            # Add milliseconds if missing
            time_str += '.000'
        
        # Ensure proper format: H:MM:SS.ss
        parts = time_str.split(':')
        if len(parts) == 3:
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
            return f"{hours}:{minutes:02d}:{seconds:05.2f}"
        else:
            # Fallback
            return time_str
    except Exception as e:
        logger.error(f"Failed to convert time format: {time_str}, error: {str(e)}")
        return "0:00:00.00"  # Fallback time 