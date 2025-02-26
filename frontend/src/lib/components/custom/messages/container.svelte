<script>
	import ScrollArea from '$lib/components/ui/scroll-area/scroll-area.svelte';
	import { messages } from '$lib/stores/messages';
	import { flip } from 'svelte/animate';
	import Agent from './agent.svelte';
	import User from './user.svelte';
	import { fade } from 'svelte/transition';
</script>

<ScrollArea class="h-full w-full">
	{#if $messages.length === 0}
		<div class="flex h-full w-full items-center justify-center" transition:fade>
			<p class="text-muted-foreground">
				Chat with your <span class="font-mono">
					AI <span class="text-blue-600">&lt;A11y</span>/&gt;</span
				> here
			</p>
		</div>
	{:else}
		<div class="flex flex-col gap-4 px-4 pt-4">
			{#each $messages as message (message)}
				<div animate:flip>
					{#if message.role === 'User'}
						<User {message} />
					{:else if message.role === 'Agent'}
						<Agent {message} />
					{/if}
				</div>
			{/each}
		</div>
	{/if}
</ScrollArea>
