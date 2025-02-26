<script lang="ts">
	import Input from '$lib/components/ui/input/input.svelte';
	import { Toaster } from '$lib/components/ui/sonner';
	import { browserStatus, urlInput } from '$lib/stores/browserStore';
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
				class="text-muted-foreground flex-1 rounded border-none text-center text-sm shadow-none focus:border-none focus:text-slate-950 focus-visible:border-none focus-visible:ring-0"
				disabled={$browserStatus !== 'running'}
			/>
		</nav>
	</header>
	<main class="min-h-full">
		{@render children()}
	</main>
</div>
