<script lang="ts">
	import { tick, createEventDispatcher } from 'svelte';
	import * as Command from '$lib/components/ui/command/index.js';
	import { Button } from '$lib/components/ui/button';
	import ArrowRight from 'lucide-svelte/icons/arrow-right';
	import Search from 'lucide-svelte/icons/search';
	import MessageSquare from 'lucide-svelte/icons/message-square';
	import ChevronUp from 'lucide-svelte/icons/chevron-up';
	import Send from 'lucide-svelte/icons/send';
	import { clickOutside } from '$lib/events/clickOutside';
	import { flyAndScale } from '$lib/utils';

	export let disabled = false;

	// Event dispatcher
	const dispatch = createEventDispatcher<{
		action: { action: string; value: string };
	}>();

	type Action = {
		id: string;
		name: string;
		description: string;
		placeholder: string;
		icon: typeof ArrowRight;
		onSend: () => Promise<void>;
		enableSend: () => boolean;
	};

	const ACTIONS: Action[] = [
		{
			id: 'goto',
			name: 'Go to page',
			description: 'Navigate to a specific URL',
			placeholder: 'Enter URL to navigate to...',
			icon: ArrowRight,

			onSend: async () => {
				dispatch('action', { action: 'goto', value: inputText });
			},
			enableSend: () => {
				return inputText.startsWith('http') || inputText.startsWith('www');
			}
		},
		{
			id: 'get_actions',
			name: 'Get actions',
			description: 'Find available actions on this page',
			placeholder: 'Press enter to get available actions',
			icon: Search,
			onSend: async () => {
				dispatch('action', { action: 'get_actions', value: inputText });
			},
			enableSend: () => {
				return inputText.length > 0;
			}
		},
		{
			id: 'prompt',
			name: 'Prompt',
			description: 'Ask the AI to do something',
			placeholder: 'Enter your prompt...',
			icon: MessageSquare,
			onSend: async () => {
				dispatch('action', { action: 'prompt', value: inputText });
			},
			enableSend: () => {
				return inputText.length > 0;
			}
		}
	];

	// Component state
	let inputText = '';
	let showActions = false;
	let selectedAction: Action | null = null;
	let textarea: HTMLTextAreaElement;
	let actionsDialogOpen = false;
	let showKeyboardShortcuts = false;
	let commandRef: HTMLInputElement | null = null;

	// Handle @ symbol to show actions
	async function handleInput(e: Event & { currentTarget: EventTarget & HTMLTextAreaElement }) {
		if (e instanceof InputEvent && e.data === '@') {
			showActions = true;
			actionsDialogOpen = true;
			await tick();
			setTimeout(() => {
				commandRef?.focus();
			}, 200);
		}

		// If the user deletes the @ symbol
		if (inputText === '@' && e instanceof InputEvent && !e.data) {
			showActions = false;
			actionsDialogOpen = false;
			commandRef?.blur();
		}
	}

	function selectAction(action: Action) {
		selectedAction = action;
		inputText = ''; // Clear the @ symbol
		showActions = false;
		actionsDialogOpen = false;

		// Focus the input
		setTimeout(() => {
			textarea.focus();
		}, 0);
	}

	function submitAction() {
		if (!inputText || !selectedAction) return;

		dispatch('action', { action: selectedAction.id, value: inputText });
		inputText = '';
		selectedAction = null;
	}

	// Handle keyboard shortcuts
	function handleKeydown(e: KeyboardEvent) {
		// Escape key to close actions
		if (e.key === 'Escape' && showActions) {
			showActions = false;
			actionsDialogOpen = false;
			e.preventDefault();
		}

		// Enter to submit (but not if shift is pressed)
		if (e.key === 'Enter' && !e.shiftKey) {
			if (inputText) {
				submitAction();
				e.preventDefault();
			}
		}
	}

	// Close the actions menu when clicking outside
	function handleBlur() {
		setTimeout(() => {
			if (!actionsDialogOpen) {
				showActions = false;
				commandRef?.blur();
			}
		}, 200);
	}

	// Toggle keyboard shortcuts
	function toggleKeyboardShortcuts() {
		showKeyboardShortcuts = !showKeyboardShortcuts;
	}

	// Clear action selection
	function clearSelection() {
		selectedAction = null;
	}
</script>

<div class="bg-background flex w-full flex-col rounded-lg border shadow-sm">
	{#if selectedAction}
		<div class="flex items-center border-b px-3 py-2">
			<div class="flex items-center gap-2 text-sm">
				<span class="bg-primary/10 text-primary rounded-md p-1">
					<svelte:component this={selectedAction.icon} class="h-4 w-4" />
				</span>
				<span class="font-medium">{selectedAction.name}</span>
			</div>
			<button
				type="button"
				class="text-muted-foreground hover:text-foreground ml-auto"
				aria-label="Clear selection"
				on:click={clearSelection}
			>
				<svg
					width="16"
					height="16"
					viewBox="0 0 24 24"
					fill="none"
					xmlns="http://www.w3.org/2000/svg"
				>
					<path
						d="M18 6L6 18M6 6L18 18"
						stroke="currentColor"
						stroke-width="2"
						stroke-linecap="round"
						stroke-linejoin="round"
					/>
				</svg>
			</button>
		</div>
	{/if}

	<div class="relative flex w-full">
		<textarea
			bind:this={textarea}
			bind:value={inputText}
			on:input={handleInput}
			on:keydown={handleKeydown}
			on:blur={handleBlur}
			placeholder={selectedAction
				? selectedAction.placeholder
				: 'Type @ to access commands or enter a prompt...'}
			{disabled}
			rows="3"
			class="placeholder:text-muted-foreground w-full flex-1 resize-none border-0 bg-transparent p-3 focus-visible:outline-none focus-visible:ring-0 disabled:cursor-not-allowed disabled:opacity-50"
			aria-label="Message input"
		></textarea>
	</div>

	<div class="flex items-center justify-between border-t p-2">
		<div class="text-muted-foreground flex gap-2 text-xs">
			<button
				type="button"
				class="hover:bg-muted rounded p-1"
				on:click={toggleKeyboardShortcuts}
				aria-label="Keyboard shortcuts"
			>
				<ChevronUp
					class={`h-4 w-4 transition-transform ${showKeyboardShortcuts ? 'rotate-180' : ''}`}
				/>
			</button>
			{#if showKeyboardShortcuts}
				<div class="flex gap-2">
					<kbd class="bg-muted rounded px-1.5 text-xs">@</kbd>
					<span>Actions</span>
					<kbd class="bg-muted rounded px-1.5 text-xs">↵</kbd>
					<span>Send</span>
					<kbd class="bg-muted rounded px-1.5 text-xs">Shift+↵</kbd>
					<span>New line</span>
				</div>
			{/if}
		</div>

		<Button
			variant="default"
			size="sm"
			onclick={submitAction}
			disabled={!inputText || !selectedAction || disabled}
			aria-label="Send message"
		>
			<Send class="mr-1 h-4 w-4" />
			Send
		</Button>
	</div>

	{#if showActions}
		<div
			use:clickOutside
			on:outsideclick={() => (showActions = false)}
			transition:flyAndScale
			class="absolute bottom-14 left-3 w-4/5"
		>
			<Command.Root class="overflow-hidden rounded-lg border shadow-md">
				<Command.Input
					placeholder="Type a command or search..."
					{disabled}
					aria-label="Search commands"
					bind:ref={commandRef}
				/>
				<Command.List>
					<Command.Empty>No actions found</Command.Empty>
					<Command.Group heading="Available Commands">
						{#each ACTIONS as action}
							<Command.Item onSelect={() => selectAction(action)} class="cursor-pointer">
								<div class="flex items-center gap-2">
									<span class="flex-shrink-0">
										<svelte:component this={action.icon} class="h-4 w-4" />
									</span>
									<div class="flex flex-col">
										<span>{action.name}</span>
										<span class="text-muted-foreground text-xs">{action.description}</span>
									</div>
								</div>
							</Command.Item>
						{/each}
					</Command.Group>
				</Command.List>
			</Command.Root>
		</div>
	{/if}
</div>
