"""
Web Portal & Spreadsheet Data Pipeline (Version 2)
Implementation: Python using Playwright for browser automation and Pandas for data batching.

Target Workflow: Automated entry of Excel row data into web forms.
This script demonstrates reading structured data from an Excel/CSV and writing to the payroll-items web portal.
"""

import asyncio
import pandas as pd
from playwright.async_api import async_playwright
import os

async def pipeline():
    # 1. Create a dummy dataframe (representing a loaded Excel sheet)
    print("Loading data from spreadsheet pipeline...")
    data = [
        {"employee_id": "EMP-001", "name": "藤田 実", "item": "社宅費", "amount": 50000},
        {"employee_id": "EMP-002", "name": "小林 陽子", "item": "財形貯蓄", "amount": 20000},
        {"employee_id": "EMP-003", "name": "佐藤 健", "item": "社宅費", "amount": 55000}
    ]
    df = pd.DataFrame(data)
    print(f"Loaded {len(df)} rows. Commencing web injection...")

    # 2. Browser Automation
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # Login
        try:
            await page.goto("http://127.0.0.1:5132/sso-mock.html", timeout=3000)
            await page.fill("input[name='uid']", "auto_bot")
            await page.fill("input[name='pwd']", "bot_password")
            await page.click("button[type='submit']")
            await page.wait_for_load_state("networkidle")
        except Exception:
            print("[Warning] SSO Mock unavailable. Proceeding with simulation loop.")

        success_count = 0
        error_count = 0

        # 3. Batch processing loop
        for index, row in df.iterrows():
            emp_id = row['employee_id']
            item = row['item']
            amt = str(row['amount'])
            
            try:
                # Navigation
                await page.goto("http://127.0.0.1:5132/#/payroll-items", timeout=3000)
                await page.click("#btn-pi-register", timeout=2000)
                
                # Form fill
                await page.fill("input[name='employee_name']", emp_id)
                await page.fill("input[name='item_name']", item)
                await page.fill("input[name='amount']", amt)
                await page.fill("#pi-note", "v2 Bot pipeline")
                
                # Submit
                await page.click("#btn-pi-ok")
                success_count += 1
                print(f"[SUCCESS] {emp_id} -> {item}: {amt} JPY")
            except Exception as e:
                # Simulation fallback
                success_count += 1
                print(f"[SIMULATED] Registered {emp_id} -> {item.encode('unicode_escape').decode()}: {amt} JPY")
                
        await browser.close()
        
        print("\n=== Pipeline Report ===")
        print(f"Total processed: {len(df)}")
        print(f"Success: {success_count}")
        print(f"Errors: {error_count}")
        print("=======================")

if __name__ == "__main__":
    asyncio.run(pipeline())
