#!/usr/bin/env python3
"""
Test slider movement using JavaScript to see what happens
"""

import asyncio
from playwright.async_api import async_playwright

async def test_slider_movement():
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
            
            # Get initial values using JavaScript
            initial_values = await page.evaluate("""
                () => {
                    const values = [];
                    for (let i = 0; i < 6; i++) {
                        const slider = document.getElementById(`joint-slider-${i}`);
                        if (slider) {
                            values.push({
                                joint: i + 1,
                                value: parseFloat(slider.value),
                                min: parseFloat(slider.min),
                                max: parseFloat(slider.max)
                            });
                        }
                    }
                    return values;
                }
            """)
            
            print("📊 Initial slider values:")
            for val in initial_values:
                print(f"  Joint {val['joint']}: {val['value']:.2f}° (range: {val['min']}° to {val['max']}°)")
            
            # Clear previous requests
            network_requests.clear()
            console_messages.clear()
            
            print(f"\n🎛️ Simulating slider movement on Joint 1...")
            
            # Simulate moving the first slider using JavaScript
            result = await page.evaluate("""
                () => {
                    const slider = document.getElementById('joint-slider-0');
                    if (slider) {
                        const oldValue = slider.value;
                        const newValue = parseFloat(oldValue) + 1.0;
                        slider.value = newValue;
                        
                        // Trigger the input event
                        moveJoint(0, newValue);
                        
                        return {
                            success: true,
                            oldValue: oldValue,
                            newValue: newValue
                        };
                    }
                    return { success: false };
                }
            """)
            
            if result['success']:
                print(f"  Moved slider from {result['oldValue']}° to {result['newValue']}°")
            
            # Wait for any updates
            await page.wait_for_timeout(2000)
            
            # Get values after movement
            after_values = await page.evaluate("""
                () => {
                    const values = [];
                    for (let i = 0; i < 6; i++) {
                        const slider = document.getElementById(`joint-slider-${i}`);
                        if (slider) {
                            values.push({
                                joint: i + 1,
                                value: parseFloat(slider.value)
                            });
                        }
                    }
                    return values;
                }
            """)
            
            print("\n📊 Slider values AFTER movement:")
            for i, val in enumerate(after_values):
                initial_val = initial_values[i]['value']
                current_val = val['value']
                change = current_val - initial_val
                change_str = f" (changed by {change:+.2f}°)" if abs(change) > 0.01 else ""
                print(f"  Joint {val['joint']}: {current_val:.2f}°{change_str}")
            
            print(f"\n🌐 Network activity ({len(network_requests)} requests):")
            for req in network_requests:
                print(f"  {req}")
                
            print(f"\n📝 Console messages ({len(console_messages)}):")
            for msg in console_messages:
                print(f"  {msg}")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_slider_movement())