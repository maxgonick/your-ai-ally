import ArrowRight from "lucide-svelte/icons/arrow-right";
import MessageSquare from "lucide-svelte/icons/message-square";
import Search from "lucide-svelte/icons/search";
import * as browserStore from '$lib/stores/browserStore';

// Function to validate a URL
function isValidUrl(url: string): boolean {
    const urlRegex =
        /^(https?:\/\/)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$/;
    return urlRegex.test(url);
}

export const Commands: Command[] = [
    {
        id: 'goto',
        name: 'Go to page',
        description: 'Navigate to a specific URL',
        placeholder: 'Enter URL to navigate to...',
        icon: ArrowRight,
        onSend: async (url: string) => { await browserStore.navigateToUrl(url); },
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
        onSend: async (prompt: string) => { await browserStore.runAgent(prompt); },
        enableSend: (prompt: string) => {
            return prompt.length > 0;
        },
        runningText: 'Generating Response'
    }
];