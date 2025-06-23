#!/usr/bin/env python3
"""
Test script for video upload with language selection
"""

import requests
import json
import time
from pathlib import Path

# API Configuration
API_BASE_URL = "http://localhost:8082/api/v1"

def get_supported_languages():
    """Get list of supported languages"""
    try:
        response = requests.get(f"{API_BASE_URL}/upload/languages")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error getting languages: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def upload_video_with_language(video_path: str, target_language: str = "tr"):
    """Upload video with specific language"""
    try:
        # Check if video file exists
        if not Path(video_path).exists():
            print(f"Video file not found: {video_path}")
            return None
        
        # Prepare the upload
        files = {'file': open(video_path, 'rb')}
        data = {'target_language': target_language}
        
        print(f"Uploading {video_path} with target language: {target_language}")
        
        response = requests.post(
            f"{API_BASE_URL}/upload/",
            files=files,
            data=data
        )
        
        if response.status_code == 202:
            result = response.json()
            print(f"✅ Upload successful!")
            print(f"   Video ID: {result['video_id']}")
            print(f"   Language: {result['language_name']} ({result['target_language']})")
            print(f"   Status: {result['status']}")
            print(f"   Task ID: {result['task_id']}")
            return result['video_id']
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"Error during upload: {e}")
        return None

def check_video_status(video_id: str):
    """Check video processing status"""
    try:
        response = requests.get(f"{API_BASE_URL}/status/{video_id}")
        if response.status_code == 200:
            status = response.json()
            print(f"📊 Status for {video_id}:")
            print(f"   Status: {status.get('status', 'unknown')}")
            if 'progress' in status:
                print(f"   Progress: {status['progress']}%")
            if 'error' in status:
                print(f"   Error: {status['error']}")
            return status
        else:
            print(f"Error checking status: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def download_video(video_id: str, output_path: str = None):
    """Download processed video"""
    try:
        if output_path is None:
            output_path = f"downloaded_{video_id}.mp4"
        
        response = requests.get(f"{API_BASE_URL}/status/download/{video_id}")
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            print(f"✅ Video downloaded: {output_path}")
            return output_path
        else:
            print(f"❌ Download failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error downloading: {e}")
        return None

def monitor_video_processing(video_id: str, max_wait_time: int = 600):
    """Monitor video processing until completion"""
    print(f"🔄 Monitoring video processing for {video_id}...")
    
    start_time = time.time()
    while time.time() - start_time < max_wait_time:
        status = check_video_status(video_id)
        
        if status and status.get('status') == 'completed':
            print("✅ Video processing completed!")
            return True
        elif status and status.get('status') == 'failed':
            print("❌ Video processing failed!")
            return False
        
        print("⏳ Waiting 10 seconds...")
        time.sleep(10)
    
    print("⏰ Timeout reached")
    return False

def main():
    """Main test function"""
    print("🌍 Video Processing API - Language Test")
    print("=" * 50)
    
    # Get supported languages
    print("\n📋 Getting supported languages...")
    languages = get_supported_languages()
    if languages:
        print(f"Found {languages['count']} supported languages")
        print("Popular languages:")
        popular_langs = ['tr', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'zh']
        for lang in popular_langs:
            if lang in languages['languages']:
                print(f"   {lang}: {languages['languages'][lang]}")
    
    # Test video path (you need to provide a real video file)
    video_path = input("\n🎬 Enter path to your video file: ").strip()
    
    if not video_path or not Path(video_path).exists():
        print("❌ Please provide a valid video file path")
        return
    
    # Select language
    print("\n🌐 Select target language:")
    print("Popular options: tr (Turkish), es (Spanish), fr (French), de (German)")
    print("                 it (Italian), pt (Portuguese), ru (Russian)")
    print("                 ja (Japanese), ko (Korean), zh (Chinese)")
    
    target_lang = input("Enter language code (default: tr): ").strip() or "tr"
    
    # Upload video
    print(f"\n📤 Uploading video with language: {target_lang}")
    video_id = upload_video_with_language(video_path, target_lang)
    
    if not video_id:
        print("❌ Upload failed")
        return
    
    # Monitor processing
    print(f"\n🔄 Monitoring processing...")
    success = monitor_video_processing(video_id)
    
    if success:
        # Download video
        print(f"\n📥 Downloading processed video...")
        download_path = download_video(video_id)
        if download_path:
            print(f"🎉 Success! Processed video saved as: {download_path}")
        else:
            print("❌ Download failed")
    else:
        print("❌ Processing failed or timed out")

if __name__ == "__main__":
    main() 