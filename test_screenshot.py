#!/usr/bin/env python3

import asyncio
import base64
import os
import time
from playwright.async_api import async_playwright
import cv2
import numpy as np
from PIL import Image
import io

async def test_screenshot_functionality():
    """Test the screenshot functionality using headless browser"""
    
    # Create downloads directory
    downloads_dir = "/home/er/lsh/test_downloads"
    os.makedirs(downloads_dir, exist_ok=True)
    
    async with async_playwright() as p:
        # Launch browser with download path
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            accept_downloads=True,
            viewport={'width': 1280, 'height': 720}
        )
        
        # Set download behavior
        page = await context.new_page()
        
        try:
            print("🌐 Navigating to web app...")
            await page.goto("http://localhost:5000", timeout=10000)
            await page.wait_for_load_state('networkidle')
            
            print("📷 Starting camera...")
            await page.click('#start-camera-btn')
            await asyncio.sleep(3)  # Wait for camera to initialize
            
            print("📸 Taking screenshot...")
            # Start download waiter before clicking
            async with page.expect_download() as download_info:
                await page.click('#screenshot-btn')
                download = await download_info.value
            
            # Save the downloaded file
            screenshot_path = os.path.join(downloads_dir, f"test_screenshot_{int(time.time())}.jpg")
            await download.save_as(screenshot_path)
            
            print(f"✅ Screenshot saved to: {screenshot_path}")
            
            # Verify the file exists and is a valid image
            if os.path.exists(screenshot_path):
                file_size = os.path.getsize(screenshot_path)
                print(f"📊 File size: {file_size} bytes")
                
                # Check if it's a valid JPEG
                try:
                    with Image.open(screenshot_path) as img:
                        print(f"🖼️  Image format: {img.format}")
                        print(f"📏 Image size: {img.size}")
                        print(f"🎨 Image mode: {img.mode}")
                        
                        # Convert to numpy array for analysis
                        img_array = np.array(img)
                        
                        # Basic image analysis
                        mean_brightness = np.mean(img_array)
                        print(f"💡 Average brightness: {mean_brightness:.1f}")
                        
                        # Check if image has significant content (not just black/white)
                        std_dev = np.std(img_array)
                        print(f"📈 Pixel standard deviation: {std_dev:.1f}")
                        
                        if std_dev > 10:  # Threshold for "real" image content
                            print("✅ Image appears to contain actual webcam content")
                        else:
                            print("⚠️  Image appears to be mostly uniform (may be error screen)")
                        
                        # Try to detect if this looks like a webcam feed
                        # Check color distribution
                        if len(img_array.shape) == 3:  # Color image
                            r_mean = np.mean(img_array[:,:,0])
                            g_mean = np.mean(img_array[:,:,1])
                            b_mean = np.mean(img_array[:,:,2])
                            print(f"🔴 Red channel avg: {r_mean:.1f}")
                            print(f"🟢 Green channel avg: {g_mean:.1f}")
                            print(f"🔵 Blue channel avg: {b_mean:.1f}")
                        
                        # Analyze what might be in the image
                        print("\n🔍 Image Analysis:")
                        analyze_image_content(img_array)
                        
                        return True, screenshot_path
                        
                except Exception as e:
                    print(f"❌ Error opening image: {e}")
                    return False, screenshot_path
            else:
                print("❌ Screenshot file not found")
                return False, None
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False, None
            
        finally:
            await browser.close()

def analyze_image_content(img_array):
    """Analyze the content of the screenshot"""
    height, width = img_array.shape[:2]
    
    # Check if image is mostly dark (camera off) or bright (camera on)
    brightness = np.mean(img_array)
    
    if brightness < 30:
        print("🌚 Image is very dark - camera may be off or covered")
    elif brightness > 200:
        print("🌞 Image is very bright - may be overexposed or showing bright scene")
    else:
        print(f"🌗 Image has moderate brightness ({brightness:.1f}) - likely showing normal scene")
    
    # Check for edges (indicates structured content)
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array
        
    edges = cv2.Canny(gray, 50, 150)
    edge_density = np.sum(edges > 0) / (height * width)
    
    print(f"🔲 Edge density: {edge_density:.4f}")
    
    if edge_density > 0.05:
        print("📐 High edge density - image contains structured objects/scenes")
    elif edge_density > 0.01:
        print("📄 Moderate edge density - some structure visible")
    else:
        print("⬜ Low edge density - mostly uniform content")
    
    # Check for common webcam artifacts
    # Look for typical webcam resolution patterns
    if width == 640 and height == 480:
        print("📹 Standard VGA webcam resolution detected")
    elif width == 1280 and height == 720:
        print("📹 HD webcam resolution detected")
    elif width == 1920 and height == 1080:
        print("📹 Full HD webcam resolution detected")
    
    # Simple motion blur detection (can indicate live feed)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    print(f"🌊 Image sharpness metric: {laplacian_var:.1f}")
    
    if laplacian_var < 100:
        print("🌫️  Image appears blurry (motion or focus issues)")
    else:
        print("🔍 Image appears reasonably sharp")

async def main():
    print("🧪 Starting screenshot functionality test...\n")
    
    success, screenshot_path = await test_screenshot_functionality()
    
    if success:
        print(f"\n✅ Test completed successfully!")
        print(f"📁 Screenshot saved at: {screenshot_path}")
    else:
        print(f"\n❌ Test failed!")
        if screenshot_path:
            print(f"📁 Partial file may exist at: {screenshot_path}")

if __name__ == "__main__":
    asyncio.run(main())