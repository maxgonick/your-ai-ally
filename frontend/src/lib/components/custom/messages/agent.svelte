<script lang="ts">
	import Card from '$lib/components/ui/card/card.svelte';
	import { messages } from '$lib/stores/messages';
	import { turn } from '$lib/stores/turn';
	import { flyAndScale } from '$lib/utils';
	import { onMount } from 'svelte';
	import { fly } from 'svelte/transition';
	import GradientText from '../gradientText.svelte';

	export let message: Message;

	onMount(async () => {
		await message.command.onSend(message.content);
		turn.set('idle');
	});
</script>

<div transition:fly={{ delay: 100 }} class="flex w-full justify-start">
	<Card class="w-3/4 p-4 shadow-sm">
		<GradientText>{message.command.runningText}</GradientText>
	</Card>
</div>
