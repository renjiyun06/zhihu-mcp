"""Zhihu MCP Server - Main entry point"""

import logging
import sys
from fastmcp import FastMCP
from .zhihu_client import ZhihuClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set root level to INFO
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Set DEBUG level only for our modules
logging.getLogger("zhihu_mcp").setLevel(logging.DEBUG)

# Reduce noise from other libraries
logging.getLogger("fakeredis").setLevel(logging.WARNING)
logging.getLogger("docket").setLevel(logging.WARNING)
logging.getLogger("mcp").setLevel(logging.INFO)
logging.getLogger("asyncio").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Create FastMCP server instance
mcp = FastMCP("zhihu-mcp")

# Create Zhihu client instance
zhihu_client = ZhihuClient()


@mcp.tool()
async def publish_idea(title: str = "", content: str = "") -> dict:
    """
    Publish a Zhihu idea

    Args:
        title: Idea title (optional, max 50 chars)
        content: Idea content

    Returns:
        Publishing result with success status and message
    """
    logger.info("Received publish_idea request")
    logger.debug(
        "Parameters - title: %s, content_length: %d",
        title,
        len(content)
    )

    if not content:
        logger.warning("Publishing failed: content is empty")
        return {
            "success": False,
            "error": "Content cannot be empty"
        }

    try:
        result = await zhihu_client.publish_idea(title, content)
        logger.info("publish_idea completed with result: %s", result)
        return result
    except Exception as e:
        logger.error("Error during publishing: %s", str(e), exc_info=True)
        return {
            "success": False,
            "error": f"Publishing error: {str(e)}"
        }


@mcp.tool()
async def publish_article(title: str, content: str) -> dict:
    """
    Publish a Zhihu article

    Args:
        title: Article title
        content: Article content (supports Markdown)

    Returns:
        Publishing result with success status, message, and article URL
    """
    logger.info("Received publish_article request")
    logger.debug(
        "Parameters - title: %s, content_length: %d",
        title,
        len(content)
    )

    if not title:
        logger.warning("Publishing failed: title is empty")
        return {
            "success": False,
            "error": "Title cannot be empty"
        }

    if not content:
        logger.warning("Publishing failed: content is empty")
        return {
            "success": False,
            "error": "Content cannot be empty"
        }

    try:
        result = await zhihu_client.publish_article(title, content)
        logger.info("publish_article completed with result: %s", result)
        return result
    except Exception as e:
        logger.error("Error during publishing: %s", str(e), exc_info=True)
        return {
            "success": False,
            "error": f"Publishing error: {str(e)}"
        }


def main():
    """Start the MCP server"""
    logger.info("Starting Zhihu MCP server")

    # Default to HTTP transport for easy testing
    # Can override via command line: --transport stdio or --transport sse
    transport = "sse"  # sse = HTTP (Server-Sent Events)
    port = 8001  # Default port

    if "--transport" in sys.argv:
        idx = sys.argv.index("--transport")
        if idx + 1 < len(sys.argv):
            transport = sys.argv[idx + 1]

    if "--port" in sys.argv:
        idx = sys.argv.index("--port")
        if idx + 1 < len(sys.argv):
            try:
                port = int(sys.argv[idx + 1])
            except ValueError:
                logger.error("Invalid port number, using default 8001")

    logger.info("Using transport: %s", transport)
    logger.info("Using port: %d", port)

    # Run the server
    mcp.run(transport=transport, port=port)


if __name__ == "__main__":
    main()
