#!/usr/bin/env python3
"""
Test both the Demo and Home buttons to see if there's a difference
"""

import asyncio
from playwright.async_api import async_playwright
import time

async def test_buttons():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        console_messages = []
        network_requests = []
        
        page.on("console", lambda msg: console_messages.append(f"[{msg.type}] {msg.text}"))
        page.on("request", lambda request: network_requests.append(f"→ {request.method} {request.url}"))
        page.on("response", lambda response: network_requests.append(f"← {response.status} {response.url}"))
        
        try:
            await page.goto("http://localhost:5000", timeout=10000)
            await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(3000)
            
            print("🎮 Testing Home Button...")
            network_requests.clear()
            console_messages.clear()
            
            # Click the Home button
            home_button = await page.query_selector('button[onclick="moveHome()"]')
            if home_button:
                await home_button.click()
                print("  ✅ Home button clicked")
                
                # Wait for the API call to complete (6 seconds + buffer)
                await page.wait_for_timeout(8000)
                
                print(f"\n📡 Network requests for Home button ({len(network_requests)}):")
                for req in network_requests:
                    print(f"    {req}")
                
                print(f"\n📝 Console messages for Home button ({len(console_messages)}):")
                for msg in console_messages:
                    print(f"    {msg}")
            else:
                print("  ❌ Home button not found")
                
            print(f"\n" + "="*50)
            print("🎮 Testing Demo Button...")
            network_requests.clear()
            console_messages.clear()
            
            # Click the Demo button
            demo_button = await page.query_selector('button[onclick="runDemo()"]')
            if demo_button:
                await demo_button.click()
                print("  ✅ Demo button clicked")
                
                # Wait for the API call to complete (longer for demo)
                await page.wait_for_timeout(12000)
                
                print(f"\n📡 Network requests for Demo button ({len(network_requests)}):")
                for req in network_requests:
                    print(f"    {req}")
                
                print(f"\n📝 Console messages for Demo button ({len(console_messages)}):")
                for msg in console_messages:
                    print(f"    {msg}")
            else:
                print("  ❌ Demo button not found")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_buttons())