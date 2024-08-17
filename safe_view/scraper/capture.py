import asyncio
from urllib.parse import urlparse
from playwright.async_api import async_playwright
import logging 
import asyncio
import aiohttp

async def fetch_content_type(url):
    async with aiohttp.ClientSession() as session:
        async with session.head(url) as response:
            return response.headers.get('Content-Type')
        
async def capture_screenshot(url: str):
    content_type = await fetch_content_type(url)
    if 'text/html' not in content_type:
        print(f"URL is not an HTML page, content type: {content_type}")
        return None
    
    async with async_playwright() as playwright:
        parsed_url = urlparse(url)
        # Replace '/' with '_' to create a valid file name
        file_name = f"{parsed_url.netloc}{parsed_url.path.replace('/', '_')}.png"
        # Save the screenshot in the 'static' folder
        output_path = f"safe_view/static/screenshots/{file_name}"

        # chromium = playwright.chromium
        # browser = await chromium.launch(headless=True)
        firefox = playwright.firefox
        browser = await firefox.launch(headless=True)

        # page = await browser.new_page(viewport={'width': 1280, 'height': 720})

        # สร้าง context ใหม่พร้อมกำหนด User-Agent
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.4472.124 Safari/537.36",
            viewport={'width': 1280, 'height': 720}
        )
        page = await context.new_page()

        try:
            await page.goto(url, timeout=30000) # , wait_until="domcontentloaded"
        except Exception as e:
            print("The page took too long to load or cannot be accessed.")
            logging.error(f"Error: {e}")
            return None

        
        await page.screenshot(path=output_path, full_page=False)
        await browser.close()

        return file_name  # Return just the file name, not the full path
