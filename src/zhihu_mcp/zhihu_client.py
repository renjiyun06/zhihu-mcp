"""Zhihu client - Browser automation via chrome-devtools MCP"""

import asyncio
import json
import logging
import re
from typing import Any, Dict, List
from fastmcp import Client
from fastmcp.client import NpxStdioTransport

logger = logging.getLogger(__name__)


class ZhihuClient:
    """Zhihu client that encapsulates idea and article publishing"""

    def __init__(
        self,
        chrome_package: str = "chrome-devtools-mcp@latest",
        chrome_args: List[str] = None
    ):
        """
        Initialize Zhihu client

        Args:
            chrome_package: NPM package name for chrome-devtools MCP
            chrome_args: Arguments for the chrome-devtools MCP server
        """
        if chrome_args is None:
            chrome_args = [
                "--browser-url=http://192.168.2.6:19222"
            ]

        self.chrome_package = chrome_package
        self.chrome_args = chrome_args

        logger.info(
            "ZhihuClient initialized with package: %s, args: %s",
            chrome_package,
            chrome_args
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

            # Step 1: Navigate to article write page
            logger.debug("Navigating to article write page")
            await client.call_tool(
                "navigate_page",
                {
                    "type": "url",
                    "url": "https://zhuanlan.zhihu.com/write"
                }
            )
            logger.debug("Navigation completed")

            # Wait for page to load
            logger.debug("Waiting for page to load")
            await asyncio.sleep(3)

            # Step 2: Fill title
            # Take snapshot just before filling
            logger.debug("Taking snapshot to locate title input")
            snapshot1 = await client.call_tool("take_snapshot", {})
            snapshot1_text = str(snapshot1)

            # Find first textbox (title)
            textbox_pattern = r'uid=(\d+_\d+)\s+textbox.*?multiline'
            matches1 = list(re.finditer(textbox_pattern, snapshot1_text))

            if len(matches1) < 1:
                logger.error("Failed to locate title input")
                return {
                    "success": False,
                    "message": "Failed to locate title input field"
                }

            title_uid = matches1[0].group(1)
            logger.debug("Found title uid: %s", title_uid)

            # Fill title immediately
            logger.debug("Filling title")
            await client.call_tool(
                "fill",
                {
                    "uid": title_uid,
                    "value": title
                }
            )
            logger.debug("Title filled successfully")

            # Wait for UI to update
            await asyncio.sleep(1)

            # Step 3: Fill content
            # Take fresh snapshot just before filling content
            logger.debug("Taking fresh snapshot to locate content input")
            snapshot2 = await client.call_tool("take_snapshot", {})
            snapshot2_text = str(snapshot2)

            # Find textbox with description="请输入正文"
            matches2 = list(re.finditer(textbox_pattern, snapshot2_text))

            content_uid = None
            for i, match in enumerate(matches2):
                uid = match.group(1)
                # Extract just this element's declaration (until next uid= or newline + non-space)
                line_start = match.start()
                # Find the end: either next "uid=" or a newline followed by non-indented content
                next_uid_pos = snapshot2_text.find('uid=', line_start + 10)
                line_end = snapshot2_text.find('\n  uid=', line_start)  # Next sibling element

                if line_end == -1 or (next_uid_pos != -1 and next_uid_pos < line_end):
                    line_end = next_uid_pos if next_uid_pos != -1 else line_start + 300

                element_text = snapshot2_text[line_start:line_end]

                has_desc = 'description="请输入正文"' in element_text
                logger.debug("Textbox %d: uid=%s, has_desc=%s", i, uid, has_desc)
                logger.debug("  Element: %s", element_text[:120])

                if has_desc:
                    content_uid = uid
                    logger.debug("✓ Found content uid: %s", content_uid)
                    break

            # Fallback: if not found by description, use second textbox
            if not content_uid and len(matches2) >= 2:
                content_uid = matches2[1].group(1)
                logger.debug("Using second textbox as content uid: %s", content_uid)

            if not content_uid:
                logger.error("Failed to locate content input")
                return {
                    "success": False,
                    "message": "Failed to locate content input field"
                }

            # Fill content immediately
            logger.debug("Filling content")
            await client.call_tool(
                "fill",
                {
                    "uid": content_uid,
                    "value": content
                }
            )
            logger.debug("Content filled successfully")

            # Wait for auto-save to complete
            logger.debug("Waiting for auto-save to complete")
            await asyncio.sleep(3)

            # Step 5: Click publish button using evaluate_script
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

            # Wait for publishing to complete
            logger.debug("Waiting for publishing to complete")
            await asyncio.sleep(5)

            # Step 6: Check the publishing result
            logger.debug("Checking publishing result")
            check_js = """() => {
                const hasSuccessMsg = document.body.textContent.includes(
                    '发布成功'
                );
                const currentUrl = window.location.href;
                const isArticlePage = currentUrl.includes('/p/') &&
                                     !currentUrl.includes('/edit');

                return {
                    success: hasSuccessMsg || isArticlePage,
                    message: hasSuccessMsg
                        ? 'Published successfully'
                        : (isArticlePage
                            ? 'Redirected to article page'
                            : 'Publishing status unknown'),
                    url: currentUrl
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
                logger.info("Article published successfully")
                logger.info("Article URL: %s", result_data.get("url"))
            else:
                logger.warning(
                    "Publishing result unclear: %s",
                    result_data.get("message")
                )

            return result_data
