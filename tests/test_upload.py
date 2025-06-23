#!/usr/bin/env python3
"""
Test script for video upload functionality
"""
import requests
import os
import json

def upload_video(file_path, source_language, target_language):
    url = "http://localhost:8082/api/v1/upload"
    
    with open(file_path, 'rb') as f:
        files = {'file': (os.path.basename(file_path), f, 'video/mp4')}
        data = {
            'target_language': target_language
        }
        response = requests.post(url, files=files, data=data)
        print("Status code:", response.status_code)
        print("Response text:", response.text)
    
    return response.json()

def test_video_upload():
    print("=== Video Upload Test ===")
    
    # Check if test video exists
    test_video_path = "uploads/test_video.mp4"
    if not os.path.exists(test_video_path):
        print(f"Test video not found at {test_video_path}")
        print("Please ensure test_video.mp4 exists in the uploads folder")
        return False
    
    print(f"Found test video: {test_video_path}")
    
    # API endpoint
    api_url = "http://localhost:8082/api/v1/upload"
    print(f"Uploading video to: {api_url}")
    
    try:
        # Prepare the multipart form data
        with open(test_video_path, 'rb') as video_file:
            files = {
                'file': ('test_video.mp4', video_file, 'video/mp4')
            }
            data = {
                'language': 'en'
            }
            
            print(f"Making request to: {api_url}")
            print(f"Files: {files}")
            print(f"Data: {data}")
            
            # Make the request
            response = requests.post(api_url, files=files, data=data, timeout=60)
            
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {response.headers}")
            print(f"Response content: {response.text[:200]}...")
            
            if response.status_code == 200:
                result = response.json()
                print("Upload successful!")
                print(f"Response: {json.dumps(result, indent=2)}")
                
                if 'task_id' in result:
                    print(f"Task ID: {result['task_id']}")
                    print(f"You can check status at: http://localhost:8082/api/v1/status/{result['task_id']}")
                    print(f"Or view in admin panel: http://localhost:8181")
                    return result['task_id']
            else:
                print(f"Upload failed with status code: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"Upload failed!")
        print(f"Error: {str(e)}")
        return False

def check_status(task_id):
    """Check the status of a processing task"""
    print(f"\n=== Checking Status for Task {task_id} ===")
    
    try:
        status_url = f"http://localhost:8082/api/v1/status/{task_id}"
        response = requests.get(status_url, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"Status: {json.dumps(result, indent=2)}")
            return result
        else:
            print(f"Status check failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"Status check failed!")
        print(f"Error: {str(e)}")
        return None

if __name__ == "__main__":
    video_path = "uploads/testen.mp4"
    source_language = "en"
    target_language = "tr"
    
    print(f"Checking if video exists at {video_path}...")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Files in uploads directory: {os.listdir('uploads')}")
    
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        exit(1)
    
    print(f"Video file found! Size: {os.path.getsize(video_path)} bytes")
    
    try:
        result = upload_video(video_path, source_language, target_language)
        print("Upload successful!")
        print("Response:", result)
    except Exception as e:
        print(f"Upload failed: {str(e)}")
        exit(1) 