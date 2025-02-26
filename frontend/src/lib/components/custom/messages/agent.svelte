<script lang="ts">
	import Card from '$lib/components/ui/card/card.svelte';
	import { messages } from '$lib/stores/messages';
	import { turn } from '$lib/stores/turn';
	import { flyAndScale } from '$lib/utils';
	import { onMount, tick } from 'svelte';
	import { fly } from 'svelte/transition';
	import GradientText from '../gradientText.svelte';
	import { updates } from '$lib/stores/browserStore';

	export let message: Message;

	let response: string = '';

	onMount(async () => {
		const { status, message: _message } = await message.command.onSend(message.content);
		if (status === 'completed' && _message) {
			console.log(_message);
			response = _message;
			turn.set('idle');
		} else if (status === 'started') {
			const unsubscribe = updates.subscribe((update) => {
				if (update.length > 0) {
					const lastUpdate = update[update.length - 1];
					if (lastUpdate.status === 'completed') {
						response = lastUpdate.data.message;
						unsubscribe();
						updates.set([]);
						turn.set('idle');
					} else if (lastUpdate.status === 'step') {
						// response = lastUpdate.data;
					}
				}
			});
			// response = message.command;
		}
	});
</script>

<div transition:fly={{ delay: 10000 }} class="flex w-full justify-start">
	<Card class="w-3/4 p-4 shadow-sm">
		{#if response === ''}
			<GradientText>{message.command.runningText}</GradientText>
		{:else}
			{response}
		{/if}
	</Card>
</div>
