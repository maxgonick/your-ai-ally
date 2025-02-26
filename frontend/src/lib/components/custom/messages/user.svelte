<script lang="ts">
	import * as Avatar from '$lib/components/ui/avatar';
	import Card from '$lib/components/ui/card/card.svelte';
	import { messages } from '$lib/stores/messages';
	import { flyAndScale } from '$lib/utils';
	import { onMount } from 'svelte';
	import { fly } from 'svelte/transition';

	export let message: Message;

	onMount(() => {
		messages.update((msgs) => {
			msgs.push({
				role: 'Agent',
				content: message.content,
				command: message.command
			});
			return msgs;
		});
	});
</script>

<div transition:fly={{ delay: 1000 }} class="flex w-full justify-end">
	<div class="max-w-3/4 flex items-center gap-2">
		{message.content}
		<Avatar.Root class="h-6 w-6">
			<Avatar.Image src="https://github.com/kalcow.png" alt="@kalcow" />
			<Avatar.Fallback>KK</Avatar.Fallback>
		</Avatar.Root>
	</div>
	<!-- <Card class="max-w-3/4 rounded-3xl p-4">{message.content}</Card> -->
</div>
