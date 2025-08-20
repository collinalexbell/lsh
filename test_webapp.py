#!/usr/bin/env python3
"""
Web app testing script using Playwright to check for JavaScript errors
"""

import asyncio
from playwright.async_api import async_playwright
import json

async def test_webapp():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Collect console messages and errors
        console_messages = []
        errors = []
        
        page.on("console", lambda msg: console_messages.append(f"[{msg.type}] {msg.text}"))
        page.on("pageerror", lambda error: errors.append(str(error)))
        
        try:
            # Navigate to the web app
            print("🔍 Loading web app at http://localhost:5000...")
            await page.goto("http://localhost:5000", timeout=10000)
            
            # Wait for the page to load completely
            await page.wait_for_load_state('networkidle', timeout=10000)
            
            # Wait a bit more for JavaScript to execute
            await page.wait_for_timeout(3000)
            
            print("\n📊 Page Analysis:")
            print(f"Title: {await page.title()}")
            
            # Check if joint controls container exists
            joint_controls = await page.query_selector("#joint-controls")
            if joint_controls:
                print("✅ joint-controls container found")
                
                # Count joint sliders
                sliders = await page.query_selector_all(".joint-slider")
                print(f"🎛️ Found {len(sliders)} sliders")
                
                # Get the content of joint-controls div
                content = await joint_controls.inner_html()
                print(f"📄 Joint controls content preview: {content[:200]}...")
                
            else:
                print("❌ joint-controls container NOT found")
            
            # Check for speed slider
            speed_slider = await page.query_selector("#speed-slider")
            print(f"🎚️ Speed slider found: {speed_slider is not None}")
            
            # Test the API endpoint
            try:
                response = await page.goto("http://localhost:5000/api/joints/get_current")
                if response.status == 200:
                    api_data = await response.json()
                    print(f"✅ API working - got {len(api_data.get('angles', []))} joint angles")
                else:
                    print(f"❌ API error - status {response.status}")
            except Exception as e:
                print(f"❌ API request failed: {e}")
            
            # Go back to main page
            await page.goto("http://localhost:5000")
            await page.wait_for_timeout(2000)
            
            print(f"\n📝 Console Messages ({len(console_messages)}):")
            for msg in console_messages[-20:]:  # Show last 20 messages
                print(f"  {msg}")
            
            print(f"\n❌ JavaScript Errors ({len(errors)}):")
            for error in errors:
                print(f"  ERROR: {error}")
            
            # Take a screenshot for debugging
            await page.screenshot(path="/tmp/webapp_screenshot.png")
            print("\n📸 Screenshot saved to /tmp/webapp_screenshot.png")
            
        except Exception as e:
            print(f"❌ Failed to test web app: {e}")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_webapp())