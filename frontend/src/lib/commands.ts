import ArrowRight from "lucide-svelte/icons/arrow-right";
import MessageSquare from "lucide-svelte/icons/message-square";
import Search from "lucide-svelte/icons/search";
import * as browserStore from '$lib/stores/browserStore';
import { toast } from "svelte-sonner";

// Function to validate a URL
function isValidUrl(url: string): boolean {
    const urlRegex =
        /^(https?:\/\/)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$/;
    return urlRegex.test(url);
}

async function navigateToURL(url: string) {
    let processedUrl = url.trim();
    const hasProtocol = /^[a-z][a-z0-9+.-]*:\/\//i.test(processedUrl);
    const defaultProtocol: string = 'https://'

    if (!hasProtocol) {
        processedUrl = defaultProtocol + processedUrl;
    }

    try {
        const urlObject = new URL(processedUrl);

        // Additional checks for valid URL
        // Must have a hostname with at least one dot (e.g., example.com)
        const hasValidHostname = urlObject.hostname.includes('.') &&
            urlObject.hostname.length > 3;

        if (hasValidHostname) {
            await browserStore.navigateToUrl(processedUrl);
            return {
                status: "completed",
                message: `Navigated to ${processedUrl}`,
            }
        }


    } catch (error) {

    }
    toast.error(`${processedUrl} is not a valid URL`)
    return {
        status: "failed",
        message: `${processedUrl} is not a valid URL`,
    }
}

async function runAgent(prompt: string) {
    try {
        const id = await browserStore.runAgent(prompt);
        if (id) {
            toast.success(`Agent started with ID: ${id}`);
            return {
                status: "started",
                message: id,
            }
        }
    } catch (error) {
        toast.error(`Failed to run agent - ${error}`)
        return {
            status: "failed",
            message: `Failed to run agent - ${error}`,
        }

    }
}


export const Commands: Command[] = [
    {
        id: 'goto',
        name: 'Go to page',
        description: 'Navigate to a specific URL',
        placeholder: 'Enter URL to navigate to...',
        icon: ArrowRight,
        onSend: navigateToURL,
        enableSend: isValidUrl,
        runningText: 'Navigating to Page'
    },
    {
        id: 'get_actions',
        name: 'Get actions',
        description: 'Find available actions on this page',
        placeholder: 'Press enter to get available actions',
        icon: Search,
        onSend: async () => {
            return { status: true, message: 'Actions retrieved successfully' };
        },
        enableSend: (prompt: string) => {
            return prompt.length > 0;
        },
        runningText: 'Getting Actions'
    },
    {
        id: 'prompt',
        name: 'Prompt',
        description: 'Ask the AI to do something',
        placeholder: 'Enter your prompt...',
        icon: MessageSquare,
        onSend: runAgent,
        enableSend: (prompt: string) => {
            return prompt.length > 0;
        },
        runningText: 'Working with Browser'
    }
];