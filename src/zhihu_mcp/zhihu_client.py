"""Zhihu client - Browser automation via Playwright"""

import asyncio
import logging
from typing import Any, Dict
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)


class ZhihuClient:
    """Zhihu client that encapsulates idea and article publishing"""

    def __init__(self, cdp_endpoint: str = "http://192.168.2.6:19222"):
        """
        Initialize Zhihu client

        Args:
            cdp_endpoint: Chrome DevTools Protocol endpoint URL
        """
        self.cdp_endpoint = cdp_endpoint

        logger.info(
            "ZhihuClient initialized with CDP endpoint: %s",
            cdp_endpoint
        )

    async def publish_idea(
        self,
        title: str,
        content: str
    ) -> Dict[str, Any]:
        """
        Publish a Zhihu idea

        Args:
            title: Idea title (optional, max 50 chars)
            content: Idea content

        Returns:
            Publishing result with success status and message
        """
        logger.info("Starting to publish idea with title: %s", title)
        logger.debug("Content length: %d", len(content))

        async with async_playwright() as p:
            logger.debug("Connecting to browser via CDP: %s", self.cdp_endpoint)
            browser = await p.chromium.connect_over_cdp(self.cdp_endpoint)

            # Get the first page (assuming browser is already open)
            contexts = browser.contexts
            if not contexts:
                logger.error("No browser contexts found")
                return {
                    "success": False,
                    "message": "No browser contexts found"
                }

            context = contexts[0]
            pages = context.pages
            if not pages:
                logger.error("No pages found in browser context")
                return {
                    "success": False,
                    "message": "No pages found"
                }

            page = pages[0]
            logger.debug("Using existing page")

            try:
                # Step 1: Navigate to Zhihu homepage
                logger.debug("Navigating to Zhihu homepage")
                await page.goto(
                    "https://www.zhihu.com/",
                    wait_until="domcontentloaded"
                )
                logger.debug("Navigation completed")

                # Wait for page to load
                logger.debug("Waiting for page to load")
                await asyncio.sleep(2)

                # Step 2: Click "发想法" button to open idea form
                logger.debug("Clicking '发想法' button")
                idea_btn = page.locator('button').filter(has_text="发想法")
                await idea_btn.click()
                logger.debug("Idea button clicked")

                # Wait for form to appear
                logger.debug("Waiting for publish form to appear")
                await asyncio.sleep(2)

                # Step 3: Fill in the title with long timeout (5 minutes)
                logger.debug("Filling title field")
                title_input = page.locator('textarea[name="title"]')
                await title_input.fill(title, timeout=300000)
                logger.debug("Title filled successfully")

                # Wait for UI to update
                await asyncio.sleep(1)

                # Step 4: Fill in the content with long timeout (5 minutes)
                logger.debug("Filling content field")
                editor = page.locator('div[contenteditable="true"][role="textbox"]')
                await editor.fill(content, timeout=300000)
                logger.debug("Content filled successfully")

                # Wait for form validation
                logger.debug("Waiting for form validation")
                await asyncio.sleep(1)

                # Step 5: Click the publish button
                logger.debug("Clicking publish button")
                publish_btn = page.locator('button').filter(has_text="发布")
                await publish_btn.click()
                logger.debug("Publish button clicked")

                # Wait for publishing to complete
                logger.debug("Waiting for publishing to complete")
                await asyncio.sleep(3)

                # Step 6: Check the publishing result
                logger.debug("Checking publishing result")
                page_text = await page.locator('body').text_content()

                has_success_msg = '发布成功' in page_text
                success = has_success_msg
                message = (
                    'Published successfully' if has_success_msg
                    else 'Publishing status unknown'
                )

                if success:
                    logger.info("Idea published successfully")
                else:
                    logger.warning("Publishing result unclear: %s", message)

                return {
                    "success": success,
                    "message": message
                }

            finally:
                # Don't close browser since it's a shared instance
                await browser.close()
                logger.debug("Disconnected from browser")

    async def publish_article(
        self,
        title: str,
        content: str
    ) -> Dict[str, Any]:
        """
        Publish a Zhihu article

        Args:
            title: Article title
            content: Article content (supports Markdown)

        Returns:
            Publishing result with success status and message
        """
        logger.info("Starting to publish article with title: %s", title)
        logger.debug("Content length: %d", len(content))

        async with async_playwright() as p:
            logger.debug("Connecting to browser via CDP: %s", self.cdp_endpoint)
            browser = await p.chromium.connect_over_cdp(self.cdp_endpoint)

            # Get the first page (assuming browser is already open)
            contexts = browser.contexts
            if not contexts:
                logger.error("No browser contexts found")
                return {
                    "success": False,
                    "message": "No browser contexts found"
                }

            context = contexts[0]
            pages = context.pages
            if not pages:
                logger.error("No pages found in browser context")
                return {
                    "success": False,
                    "message": "No pages found"
                }

            page = pages[0]
            logger.debug("Using existing page")

            try:
                # Step 1: Navigate to article write page
                logger.debug("Navigating to article write page")
                await page.goto(
                    "https://zhuanlan.zhihu.com/write",
                    wait_until="domcontentloaded"
                )
                logger.debug("Navigation completed")

                # Wait for page to load
                logger.debug("Waiting for page to load")
                await asyncio.sleep(3)

                # Step 2: Fill title with long timeout (5 minutes)
                logger.debug("Filling title field")
                title_input = page.locator('textarea[placeholder]')
                await title_input.fill(title, timeout=300000)
                logger.debug("Title filled successfully")

                # Wait for UI to update
                await asyncio.sleep(1)

                # Step 3: Fill content with long timeout (5 minutes)
                logger.debug("Filling content field")
                editor = page.locator('div[contenteditable="true"][role="textbox"]')
                await editor.fill(content, timeout=300000)
                logger.debug("Content filled successfully")

                # Wait for auto-save to complete
                logger.debug("Waiting for auto-save to complete")
                await asyncio.sleep(3)

                # Step 4: Click publish button
                # Use filter to match exact text "发布", not "发布设置"
                logger.debug("Clicking publish button")
                publish_btn = page.locator('button').filter(has_text="发布").filter(has_not_text="设置")
                await publish_btn.click()
                logger.debug("Publish button clicked")

                # Wait for publishing to complete
                logger.debug("Waiting for publishing to complete")
                await asyncio.sleep(5)

                # Step 5: Check the publishing result
                logger.debug("Checking publishing result")
                current_url = page.url
                page_text = await page.locator('body').text_content()

                has_success_msg = '发布成功' in page_text
                is_article_page = '/p/' in current_url

                success = has_success_msg or is_article_page
                message = (
                    'Published successfully' if has_success_msg
                    else ('Redirected to article page' if is_article_page
                          else 'Publishing status unknown')
                )

                if success:
                    logger.info("Article published successfully")
                    logger.info("Article URL: %s", current_url)
                else:
                    logger.warning("Publishing result unclear: %s", message)

                return {
                    "success": success,
                    "message": message,
                    "url": current_url
                }

            finally:
                # Don't close browser since it's a shared instance
                await browser.close()
                logger.debug("Disconnected from browser")
