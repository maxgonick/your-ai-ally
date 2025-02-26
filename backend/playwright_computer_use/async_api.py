"""This module contains the PlaywrightToolbox class to be used with an Async Playwright Page."""

import importlib.resources
import base64
from typing import Literal, TypedDict
from playwright.async_api import Page
from PIL import Image
import io
from anthropic.types.beta import (
    BetaToolComputerUse20241022Param,
    BetaToolParam,
    BetaToolResultBlockParam,
    BetaTextBlockParam,
    BetaImageBlockParam,
)
from dataclasses import dataclass

TYPING_GROUP_SIZE = 50

Action = Literal[
    "key",
    "type",
    "mouse_move",
    "left_click",
    "left_click_drag",
    "right_click",
    "middle_click",
    "double_click",
    "screenshot",
    "cursor_position",
]


class ComputerToolOptions(TypedDict):
    """Options for the computer tool."""

    display_height_px: int
    display_width_px: int
    display_number: int | None


def chunks(s: str, chunk_size: int) -> list[str]:
    """Split a string into chunks of a specific size."""
    return [s[i : i + chunk_size] for i in range(0, len(s), chunk_size)]


@dataclass(kw_only=True, frozen=True)
class ToolResult:
    """Represents the result of a tool execution."""

    output: str | None = None
    error: str | None = None
    base64_image: str | None = None


class ToolError(Exception):
    """Raised when a tool encounters an error."""

    def __init__(self, message):
        """Create a new ToolError."""
        self.message = message


class PlaywrightToolbox:
    """Toolbox for interaction between Claude and Async Playwright Page."""

    def __init__(
        self,
        page: Page,
        use_cursor: bool = True,
        screenshot_wait_until: (
            Literal["load", "domcontentloaded", "networkidle"] | None
        ) = None,
    ):
        """Create a new PlaywrightToolbox.

        Args:
            page: The Async Playwright page to interact with.
            use_cursor: Whether to display the cursor in the screenshots or not.
            screenshot_wait_until: Optional, wait until the page is in a specific state before taking a screenshot. Default does not wait

        """
        self.page = page
        self.tools: list[
            PlaywrightComputerTool | PlaywrightSetURLTool | PlaywrightBackTool
        ] = [
            PlaywrightComputerTool(
                page, use_cursor=use_cursor, screenshot_wait_until=screenshot_wait_until
            ),
            PlaywrightSetURLTool(page),
            PlaywrightBackTool(page),
        ]

    def to_params(self) -> list[BetaToolParam]:
        """Expose the params of all the tools in the toolbox."""
        return [tool.to_params() for tool in self.tools]

    async def run_tool(
        self, name: str, input: dict, tool_use_id: str
    ) -> BetaToolResultBlockParam:
        """Pick the right tool using `name` and run it."""
        try:
            if name not in [tool.name for tool in self.tools]:
                error_msg = f"Unknown tool '{name}'. Please try a valid tool: computer, set_url, or previous_page."
                return _make_api_tool_result(
                    tool_use_id=tool_use_id, result=ToolResult(error=error_msg)
                )

            tool = next(tool for tool in self.tools if tool.name == name)
            result = await tool(**input)
            return _make_api_tool_result(tool_use_id=tool_use_id, result=result)

        except Exception as e:
            error_msg = f"Error executing tool '{name}': {str(e)}. Please try again with correct parameters."
            return _make_api_tool_result(
                tool_use_id=tool_use_id, result=ToolResult(error=error_msg)
            )


class PlaywrightSetURLTool:
    """Tool to navigate to a specific URL."""

    name: Literal["set_url"] = "set_url"

    def __init__(self, page: Page):
        """Create a new PlaywrightSetURLTool.

        Args:
            page: The Async Playwright page to interact with.
        """
        super().__init__()
        self.page = page

    def to_params(self) -> BetaToolParam:
        """Params describing the tool. Description used by Claude to understand how to this use tool."""
        return BetaToolParam(
            name=self.name,
            description="This tool allows to go directly to a specified URL.",
            input_schema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL of the web page to navigate to.",
                    }
                },
                "required": ["url"],
            },
        )

    async def __call__(self, *, url: str):
        """Trigger goto the chosen url."""
        try:
            await self.page.goto(url)
            return ToolResult()
        except Exception as e:
            error_msg = f"Failed to navigate to URL: {str(e)}. Please check the URL format and try again."
            return ToolResult(error=error_msg)


class PlaywrightBackTool:
    """Tool to navigate to the previous page."""

    name: Literal["previous_page"] = "previous_page"

    def __init__(self, page: Page):
        """Create a new PlaywrightBackTool.

        Args:
            page: The Async Playwright page to interact with.
        """
        super().__init__()
        self.page = page

    def to_params(self) -> BetaToolParam:
        """Params describing the tool. Description used by Claude to understand how to this use tool."""
        return BetaToolParam(
            name=self.name,
            description="This tool navigate to the previous page.",
            input_schema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        )

    async def __call__(self):
        """Trigger the back button in the browser."""
        try:
            await self.page.go_back()
            return ToolResult()
        except Exception as e:
            error_msg = f"Failed to navigate to previous page: {str(e)}. This may happen if there's no previous page in the browser history."
            return ToolResult(error=error_msg)


class PlaywrightComputerTool:
    """A tool that allows the agent to interact with Async Playwright Page."""

    name: Literal["computer"] = "computer"
    api_type: Literal["computer_20250124"] = "computer_20250124"

    @property
    def width(self) -> int:
        """The width of the Playwright page in pixels."""
        return self.page.viewport_size["width"]

    @property
    def height(self) -> int:
        """The height of the Playwright page in pixels."""
        return self.page.viewport_size["height"]

    @property
    def options(self) -> ComputerToolOptions:
        """The options of the tool."""
        return {
            "display_width_px": self.width,
            "display_height_px": self.height,
            "display_number": 1,  # hardcoded
        }

    def to_params(self) -> BetaToolComputerUse20241022Param:
        """Params describing the tool. Used by Claude to understand this is a computer use tool."""
        return {"name": self.name, "type": self.api_type, **self.options}

    def __init__(
        self,
        page: Page,
        use_cursor: bool = True,
        screenshot_wait_until: (
            Literal["load", "domcontentloaded", "networkidle"] | None
        ) = None,
    ):
        """Initializes the PlaywrightComputerTool.

        Args:
            page: The Async Playwright page to interact with.
            use_cursor: Whether to display the cursor in the screenshots or not.
            screenshot_wait_until: Optional, wait until the page is in a specific state before taking a screenshot. Default does not wait
        """
        super().__init__()
        self.page = page
        self.use_cursor = use_cursor
        self.mouse_position: tuple[int, int] = (0, 0)
        self.screenshot_wait_until = screenshot_wait_until
        self.valid_actions = {
            "mouse_move",
            "left_click",
            "right_click",
            "middle_click",
            "double_click",
            "left_click_drag",
            "key",
            "type",
            "screenshot",
            "cursor_position",
        }

    async def __call__(
        self,
        *,
        action: Action,
        text: str | None = None,
        coordinate: list[int] | tuple[int, int] | None = None,
        **kwargs,
    ):
        """Run an action. text and coordinate are potential additional parameters."""
        try:
            # First validate the action
            if action not in self.valid_actions:
                valid_actions_str = ", ".join(sorted(list(self.valid_actions)))
                raise ToolError(
                    f"Invalid action: '{action}'. Valid actions are: {valid_actions_str}"
                )

            if action in (
                "mouse_move",
                "left_click",
                "right_click",
                "middle_click",
                "double_click",
                "left_click_drag",
            ):
                # Check if coordinate is required but not provided
                if action in ("mouse_move", "left_click_drag") and coordinate is None:
                    raise ToolError(
                        f"Coordinate is required for '{action}'. Please provide x,y coordinates."
                    )

                # Handle coordinate parameter which may come in different formats
                if coordinate is not None:
                    # Ensure coordinate is a valid format (list or tuple of 2 integers)
                    if isinstance(coordinate, (list, tuple)):
                        if len(coordinate) != 2:
                            raise ToolError(
                                f"Coordinate must have exactly 2 elements (x,y), got {len(coordinate)}."
                            )
                        if not all(
                            isinstance(i, (int, float)) and i >= 0 for i in coordinate
                        ):
                            raise ToolError(
                                f"Coordinate elements must be non-negative numbers. Got: {coordinate}"
                            )

                        # Convert to integers if they're floats
                        x, y = int(coordinate[0]), int(coordinate[1])

                        # Check if coordinates are within viewport bounds
                        if x > self.width or y > self.height:
                            raise ToolError(
                                f"Coordinate ({x},{y}) is outside viewport bounds ({self.width}x{self.height}). Please use coordinates within the visible area."
                            )
                    else:
                        raise ToolError(
                            f"Coordinate must be a list or tuple of [x,y], got {type(coordinate).__name__}."
                        )

                    if text is not None and action in ("mouse_move", "left_click_drag"):
                        raise ToolError(
                            f"Text parameter is not accepted for '{action}' action."
                        )

                    if action == "mouse_move":
                        await self.page.mouse.move(x, y)
                        self.mouse_position = (x, y)
                        return ToolResult(
                            output=f"Moved cursor to ({x},{y})",
                            error=None,
                            base64_image=None,
                        )
                    elif action == "left_click_drag":
                        raise ToolError(
                            "The left_click_drag action is not implemented yet. Please use mouse_move followed by left_click instead."
                        )
                    elif action in (
                        "left_click",
                        "right_click",
                        "middle_click",
                        "double_click",
                    ):
                        click_arg = {
                            "left_click": {"button": "left", "click_count": 1},
                            "right_click": {"button": "right", "click_count": 1},
                            "middle_click": {"button": "middle", "click_count": 1},
                            "double_click": {
                                "button": "left",
                                "click_count": 2,
                                "delay": 100,
                            },
                        }[action]

                        # Move to the coordinate first, then click
                        await self.page.mouse.move(x, y)
                        self.mouse_position = (x, y)
                        await self.page.mouse.click(x, y, **click_arg)
                        return await self.screenshot()

            if action in ("key", "type"):
                if text is None:
                    raise ToolError(
                        f"Text parameter is required for '{action}' action. Please provide the text to type or key to press."
                    )
                if coordinate is not None:
                    raise ToolError(
                        f"Coordinate parameter is not accepted for '{action}' action."
                    )
                if not isinstance(text, str):
                    raise ToolError(
                        f"Text must be a string, got {type(text).__name__}."
                    )

                if action == "key":
                    # handle shifts with macOS-specific mappings if needed
                    await self.press_key(text)
                    return ToolResult(output=f"Pressed key: {text}")
                elif action == "type":
                    for chunk in chunks(text, TYPING_GROUP_SIZE):
                        await self.page.keyboard.type(chunk)
                    return await self.screenshot()

            if action in ("screenshot", "cursor_position"):
                if text is not None:
                    raise ToolError(
                        f"Text parameter is not accepted for '{action}' action."
                    )

                if action == "screenshot":
                    return await self.screenshot()
                elif action == "cursor_position":
                    return ToolResult(
                        output=f"Cursor position: X={self.mouse_position[0]}, Y={self.mouse_position[1]}"
                    )

            # This shouldn't be reached with the validation above, but keeping as a fallback
            raise ToolError(f"Invalid action: {action}")

        except ToolError as e:
            # Format error message for Claude to understand what went wrong
            error_msg = e.message
            suggestion = "Please try again with a valid command."
            return ToolResult(error=f"{error_msg} {suggestion}")

        except Exception as e:
            # Catch any other exceptions and provide useful feedback
            return ToolResult(
                error=f"Unexpected error during '{action}' action: {str(e)}. Please try again."
            )

    async def screenshot(self) -> ToolResult:
        """Take a screenshot of the current screen and return the base64 encoded image."""
        try:
            if self.screenshot_wait_until is not None:
                await self.page.wait_for_load_state(self.screenshot_wait_until)
            await self.page.wait_for_load_state()
            screenshot = await self.page.screenshot()
            image = Image.open(io.BytesIO(screenshot))
            img_small = image.resize((self.width, self.height), Image.LANCZOS)
            if self.use_cursor:
                cursor = load_cursor_image()
                img_small.paste(cursor, self.mouse_position, cursor)
            buffered = io.BytesIO()
            img_small.save(buffered, format="PNG")
            base64_image = base64.b64encode(buffered.getvalue()).decode()
            return ToolResult(base64_image=base64_image)
        except Exception as e:
            return ToolResult(error=f"Failed to take screenshot: {str(e)}")

    async def press_key(self, key: str):
        """Press a key on the keyboard. Handle + shifts. Eg: Ctrl+Shift+T."""
        valid_keys = (
            ["F{i}" for i in range(1, 13)]
            + ["Digit{i}" for i in range(10)]
            + ["Key{i}" for i in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"]
            + [i for i in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"]
            + [i.lower() for i in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"]
            + [
                "Backquote",
                "Minus",
                "Equal",
                "Backslash",
                "Backspace",
                "Tab",
                "Delete",
                "Escape",
                "ArrowDown",
                "End",
                "Enter",
                "Home",
                "Insert",
                "PageDown",
                "PageUp",
                "ArrowRight",
                "ArrowUp",
                "ArrowLeft",
                "Space",
                "Meta",
                "Alt",
                "Control",
                "Shift",
            ]
        )

        shifts = []
        if "+" in key:
            parts = key.split("+")
            shifts = parts[:-1]
            key = parts[-1]

            # Validate modifier keys
            for modifier in shifts:
                mapped_modifier = _map_key_name(modifier)
                if mapped_modifier not in ["Control", "Meta", "Alt", "Shift"]:
                    raise ToolError(
                        f"Invalid modifier key: '{modifier}'. Valid modifiers are: Ctrl, Meta, Alt, Shift"
                    )

        # Map key to Playwright format and validate
        mapped_key = to_playwright_key(key)

        try:
            # Press down all modifier keys
            for shift in shifts:
                mapped_shift = _map_key_name(shift)
                await self.page.keyboard.down(mapped_shift)

            # Press the main key
            await self.page.keyboard.press(mapped_key)

            # Release all modifier keys in reverse order
            for shift in reversed(shifts):
                mapped_shift = _map_key_name(shift)
                await self.page.keyboard.up(mapped_shift)

        except Exception as e:
            # Make sure to release any pressed keys to avoid keyboard getting stuck
            for shift in shifts:
                try:
                    mapped_shift = _map_key_name(shift)
                    await self.page.keyboard.up(mapped_shift)
                except:
                    pass
            raise ToolError(f"Error pressing key '{key}': {str(e)}")


def _map_key_name(key: str) -> str:
    """Map common key names to Playwright key format."""
    key_map = {
        "ctrl": "Control",
        "control": "Control",
        "cmd": "Meta",
        "command": "Meta",
        "alt": "Alt",
        "option": "Alt",
        "shift": "Shift",
        "enter": "Enter",
        "return": "Enter",
        "esc": "Escape",
        "escape": "Escape",
        "space": "Space",
        "spacebar": "Space",
    }
    return key_map.get(key.lower(), key)


def to_playwright_key(key: str) -> str:
    """Convert a key to the Playwright key format."""
    key_map = {
        "Return": "Enter",
        "Page_Down": "PageDown",
        "Page_Up": "PageUp",
        "Left": "ArrowLeft",
        "Right": "ArrowRight",
        "Up": "ArrowUp",
        "Down": "ArrowDown",
        "BackSpace": "Backspace",
        "Delete": "Delete",
        "Del": "Delete",
        "Esc": "Escape",
        "Space": " ",
        "Spacebar": " ",
        "Tab": "Tab",
        "alt": "Alt",
    }

    if key in key_map:
        return key_map[key]

    # Check if valid key as is
    valid_keys = (
        ["F{i}" for i in range(1, 13)]
        + ["Digit{i}" for i in range(10)]
        + ["Key{i}" for i in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"]
        + [i for i in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"]
        + [i.lower() for i in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"]
        + [
            "Backquote",
            "Minus",
            "Equal",
            "Backslash",
            "Backspace",
            "Tab",
            "Delete",
            "Escape",
            "ArrowDown",
            "End",
            "Enter",
            "Home",
            "Insert",
            "PageDown",
            "PageUp",
            "ArrowRight",
            "ArrowUp",
            "ArrowLeft",
        ]
    )

    if key in valid_keys:
        return key

    # Handle single character keys
    if len(key) == 1:
        return key

    # If we get here, the key is not recognized
    raise ToolError(f"Unrecognized key: '{key}'. Please use a standard key name.")


def load_cursor_image():
    """Access the cursor.png file in the assets directory."""
    with importlib.resources.open_binary(
        "playwright_computer_use.assets", "cursor.png"
    ) as img_file:
        image = Image.open(img_file)
        image.load()  # Ensure the image is fully loaded into memory
    return image


def _make_api_tool_result(
    result: ToolResult, tool_use_id: str
) -> BetaToolResultBlockParam:
    """Convert an agent ToolResult to an API ToolResultBlockParam."""
    if result.error:
        return BetaToolResultBlockParam(
            tool_use_id=tool_use_id,
            is_error=True,
            content=result.error,
            type="tool_result",
        )
    else:
        tool_result_content: list[BetaTextBlockParam | BetaImageBlockParam] = []
        if result.output:
            tool_result_content.append(
                BetaTextBlockParam(
                    type="text",
                    text=result.output,
                )
            )
        if result.base64_image:
            tool_result_content.append(
                BetaImageBlockParam(
                    type="image",
                    source={
                        "type": "base64",
                        "media_type": "image/png",
                        "data": result.base64_image,
                    },
                )
            )
        return BetaToolResultBlockParam(
            tool_use_id=tool_use_id,
            is_error=False,
            content=tool_result_content,
            type="tool_result",
        )
