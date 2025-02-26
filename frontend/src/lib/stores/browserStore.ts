import { writable } from 'svelte/store';
import { toast } from "svelte-sonner";

// Browser connection info
export const connected = writable(false);
export const messages = writable<string[]>([]);
export const browserScreenshot = writable<string>('');
export const isLoading = writable(false);

// Browser state
export const browserStatus = writable<'idle' | 'starting' | 'running' | 'stopping'>('idle');

// User inputs
export const urlInput = writable('https://www.example.com');
export const promptInput = writable('Tell me what\'s on this page');
export const fpsValue = writable(5);

// Socket handlers
let socket: WebSocket | null = null;
let pingInterval: number | null = null;

export function addMessage(from: "System" | "Agent" | "User", message: string, error: boolean = false) {
    if (from === "System") {
        if (error) {
            toast.error(message);
        } else {
            toast.success(message);
        }
    }
    messages.update(msgs => [...msgs, message]);
}

export function connectWebSocket() {
    if (socket?.readyState === WebSocket.OPEN) return;

    const socketUrl = 'ws://localhost:8000/ws';
    socket = new WebSocket(socketUrl);

    socket.onopen = () => {
        connected.set(true);
        addMessage("System", 'Connected to server');

        // Send ping every 30s to keep connection alive
        pingInterval = window.setInterval(() => {
            if (socket?.readyState === WebSocket.OPEN) {
                socket.send(JSON.stringify({ type: 'ping' }));
            } else {
                if (pingInterval) clearInterval(pingInterval);
            }
        }, 30000);
    };

    socket.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);

            console.log('Received message:', data.type);

            if (data.type === 'screenshot') {
                browserScreenshot.set('data:image/png;base64,' + data.data);
                urlInput.set(data.url);
                isLoading.set(false);
            } else if (data.type === 'message') {
                addMessage('Agent', data.data);
            } else if (data.type === 'pong') {
                // Connection is alive
            }
        } catch (e) {
            console.error('Error parsing message:', e);
        }
    };

    socket.onclose = () => {
        connected.set(false);

        if (pingInterval) {
            clearInterval(pingInterval);
            pingInterval = null;
        }
    };

    socket.onerror = (error) => {
        console.error('WebSocket error:', error);
        addMessage('System', 'Connection error occurred', true);
    };
}

export function disconnectWebSocket() {
    if (socket) {
        socket.close();
        socket = null;
    }

    if (pingInterval) {
        clearInterval(pingInterval);
        pingInterval = null;
    }

    connected.set(false);
}

// API calls
const apiUrl = 'http://localhost:8000';

export async function startBrowser() {
    browserStatus.set('starting');
    isLoading.set(true);

    try {
        const response = await fetch(`${apiUrl}/browser/start`, {
            method: 'POST'
        });
        const data = await response.json();
        // addMessage('System: ' + data.message);
        addMessage('System', data.message);
        browserStatus.set('running');
    } catch (error) {
        addMessage('System', `Failed to start browser - ${error}`, true);
        browserStatus.set('idle');
        isLoading.set(false);
    }
}

export async function stopBrowser() {
    browserStatus.set('stopping');

    try {
        const response = await fetch(`${apiUrl}/browser/stop`, {
            method: 'POST'
        });
        const data = await response.json();
        addMessage('System', data.message);
        browserScreenshot.set('');
        browserStatus.set('idle');
    } catch (error) {
        // addMessage(`System Error: Failed to stop browser - ${error}`);
        addMessage('System', `Failed to stop browser - ${error}`, true);
        browserStatus.set('running');
    }
}

export async function navigateToUrl(url: string) {
    if (!url) {
        addMessage('System', 'Please enter a URL', true);
        return;
    }

    isLoading.set(true);

    try {
        const response = await fetch(`${apiUrl}/browser/navigate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url })
        });
        const data = await response.json();
        addMessage('System', data.message);

    } catch (error) {
        addMessage('System', `Failed to navigate - ${error}`, true);
        isLoading.set(false);
    }
}

export async function runAgent(prompt: string) {
    if (!prompt) {
        addMessage('System', 'Please enter a prompt', true);
        return;
    }

    addMessage('System', 'Running agent with prompt: ' + prompt);


    try {
        const response = await fetch(`${apiUrl}/agent/run`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ prompt })
        });
        const data = await response.json();
        addMessage('System', data.message);
    } catch (error) {
        addMessage('System', `Failed to run agent - ${error}`, true);
    }
}

export async function setFps(fps: number) {
    try {
        const response = await fetch(`${apiUrl}/streaming/set-fps`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ fps })
        });
        const data = await response.json();
        addMessage('System', `FPS set to ${fps}`);
    } catch (error) {
        addMessage('System', `Failed to set FPS - ${error}`, true);
    }
}