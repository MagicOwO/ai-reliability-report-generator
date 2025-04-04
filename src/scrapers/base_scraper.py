from abc import ABC, abstractmethod
from typing import List, Dict, Any
import aiohttp
import asyncio
from datetime import datetime
import logging
import time
import functools
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

def sync_to_async(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, functools.partial(func, *args, **kwargs))
    return wrapper

class BaseScraper(ABC):
    """Base class for status page scrapers"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = None
        self.playwright = None
        self.browser = None
        self.page = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    async def __aenter__(self):
        logger.debug(f"Creating session for {self.base_url}")
        self.session = aiohttp.ClientSession(headers=self.headers)
        
        # Initialize Playwright
        await self._init_browser()
        
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            logger.debug("Closing session")
            await self.session.close()
            
        if self.page:
            logger.debug("Closing Playwright page")
            await self.page.close()
            
        if self.browser:
            logger.debug("Closing Playwright browser")
            await self.browser.close()
            
        if self.playwright:
            logger.debug("Stopping Playwright")
            await self.playwright.stop()

    async def _init_browser(self):
        """Initialize Playwright browser"""
        try:
            logger.debug("Starting Playwright")
            self.playwright = await async_playwright().start()
            
            logger.debug("Launching Chromium browser")
            self.browser = await self.playwright.chromium.launch(
                headless=True,
            )
            
            logger.debug("Creating new page")
            self.page = await self.browser.new_page(
                user_agent=self.headers['User-Agent'],
                viewport={'width': 1920, 'height': 1080}
            )
            
            # Set default timeout
            self.page.set_default_timeout(30000)
            
            logger.debug("Playwright browser initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Playwright browser: {str(e)}")
            raise

    @abstractmethod
    async def fetch_incidents(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        Fetch incidents between start_date and end_date
        
        Args:
            start_date: Start date for incident fetching
            end_date: End date for incident fetching
            
        Returns:
            List of incidents with their details
        """
        pass

    async def _fetch_page(self, url: str) -> str:
        """
        Fetch a page with retry logic using Playwright
        
        Args:
            url: URL to fetch
            
        Returns:
            Page content as string
        """
        max_retries = 3
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                logger.debug(f"Fetching {url} (attempt {attempt + 1}/{max_retries})")
                
                # Navigate to the URL
                await self.page.goto(url, wait_until='networkidle')
                
                # Wait for the main content to load
                try:
                    await self.page.wait_for_selector('.layout-content', timeout=10000)
                except Exception as e:
                    logger.warning(f"Could not find .layout-content, continuing anyway: {str(e)}")
                
                # Wait a bit more for dynamic content to load
                await asyncio.sleep(2)
                
                # Get the page content
                content = await self.page.content()
                
                if not content:
                    logger.warning(f"Received empty content from {url}")
                else:
                    logger.debug(f"Successfully fetched {url} ({len(content)} bytes)")
                    logger.debug(f"First 1000 characters: {content[:1000]}")
                    
                return content
                    
            except Exception as e:
                logger.error(f"Error fetching {url}: {str(e)} (attempt {attempt + 1})")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(retry_delay * (attempt + 1))

    @abstractmethod
    async def parse_page(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse page content to extract incidents
        
        Args:
            content: HTML content of the page
            
        Returns:
            List of incidents with their details
        """
        pass 