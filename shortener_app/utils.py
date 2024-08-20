from urllib.parse import urlparse
from playwright.async_api import async_playwright
import logging 
import aiohttp
from aiohttp.client_exceptions import ClientConnectorError
import os
from pathlib import Path

def validate_and_correct_url(url: str) -> str:
    parsed_url = urlparse(url)
    if not parsed_url.scheme:
        # Add 'http' if no scheme is present
        url = 'http://' + url
    return url

def validate_url(url):
    parsed_url = urlparse(url)
    if not parsed_url.scheme or not parsed_url.netloc:
        return False
    return True


async def fetch_content_type(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.head(url) as response:
                return response.headers.get('Content-Type')
    except ClientConnectorError as e:
        print(f"Connection error: {e}")
        return None
        
async def capture_screenshot(url: str):
    '''content_type = await fetch_content_type(url)
    if 'text/html' not in content_type:
        print(f"URL is not an HTML page, content type: {content_type}")
        return None
    '''    
async def capture_screenshot(url: str):
    async with async_playwright() as playwright:
        parsed_url = urlparse(url)
        file_name = f"{parsed_url.netloc}{parsed_url.path.replace('/', '_')}.png"
        
        # Define the correct directory path relative to the project structure
        base_dir = os.path.dirname(__file__)  # Get the directory of the current script
        output_dir = os.path.join(base_dir, "static", "screenshots")
        os.makedirs(output_dir, exist_ok=True)  # Create the directory if it doesn't exist

        # Construct the full path to save the screenshot
        output_path = os.path.join(output_dir, file_name)

        # Launch the browser and take the screenshot
        firefox = playwright.firefox
        browser = await firefox.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            await page.goto(url, timeout=30000, wait_until="networkidle")
        except Exception as e:
            logging.error(f"Error: {e}")
            return None

        await page.screenshot(path=output_path, full_page=False)
        await browser.close()

        return file_name  # Return only the file name, not the full path