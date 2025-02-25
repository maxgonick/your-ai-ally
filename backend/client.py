"""Test client for the AI Browser Agent API."""

import asyncio
import json
import base64
import os
from PIL import Image
import io
import requests
import websockets
import argparse

SERVER_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws"


async def listen_for_screenshots():
    """Connect to WebSocket and listen for screenshots."""
    try:
        async with websockets.connect(WS_URL) as websocket:
            print("Connected to WebSocket server")

            # Send a ping to keep the connection alive
            await websocket.send(json.dumps({"type": "ping"}))

            # Create screenshots directory if it doesn't exist
            os.makedirs("screenshots", exist_ok=True)

            counter = 0
            while True:
                try:
                    message = await websocket.recv()
                    data = json.loads(message)

                    if data["type"] == "screenshot":
                        # Save the screenshot
                        img_data = base64.b64decode(data["data"])
                        image = Image.open(io.BytesIO(img_data))
                        image.save(f"screenshots/screenshot_{counter:04d}.png")
                        print(f"Saved screenshot_{counter:04d}.png")
                        counter += 1

                    elif data["type"] == "message":
                        print(f"Message from server: {data['data']}")

                    # Send periodic pings to keep the connection alive
                    await websocket.send(json.dumps({"type": "ping"}))

                except json.JSONDecodeError:
                    print("Received non-JSON message, ignoring")
                except Exception as e:
                    print(f"Error processing message: {e}")

    except Exception as e:
        print(f"WebSocket connection error: {e}")


def start_browser():
    """Start the browser."""
    response = requests.post(f"{SERVER_URL}/browser/start")
    print(response.json())


def stop_browser():
    """Stop the browser."""
    response = requests.post(f"{SERVER_URL}/browser/stop")
    print(response.json())


def navigate(url):
    """Navigate to a URL."""
    response = requests.post(f"{SERVER_URL}/browser/navigate", json={"url": url})
    print(response.json())


def run_agent(prompt):
    """Run the agent with a prompt."""
    response = requests.post(f"{SERVER_URL}/agent/run", json={"prompt": prompt})
    print(response.json())


async def main():
    parser = argparse.ArgumentParser(description="Test client for AI Browser Agent")
    parser.add_argument(
        "--action",
        choices=["start", "stop", "navigate", "agent", "stream"],
        required=True,
        help="Action to perform",
    )
    parser.add_argument("--url", help="URL to navigate to")
    parser.add_argument("--prompt", help="Prompt to send to the agent")

    args = parser.parse_args()

    if args.action == "start":
        start_browser()
    elif args.action == "stop":
        stop_browser()
    elif args.action == "navigate":
        if not args.url:
            print("URL is required for navigate action")
            return
        navigate(args.url)
    elif args.action == "agent":
        if not args.prompt:
            print("Prompt is required for agent action")
            return
        run_agent(args.prompt)
    elif args.action == "stream":
        print("Streaming screenshots. Press Ctrl+C to stop.")
        await listen_for_screenshots()


if __name__ == "__main__":
    asyncio.run(main())
