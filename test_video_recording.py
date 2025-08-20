#!/usr/bin/env python3

import asyncio
import os
import time
from playwright.async_api import async_playwright
import cv2
import numpy as np
from PIL import Image

async def test_video_recording_functionality():
    """Test the video recording functionality using headless browser"""
    
    # Create test downloads directory
    test_downloads_dir = "/home/er/lsh/test_downloads"
    os.makedirs(test_downloads_dir, exist_ok=True)
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            accept_downloads=True,
            viewport={'width': 1280, 'height': 720}
        )
        
        page = await context.new_page()
        
        try:
            print("🌐 Navigating to web app...")
            await page.goto("http://localhost:5000", timeout=10000)
            await page.wait_for_load_state('networkidle')
            
            print("📷 Starting camera...")
            await page.click('#start-camera-btn')
            await asyncio.sleep(3)  # Wait for camera to initialize
            
            print("🎥 Starting video recording...")
            await page.click('#start-video-btn')
            await asyncio.sleep(2)  # Wait for recording to start
            
            # Check if recording status is updated
            video_status = await page.text_content('#video-recording-status')
            print(f"📊 Video recording status: {video_status}")
            
            # Simulate some robot movements (optional - move some joints)
            print("🤖 Simulating robot movement during recording...")
            
            # Move joint 1 (Base) a bit
            await page.fill('#joint-slider-0', '30')
            await page.dispatch_event('#joint-slider-0', 'input')
            await asyncio.sleep(1)
            
            # Move joint 2 (Shoulder) 
            await page.fill('#joint-slider-1', '-45')
            await page.dispatch_event('#joint-slider-1', 'input')
            await asyncio.sleep(1)
            
            # Move back to center
            await page.fill('#joint-slider-0', '0')
            await page.dispatch_event('#joint-slider-0', 'input')
            await asyncio.sleep(1)
            
            await page.fill('#joint-slider-1', '0')
            await page.dispatch_event('#joint-slider-1', 'input')
            await asyncio.sleep(1)
            
            print("⏱️  Recording for a few more seconds...")
            await asyncio.sleep(3)  # Record for a bit longer
            
            print("⏹️  Stopping video recording...")
            await page.click('#stop-video-btn')
            await asyncio.sleep(2)  # Wait for recording to stop
            
            # Check if we get a download link
            video_status_element = await page.query_selector('#video-status')
            video_status_html = await video_status_element.inner_html()
            print(f"📄 Video status after stopping: {video_status_html}")
            
            # Try to download the video by finding the download link
            download_link = await page.query_selector('#video-status a')
            if download_link:
                print("🔗 Found download link, attempting download...")
                
                # Start download waiter before clicking
                async with page.expect_download() as download_info:
                    await download_link.click()
                    download = await download_info.value
                
                # Save the downloaded file
                video_path = os.path.join(test_downloads_dir, f"test_video_{int(time.time())}.mp4")
                await download.save_as(video_path)
                
                print(f"✅ Video saved to: {video_path}")
                return True, video_path
            else:
                print("❌ No download link found")
                return False, None
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False, None
            
        finally:
            await browser.close()

def analyze_video_file(video_path):
    """Analyze the recorded video file"""
    if not os.path.exists(video_path):
        print("❌ Video file not found")
        return False
    
    file_size = os.path.getsize(video_path)
    print(f"📊 Video file size: {file_size} bytes")
    
    if file_size < 1000:  # Very small file, likely empty or corrupt
        print("⚠️  Video file is very small, may be corrupt")
        return False
    
    try:
        # Try to open with OpenCV
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            print("❌ Could not open video file with OpenCV")
            return False
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0
        
        print(f"🎬 Video properties:")
        print(f"   📏 Resolution: {width}x{height}")
        print(f"   🎞️  Frame count: {frame_count}")
        print(f"   ⚡ FPS: {fps}")
        print(f"   ⏱️  Duration: {duration:.2f} seconds")
        
        if frame_count == 0:
            print("⚠️  Video has no frames")
            cap.release()
            return False
        
        # Read and analyze a few frames
        frames_to_check = min(5, frame_count)
        frame_brightness = []
        
        for i in range(frames_to_check):
            # Set frame position
            cap.set(cv2.CAP_PROP_POS_FRAMES, i * (frame_count // frames_to_check))
            ret, frame = cap.read()
            
            if ret:
                brightness = np.mean(frame)
                frame_brightness.append(brightness)
            else:
                print(f"⚠️  Could not read frame {i}")
        
        cap.release()
        
        if frame_brightness:
            avg_brightness = np.mean(frame_brightness)
            brightness_variation = np.std(frame_brightness)
            
            print(f"💡 Average brightness: {avg_brightness:.1f}")
            print(f"📈 Brightness variation: {brightness_variation:.1f}")
            
            if avg_brightness > 10:  # Not completely black
                print("✅ Video appears to contain actual content")
                
                if brightness_variation > 5:  # Some variation between frames
                    print("✅ Video shows variation between frames (likely real recording)")
                else:
                    print("⚠️  Video shows little variation (may be static)")
                
                return True
            else:
                print("⚠️  Video appears to be mostly black")
                return False
        else:
            print("❌ Could not analyze video frames")
            return False
    
    except Exception as e:
        print(f"❌ Error analyzing video: {e}")
        return False

async def main():
    print("🧪 Starting video recording functionality test...\n")
    
    success, video_path = await test_video_recording_functionality()
    
    if success and video_path:
        print(f"\n✅ Video recording test completed successfully!")
        print(f"📁 Video saved at: {video_path}")
        
        print(f"\n🔍 Analyzing video file...")
        video_valid = analyze_video_file(video_path)
        
        if video_valid:
            print(f"\n🎉 Video recording functionality is working correctly!")
        else:
            print(f"\n⚠️  Video was created but may have issues")
    else:
        print(f"\n❌ Video recording test failed!")

if __name__ == "__main__":
    asyncio.run(main())