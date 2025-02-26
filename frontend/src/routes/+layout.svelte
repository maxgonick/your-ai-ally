<script lang="ts">
	import Input from '$lib/components/ui/input/input.svelte';
	import * as Popover from '$lib/components/ui/popover';
	import { Toaster } from '$lib/components/ui/sonner';
	import { browserStatus, connected, urlInput } from '$lib/stores/browserStore';
	import RadioTower from 'lucide-svelte/icons/radio-tower';
	import '../app.css';
	let { children } = $props();
</script>

<Toaster />

<div class="grid h-screen max-h-screen grid-rows-[3rem_1fr]">
	<header>
		<nav aria-label="Main navigation" class="flex h-full items-center justify-between px-4">
			<a href="/">
				<h1 class="text-nowrap font-mono text-lg font-bold">
					AI &lt;<span class="text-blue-600">A11y</span>/&gt
				</h1>
			</a>
			<Input
				type="text"
				bind:value={$urlInput}
				placeholder="https://example.com"
				class="text-muted-foreground w-1/2 overflow-clip rounded border-none text-center text-sm shadow-none focus:border-none focus:text-slate-950 focus-visible:border-none focus-visible:ring-0"
				disabled={$browserStatus !== 'running'}
			/>

			<Popover.Root>
				<Popover.Trigger
					><div
						class="connection-status {$connected
							? 'bg-green-100 text-green-800'
							: 'bg-red-100 text-red-800'} flex items-center justify-center gap-1 rounded-full px-2 py-1 text-xs"
					>
						<RadioTower size="0.8rem" />
						Server {$connected ? 'Connected' : 'Disconnected'}
					</div></Popover.Trigger
				>
				<Popover.Content align="end">Place content for the popover here.</Popover.Content>
			</Popover.Root>
		</nav>
	</header>
	<main class="min-h-full">
		{@render children()}
	</main>
</div>
