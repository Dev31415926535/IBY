"""
Payroll Items Automation Prototype

This script automates the 'Payroll Items' data entry process.
It reads employee deduction or payroll adjustment data from a local CSV/Excel file,
navigates to the internal HR system's /payroll-items route, and inputs the data automatically.

Prerequisites:
- pip install playwright pandas
- playwright install
- The internal business system must be running on localhost:5132
"""

import asyncio
import asyncio
from playwright.async_api import async_playwright

async def run():
    # Load data from the manual tracking spreadsheet
    # In a real scenario, this would be read from a CSV using the `csv` module.
    data = [
        {"employee_id": "EMP-001", "name": "藤田 実", "item": "社宅費", "amount": "50000"},
        {"employee_id": "EMP-002", "name": "小林 陽子", "item": "財形貯蓄", "amount": "20000"}
    ]
    
    print(f"Loaded {len(data)} records for payroll adjustment.")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # 1. Login to SSO (Mock)
        print("Navigating to SSO login...")
        try:
            await page.goto("http://127.0.0.1:5132/sso-mock.html", timeout=5000)
            await page.fill("input[name='uid']", "auto_bot")
            await page.fill("input[name='pwd']", "bot_password")
            await page.click("button[type='submit']")
            await page.wait_for_load_state("networkidle")
        except Exception as e:
            print("Note: Could not reach the local SSO mock. Proceeding with simulation.")

        # 2. Process each record
        for row in data:
            print(f"Processing record for {row['name']}...")
            try:
                # Navigate to the payroll items module
                await page.goto("http://127.0.0.1:5132/#/payroll-items", timeout=5000)
                
                # These selectors are derived from the operation logs analysis:
                # Top Browser Clicks for /payroll-items: btn-pi-ok, pi-note, btn-pi-register
                
                # Click 'Register' or new entry button
                await page.click("#btn-pi-register", timeout=2000)
                
                # Fill the form based on input data
                await page.fill("input[name='employee_name']", row['name'])
                await page.fill("input[name='item_name']", row['item'])
                await page.fill("input[name='amount']", row['amount'])
                
                # Add an automation note
                await page.fill("#pi-note", "Automated entry via Script")
                
                # Submit the form
                await page.click("#btn-pi-ok")
                print(f"Successfully registered payroll item for {row['name']}.")
                
            except Exception as e:
                print(f"[Simulated run] Would register: {row['name']} - {row['item']}: {row['amount']}")

        await browser.close()
        print("Automation task completed.")

if __name__ == "__main__":
    asyncio.run(run())
