<script>
	import ScrollArea from '$lib/components/ui/scroll-area/scroll-area.svelte';
	import { messages } from '$lib/stores/messages';
	import { flip } from 'svelte/animate';
	import Agent from './agent.svelte';
	import User from './user.svelte';
</script>

<ScrollArea class="h-full w-full">
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
</ScrollArea>
