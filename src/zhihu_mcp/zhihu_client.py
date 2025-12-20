"""Zhihu client - Browser automation via Playwright"""

import asyncio
import json
import logging
from typing import Any, Dict
from playwright.async_api import async_playwright, Browser, Page
from fastmcp import Client
from fastmcp.client import NpxStdioTransport

logger = logging.getLogger(__name__)


class ZhihuClient:
    """Zhihu client that encapsulates idea and article publishing"""

    def __init__(
        self,
        cdp_endpoint: str = "http://192.168.2.6:19222",
        chrome_package: str = "chrome-devtools-mcp@latest"
    ):
        """
        Initialize Zhihu client

        Args:
            cdp_endpoint: Chrome DevTools Protocol endpoint URL
            chrome_package: NPM package name for chrome-devtools MCP (used by publish_idea)
        """
        self.cdp_endpoint = cdp_endpoint
        self.chrome_package = chrome_package
        self.chrome_args = [f"--browser-url={cdp_endpoint}"]

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

        # Create NPX transport for chrome-devtools MCP
        transport = NpxStdioTransport(
            package=self.chrome_package,
            args=self.chrome_args
        )
        logger.debug(
            "Connecting to chrome-devtools via npx: %s %s",
            self.chrome_package,
            " ".join(self.chrome_args)
        )

        async with Client(transport) as client:
            logger.debug("Connected to chrome-devtools MCP server")

            # Step 0: Navigate to Zhihu homepage
            logger.debug("Navigating to Zhihu homepage")
            await client.call_tool(
                "navigate_page",
                {
                    "type": "url",
                    "url": "https://www.zhihu.com/"
                }
            )
            logger.debug("Navigation completed")

            # Wait for page to load
            await asyncio.sleep(2)

            # Step 0.5: Click "发想法" button to open idea form
            logger.debug("Clicking '发想法' button")
            click_js = """() => {
                const btn = Array.from(
                    document.querySelectorAll('button')
                ).find(b => b.textContent.trim() === '发想法');
                if (!btn) {
                    return {
                        success: false,
                        error: 'Publish idea button not found'
                    };
                }
                btn.click();
                return { success: true };
            }"""

            click_result = await client.call_tool(
                "evaluate_script",
                {"function": click_js}
            )
            click_data = (
                click_result.data
                if hasattr(click_result, 'data')
                else click_result
            )
            logger.debug("Click result: %s", click_data)

            # Note: Click may return None due to page updates,
            # but the click still succeeds. Don't fail here.
            if click_data and not click_data.get("success"):
                logger.warning(
                    "Click button returned error: %s",
                    click_data.get("error")
                )

            # Wait for form to appear
            logger.debug("Waiting for publish form to appear")
            await asyncio.sleep(2)

            # Step 1: Fill in the title
            # Use JSON serialization for safe string passing
            logger.debug("Filling title field")
            title_js = f"""() => {{
                const titleText = {json.dumps(title)};
                const titleInput = document.querySelector(
                    'textarea[name="title"]'
                );
                if (!titleInput) {{
                    return {{
                        success: false,
                        error: 'Title input not found'
                    }};
                }}
                titleInput.value = titleText;
                titleInput.dispatchEvent(
                    new Event('input', {{ bubbles: true }})
                );
                return {{ success: true }};
            }}"""

            title_result = await client.call_tool(
                "evaluate_script",
                {"function": title_js}
            )
            title_data = title_result.data if hasattr(title_result, 'data') else title_result
            logger.debug("Title fill result: %s", title_data)

            # Note: Fill may return None due to page updates,
            # but the fill still succeeds. Don't fail here.
            if title_data and not title_data.get("success"):
                logger.warning(
                    "Fill title returned error: %s",
                    title_data.get("error")
                )

            # Step 2: Fill in the content
            # Use JSON serialization for safe string passing
            logger.debug("Filling content field")
            content_js = f"""() => {{
                const contentText = {json.dumps(content)};
                const editor = document.querySelector(
                    'div[contenteditable="true"][role="textbox"]'
                );
                if (!editor) {{
                    return {{
                        success: false,
                        error: 'Editor not found'
                    }};
                }}

                // Focus the editor first
                editor.focus();

                // For Draft.js editor, use execCommand to insert text
                // This properly updates the editor state
                document.execCommand('insertText', false, contentText);

                // Also trigger input event to ensure React updates
                editor.dispatchEvent(
                    new Event('input', {{ bubbles: true }})
                );
                editor.dispatchEvent(
                    new Event('change', {{ bubbles: true }})
                );

                return {{ success: true }};
            }}"""

            content_result = await client.call_tool(
                "evaluate_script",
                {"function": content_js}
            )
            content_data = (
                content_result.data
                if hasattr(content_result, 'data')
                else content_result
            )
            logger.debug("Content fill result: %s", content_data)

            # Note: Fill may return None, but operation might still succeed
            if content_data and not content_data.get("success"):
                logger.warning(
                    "Fill content returned error: %s",
                    content_data.get("error")
                )

            # Wait for form validation (max 1 second)
            logger.debug("Waiting for form validation")
            await asyncio.sleep(1)

            # Step 3: Click the publish button
            logger.debug("Clicking publish button")
            publish_js = """() => {
                const publishBtn = Array.from(
                    document.querySelectorAll('button')
                ).find(b => b.textContent.trim() === '发布');

                if (!publishBtn) {
                    return {
                        success: false,
                        error: 'Publish button not found'
                    };
                }

                if (publishBtn.disabled) {
                    return {
                        success: false,
                        error: 'Publish button is disabled'
                    };
                }

                publishBtn.click();
                return { success: true };
            }"""

            publish_result = await client.call_tool(
                "evaluate_script",
                {"function": publish_js}
            )
            publish_data = (
                publish_result.data
                if hasattr(publish_result, 'data')
                else publish_result
            )
            logger.debug("Publish button click result: %s", publish_data)

            # Note: Click may return None, but operation might still succeed
            if publish_data and not publish_data.get("success"):
                logger.warning(
                    "Click publish button returned error: %s",
                    publish_data.get("error")
                )

            # Wait for publishing to complete (max 1 second)
            logger.debug("Waiting for publishing to complete")
            await asyncio.sleep(1)

            # Step 4: Check the publishing result
            logger.debug("Checking publishing result")
            check_js = """() => {
                const successMsg = document.body.textContent.includes(
                    '发布成功'
                );
                return {
                    success: successMsg,
                    message: successMsg
                        ? 'Published successfully'
                        : 'Publishing status unknown'
                };
            }"""

            check_result = await client.call_tool(
                "evaluate_script",
                {"function": check_js}
            )

            # Extract actual data from CallToolResult object
            result_data = check_result.data if hasattr(check_result, 'data') else check_result

            if result_data is None:
                logger.warning("Check result returned None - publishing may have succeeded")
                return {
                    "success": True,
                    "message": "Publishing completed, but unable to verify result"
                }

            if result_data.get("success"):
                logger.info("Idea published successfully")
            else:
                logger.warning(
                    "Publishing result unclear: %s",
                    result_data.get("message")
                )

            return result_data

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
