#!/usr/bin/env python3
"""
Test slider movement to see what happens when we move a joint
"""

import asyncio
from playwright.async_api import async_playwright
import time

async def test_slider_movement():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Collect console messages and errors
        console_messages = []
        errors = []
        network_requests = []
        
        page.on("console", lambda msg: console_messages.append(f"[{msg.type}] {msg.text}"))
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("request", lambda request: network_requests.append(f"→ {request.method} {request.url}"))
        page.on("response", lambda response: network_requests.append(f"← {response.status} {response.url}"))
        
        try:
            print("🔍 Loading web app...")
            await page.goto("http://localhost:5000", timeout=10000)
            await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(3000)  # Wait for initialization
            
            # Get initial slider values
            print("\n📊 Initial slider values:")
            for i in range(6):
                slider = await page.query_selector(f"#joint-slider-{i}")
                if slider:
                    value = await slider.get_attribute("value")
                    min_val = await slider.get_attribute("min")
                    max_val = await slider.get_attribute("max")
                    print(f"  Joint {i+1}: {value}° (range: {min_val}° to {max_val}°)")
            
            print("\n🎛️ Moving first slider slightly...")
            first_slider = await page.query_selector("#joint-slider-0")
            if first_slider:
                # Get current value and move it slightly
                current_value = float(await first_slider.get_attribute("value"))
                new_value = current_value + 1.0  # Move 1 degree
                print(f"  Moving from {current_value}° to {new_value}°")
                
                # Clear previous network requests
                network_requests.clear()
                
                # Move the slider
                await first_slider.fill(str(new_value))
                await first_slider.dispatch_event("input")
                
                # Wait for any network requests to complete
                await page.wait_for_timeout(2000)
                
                # Check all slider values after movement
                print("\n📊 Slider values AFTER moving first slider:")
                for i in range(6):
                    slider = await page.query_selector(f"#joint-slider-{i}")
                    if slider:
                        value = await slider.get_attribute("value")
                        print(f"  Joint {i+1}: {value}°")
                
                print(f"\n🌐 Network requests during slider movement ({len(network_requests)}):")
                for req in network_requests[-10:]:  # Show last 10 requests
                    print(f"  {req}")
                
                print(f"\n📝 Console messages during movement:")
                for msg in console_messages[-5:]:  # Show last 5 messages
                    print(f"  {msg}")
                    
            print(f"\n❌ JavaScript Errors ({len(errors)}):")
            for error in errors:
                print(f"  ERROR: {error}")
                
        except Exception as e:
            print(f"❌ Failed to test slider movement: {e}")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_slider_movement())