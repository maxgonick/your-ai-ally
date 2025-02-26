<script lang="ts">
	import * as Resizable from '$lib/components/ui/resizable';
	import { Textarea } from '$lib/components/ui/textarea';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
	import Browser from '$lib/components/custom/browser.svelte';
	import CirclePlus from 'lucide-svelte/icons/circle-plus';
	import Command from '$lib/components/custom/command.svelte';
	import ActionInput from '$lib/components/custom/actionInput.svelte';
	import Container from '$lib/components/custom/messages/container.svelte';
</script>

<Resizable.PaneGroup direction="horizontal" class="h-full max-w-full border">
	<Resizable.Pane defaultSize={50} minSize={25} class="relative flex h-full flex-col">
		<Container />
		<div class="relative z-10 flex w-full items-center justify-center self-end border-t p-4">
			<ActionInput />
		</div>
	</Resizable.Pane>
	<Resizable.Handle />
	<Resizable.Pane defaultSize={50} minSize={50} class="min-h-full ">
		<Browser />
	</Resizable.Pane>
</Resizable.PaneGroup>
