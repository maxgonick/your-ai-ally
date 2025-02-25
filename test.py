"""Accessibility audit tool using Playwright and Lighthouse."""

import asyncio
import json
import os
import subprocess
from pathlib import Path
import tempfile
import time
from datetime import datetime

import typer
from termcolor import colored
import pyfiglet
from playwright.async_api import async_playwright, Playwright
from playwright_claude_lib.src.playwright_computer_use.async_api import (
    PlaywrightToolbox,
)
from anthropic import Anthropic
from dotenv import load_dotenv

# Constants
DEFAULT_CATEGORIES = ["accessibility"]
OUTPUT_DIR = Path("./lighthouse_reports")

# Initialize app
app = typer.Typer()
load_dotenv()

# Create output directory if it doesn't exist
OUTPUT_DIR.mkdir(exist_ok=True)


async def run_lighthouse(page, url, categories=None, output_format="html"):
    """
    Run Lighthouse audit on the provided URL using Playwright browser.

    Args:
        page: Playwright page object
        url: URL to audit
        categories: List of Lighthouse categories to audit (default: accessibility)
        output_format: Format of the output report (html or json)

    Returns:
        Path to the generated report file
    """
    # Navigate to the URL
    await page.goto(url)

    # Get the browser's websocket endpoint (required for Lighthouse)
    browser = page.context.browser
    # browser_ws_endpoint = browser.ws_endpoint

    # Prepare temp file for the Lighthouse report
    temp_dir = tempfile.mkdtemp()
    timestamp = int(time.time())
    sanitized_url = url.replace("://", "_").replace("/", "_").replace(".", "_")
    report_path = (
        Path(temp_dir) / f"lighthouse_{sanitized_url}_{timestamp}.{output_format}"
    )

    # Prepare Lighthouse command
    categories = categories or DEFAULT_CATEGORIES
    categories_arg = f"--only-categories={','.join(categories)}"
    output_arg = f"--output={output_format}"
    output_path_arg = f"--output-path={report_path}"

    # Run Lighthouse using Node.js
    cmd = [
        "npx",
        "lighthouse",
        url,
        # categories_arg,
        "--chrome-flags=--headless",
        # f"--port={browser_ws_endpoint.split(':')[-1]}",
        output_arg,
        output_path_arg,
    ]

    try:
        process = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("TEST")
        # Copy the report to the output directory
        final_path = OUTPUT_DIR / report_path.name
        with open(report_path, "rb") as src, open(final_path, "wb") as dst:
            dst.write(src.read())

        print(f"\n{colored('✓ Lighthouse audit completed successfully', 'green')}")
        print(f"Report saved to: {colored(final_path, 'cyan')}")

        # Parse and return the accessibility score if JSON output
        if output_format == "json":
            with open(report_path, "r") as f:
                report_data = json.load(f)
                accessibility_score = (
                    report_data["categories"]["accessibility"]["score"] * 100
                )
                return final_path, accessibility_score

        return final_path, None

    except subprocess.CalledProcessError as e:
        print(f"{colored('✗ Error running Lighthouse:', 'red')} {e.stderr}")
        return None, None


async def analyze_accessibility_issues(page, url):
    """Run an accessibility audit and analyze the results with Claude."""

    print(f"\n{colored('Running accessibility audit...', 'yellow')}")

    # Run Lighthouse to get accessibility report
    report_path, score = await run_lighthouse(page, url, output_format="json")

    if not report_path:
        print(f"{colored('✗ Failed to generate accessibility report', 'red')}")
        return

    # Load report data
    with open(report_path, "r") as f:
        report_data = json.load(f)

    # Extract accessibility audit results
    accessibility_audits = report_data["categories"]["accessibility"]["auditRefs"]
    accessibility_results = {}
    for audit in accessibility_audits:
        audit_id = audit["id"]
        if audit_id in report_data["audits"]:
            accessibility_results[audit_id] = report_data["audits"][audit_id]

    # Filter to only failed audits
    failed_audits = {
        id: data
        for id, data in accessibility_results.items()
        if data["score"] is not None and data["score"] < 1
    }

    # Print summary
    print(f"\n{colored('=== Accessibility Audit Results ===', 'cyan')}")
    print(f"URL: {url}")
    print(f"Overall Accessibility Score: {colored(f'{score:.1f}%', 'yellow')}")
    print(f"Total Issues: {colored(len(failed_audits), 'yellow')}")

    # Print details of failed audits
    if failed_audits:
        print(f"\n{colored('=== Failed Accessibility Audits ===', 'red')}")
        for audit_id, data in failed_audits.items():
            print(f"\n{colored(data['title'], 'yellow')}")
            print(
                f"Impact: {colored(data.get('details', {}).get('impact', 'Unknown'), 'red')}"
            )
            print(f"Description: {data['description']}")

            # Print elements with issues if available
            if (
                "details" in data
                and "items" in data["details"]
                and data["details"]["items"]
            ):
                print("Affected Elements:")
                for item in data["details"]["items"][:3]:  # Limit to first 3 items
                    if "node" in item:
                        print(f"  - {item['node'].get('snippet', 'Unknown element')}")

    # Also generate an HTML report for detailed review
    html_report_path, _ = await run_lighthouse(page, url, output_format="html")
    if html_report_path:
        print(
            f"\n{colored('Detailed HTML report available at:', 'green')} {html_report_path}"
        )

    return report_path


async def run(playwright: Playwright, url: str):
    """Setup browser and run the accessibility audit."""
    print(f"{colored('Launching browser...', 'blue')}")

    # Launch browser
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context()
    page = await context.new_page()
    await page.set_viewport_size({"width": 1280, "height": 800})

    # Run accessibility audit
    await analyze_accessibility_issues(page, url)

    # Clean up
    await browser.close()


@app.command()
def audit(url: str = typer.Argument(..., help="URL to audit for accessibility")):
    """Run an accessibility audit on the specified URL."""
    # Display banner
    banner = pyfiglet.figlet_format("A11y Audit", font="slant")
    print(colored(banner, "light_magenta"))

    print(colored(f"Auditing {url} for accessibility issues...", "light_cyan"))

    # Run the audit
    asyncio.run(main(url))


async def main(url: str):
    """Main entry point for the application."""
    async with async_playwright() as playwright:
        await run(playwright, url)


if __name__ == "__main__":
    app()
