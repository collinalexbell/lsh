#!/usr/bin/env python3
"""
Test script to reproduce and fix the camera screenshot freeze issue
"""
import asyncio
import time
from playwright.async_api import async_playwright

async def test_camera_freeze():
    """Test the camera freeze issue systematically"""
    
    async with async_playwright() as p:
        # Launch browser in headless mode
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("🌐 Opening web app...")
        await page.goto("http://localhost:5000/command-center")
        await page.wait_for_load_state('networkidle')
        
        print("📸 Taking initial screenshot of web app...")
        await page.screenshot(path="/tmp/webapp_step1_initial.png")
        
        # Wait for page to fully load and enable camera button
        print("⏳ Waiting for page initialization...")
        await page.wait_for_timeout(5000)
        
        # Stop camera first if it's running
        stop_disabled = await page.is_disabled("#stop-camera-btn")
        if not stop_disabled:
            print("🛑 Stopping existing camera...")
            await page.click("#stop-camera-btn")
            await page.wait_for_timeout(2000)
        
        # Check if start button is enabled, if not force enable it
        is_disabled = await page.is_disabled("#start-camera-btn")
        if is_disabled:
            print("🔧 Camera button disabled, force enabling...")
            await page.evaluate("document.getElementById('start-camera-btn').disabled = false")
        
        # Start camera
        print("🎥 Starting camera...")
        await page.click("#start-camera-btn")
        await page.wait_for_timeout(2000)  # Wait for camera API
        
        # Force browser to request video feed
        print("🎥 Forcing video feed request...")
        await page.evaluate("document.getElementById('video-stream').src = '/video_feed'")
        await page.wait_for_timeout(3000)  # Wait for video stream to start
        
        print("📸 Taking screenshot after camera start...")
        await page.screenshot(path="/tmp/webapp_step2_camera_started.png")
        
        # Move robot to Zeus position
        print("🤖 Moving robot to Zeus position...")
        await page.click('button:has-text("Zeus")')
        await page.wait_for_timeout(3000)  # Wait for movement
        
        print("📸 Taking screenshot after Zeus movement...")
        await page.screenshot(path="/tmp/webapp_step3_zeus_position.png")
        
        # Move robot to Tao book position  
        print("🤖 Moving robot to Tao book position...")
        await page.click('button:has-text("Tao book")')
        await page.wait_for_timeout(3000)  # Wait for movement
        
        print("📸 Taking screenshot after Tao book movement...")
        await page.screenshot(path="/tmp/webapp_step4_tao_position.png")
        
        print("✅ BASELINE TEST COMPLETE - Robot movement working")
        
        # Now test the screenshot freeze issue
        print("\n🔍 TESTING SCREENSHOT FREEZE ISSUE...")
        
        # Monitor network requests
        page.on("request", lambda request: print(f"REQUEST: {request.method} {request.url}"))
        page.on("response", lambda response: print(f"RESPONSE: {response.status} {response.url}"))
        
        # Take app screenshot of current camera feed
        print("📸 Taking app screenshot...")
        await page.click("#screenshot-btn")
        await page.wait_for_timeout(3000)  # Wait longer to see network activity
        
        print("📸 Taking screenshot after app screenshot...")
        await page.screenshot(path="/tmp/webapp_step5_after_app_screenshot.png")
        
        # Move robot again
        print("🤖 Moving robot back to Zeus...")
        await page.click('button:has-text("Zeus")')
        await page.wait_for_timeout(3000)
        
        print("📸 Taking final screenshot...")
        await page.screenshot(path="/tmp/webapp_step6_zeus_after_screenshot.png")
        
        print("✅ TEST COMPLETE")
        print("📁 Check screenshots in /tmp/webapp_step*.png")
        
        # Use automated image comparison to determine if camera froze
        import subprocess
        try:
            result = subprocess.run([
                "python3", "image_diff_checker.py", 
                "/tmp/webapp_step4_tao_position.png",
                "/tmp/webapp_step6_zeus_after_screenshot.png"
            ], capture_output=True, text=True)
            
            if result.returncode == 1:
                print("❌ CAMERA FREEZE DETECTED - Screenshots are identical!")
                print("🔧 The fix is NOT working - camera feed froze after screenshot")
            elif result.returncode == 0:
                print("✅ CAMERA WORKING - Screenshots are different!")  
                print("🎉 The fix IS working - camera feed continued after screenshot")
            else:
                print("⚠️  Error running image comparison")
                print(result.stderr)
                
            print("\nDetailed comparison:")
            print(result.stdout)
            
        except Exception as e:
            print(f"Error running image comparison: {e}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_camera_freeze())