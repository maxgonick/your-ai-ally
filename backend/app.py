"""FastAPI server for AI browser agent with streaming capabilities."""

import asyncio
import base64
import json
from typing import List, Optional
import uuid

import uvicorn
from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
    HTTPException,
    BackgroundTasks,
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from playwright_computer_use.async_api import PlaywrightToolbox
from playwright_computer_use.loop import sampling_loop
from anthropic import Anthropic
from enum import Enum

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="AI Browser Agent API")

# Configure CORS to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Anthropic client
anthropic_client = Anthropic()

# Default streaming frame rate
DEFAULT_FPS = 5


# Store active connections and browser instances
class ConnectionManager:
    def __init__(self, fps=5):
        self.active_connections: List[WebSocket] = []
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.tools: Optional[PlaywrightToolbox] = None
        self.is_streaming = False
        self.stream_task = None
        self.stream_fps = fps  # Frames per second for streaming

    def generate_interaction_id(self):
        """Generate a new unique interaction ID."""
        self.interaction_id = str(uuid.uuid4())
        return self.interaction_id

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_screenshot(self, base64_data: str):
        for connection in self.active_connections:
            try:
                await connection.send_json(
                    {"type": "screenshot", "data": base64_data, "url": self.page.url}
                )
            except Exception as e:
                print(f"Error sending to websocket: {e}")

    async def send_message(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_json({"type": "message", "data": message})
            except Exception as e:
                print(f"Error sending message to websocket: {e}")

    async def send_update(
        self, status: str, interaction_id: str, data: Optional[dict] = None
    ):
        for connection in self.active_connections:
            try:
                await connection.send_json(
                    {
                        "type": "update",
                        "status": status,
                        "interaction_id": interaction_id,
                        "data": data,
                    }
                )
            except Exception as e:
                print(f"Error sending message to websocket: {e}")

    async def setup_browser(self):
        """Initialize the Playwright browser if not already running."""
        if self.browser is None:
            playwright = await async_playwright().start()
            self.browser = await playwright.firefox.launch(headless=False)
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()
            await self.page.set_viewport_size({"width": 1024, "height": 768})
            self.tools = PlaywrightToolbox(self.page, use_cursor=True)
            await self.page.goto("https://www.svelte.dev")
            return True
        return False

    async def close_browser(self):
        """Close the browser if it's running."""
        if self.browser:
            await self.browser.close()
            self.browser = None
            self.context = None
            self.page = None
            self.tools = None
            return True
        return False

    async def start_streaming(self):
        """Start streaming screenshots from the browser."""
        if self.is_streaming or not self.page:
            return False

        self.is_streaming = True

        async def stream_loop():
            while self.is_streaming and self.page:
                try:
                    screenshot = await self.page.screenshot()
                    base64_data = base64.b64encode(screenshot).decode("utf-8")
                    await self.send_screenshot(base64_data)
                    await asyncio.sleep(
                        1.0 / self.stream_fps
                    )  # Stream at configured FPS
                except Exception as e:
                    print(f"Error in streaming: {e}")
                    self.is_streaming = False
                    break

        self.stream_task = asyncio.create_task(stream_loop())
        return True

    async def stop_streaming(self):
        """Stop the screenshot streaming."""
        if not self.is_streaming:
            return False

        self.is_streaming = False
        if self.stream_task:
            try:
                self.stream_task.cancel()
                await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                pass

        return True

    async def run_computer_use(self, prompt: str, interaction_id: str):
        """Run the Claude agent with the given prompt."""
        if not self.page or not self.tools:
            raise ValueError("Browser is not initialized")

        try:
            await self.send_message("Running agent with prompt: " + prompt)
            messages = await sampling_loop(
                model="claude-3-5-sonnet-20241022",
                anthropic_client=anthropic_client,
                messages=[{"role": "user", "content": prompt}],
                tools=self.tools,
                page=self.page,
                verbose=True,
                only_n_most_recent_images=5,
            )
            # Extract and send the final response from Claude
            for message in messages:
                if message["role"] == "assistant":
                    for content_block in message["content"]:
                        if content_block["type"] == "tool_use":
                            await self.send_update(
                                "step",
                                interaction_id,
                                {
                                    "type": "tool_use",
                                    "system": content_block["name"],
                                    "action": content_block["input"],
                                },
                            )

            if messages and len(messages) > 0:
                last_message = messages[-1]
                if last_message["role"] == "assistant" and "content" in last_message:
                    for content_block in last_message["content"]:
                        if content_block["type"] == "text":
                            await self.send_update(
                                "completed",
                                interaction_id,
                                {"message": content_block["text"]},
                            )
        except Exception as e:
            await self.send_message(f"Error running agent: {str(e)}")
            await self.send_update(
                "failed",
                interaction_id,
            )
            return {"status": "error", "message": str(e)}


manager = ConnectionManager(fps=DEFAULT_FPS)


# WebSocket endpoint for streaming browser output
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep the connection alive
            data = await websocket.receive_text()
            message = json.loads(data)
            # Process any client messages if needed
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


class CursorEventType(Enum):
    HOVER = 1
    CLICK = 2


# Request models
class BrowserControlRequest(BaseModel):
    url: Optional[str] = None


class AgentPromptRequest(BaseModel):
    prompt: str


class FpsControlRequest(BaseModel):
    fps: int


class CursorRequest(BaseModel):
    type: CursorEventType
    x_cord: float
    y_cord: float


# REST API endpoints
@app.get("/")
async def root():
    return {"message": "AI Browser Agent API"}


@app.post("/browser/start")
async def start_browser(background_tasks: BackgroundTasks):
    """Start the browser and navigate to Google."""
    try:
        is_new = await manager.setup_browser()
        if is_new:
            background_tasks.add_task(manager.start_streaming)
            return {"status": "success", "message": "Browser started and streaming"}
        return {"status": "info", "message": "Browser was already running"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/browser/stop")
async def stop_browser():
    """Stop the browser."""
    try:
        await manager.stop_streaming()
        is_closed = await manager.close_browser()
        if is_closed:
            return {"status": "success", "message": "Browser stopped"}
        return {"status": "info", "message": "Browser was not running"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/browser/navigate")
async def navigate(request: BrowserControlRequest):
    """Navigate to a URL."""
    if not manager.page:
        raise HTTPException(status_code=400, detail="Browser not started")

    if not request.url:
        raise HTTPException(status_code=400, detail="URL is required")

    try:
        await manager.page.goto(request.url)
        return {"status": "completed", "message": f"Navigated to {request.url}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/command/run")
async def run_agent(request: AgentPromptRequest, background_tasks: BackgroundTasks):
    """Run the agent with a specific prompt."""
    if not manager.page:
        raise HTTPException(status_code=400, detail="Browser not started")

    if not request.prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")

    # Run the agent in the background to avoid blocking the API

    interaction_id = manager.generate_interaction_id()
    background_tasks.add_task(manager.run_computer_use, request.prompt, interaction_id)

    return {
        "status": "started",
        "message": "Agent started",
        "interaction_id": interaction_id,
    }


@app.get("/streaming/start")
async def start_streaming():
    """Start streaming screenshots."""
    if not manager.page:
        raise HTTPException(status_code=400, detail="Browser not started")

    success = await manager.start_streaming()
    if success:
        return {"status": "success", "message": "Streaming started"}
    return {"status": "info", "message": "Streaming was already active"}


@app.get("/streaming/stop")
async def stop_streaming():
    """Stop streaming screenshots."""
    success = await manager.stop_streaming()
    if success:
        return {"status": "success", "message": "Streaming stopped"}
    return {"status": "info", "message": "Streaming was not active"}


@app.post("/streaming/set-fps")
async def set_fps(request: FpsControlRequest):
    """Set the frames per second for streaming."""
    if request.fps < 1:
        raise HTTPException(status_code=400, detail="FPS must be at least 1")
    if request.fps > 30:
        raise HTTPException(status_code=400, detail="FPS cannot exceed 30")

    manager.stream_fps = request.fps

    # If streaming is active, restart it to apply new FPS
    if manager.is_streaming:
        await manager.stop_streaming()
        await manager.start_streaming()

    return {"status": "success", "message": f"Stream FPS set to {request.fps}"}


@app.post("/browser/cursorEvent")
async def get_click(request: CursorRequest):
    print("TEST")
    if request.type == CursorEventType.HOVER:
        pass
    elif request.type == CursorEventType.CLICK:
        await manager.page.click(
            position={"x": request.x_cord, "y": request.y_cord},
            selector="html",
        )
    else:
        pass
    return {"status": "success", "message": "Success"}


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
