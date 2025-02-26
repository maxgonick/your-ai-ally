<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { Button } from '$lib/components/ui/button';
	import { Textarea } from '$lib/components/ui/textarea';
	import * as browserStore from '$lib/stores/browserStore';
	import {
		connected,
		messages,
		browserScreenshot,
		isLoading,
		browserStatus,
		urlInput,
		promptInput,
		fpsValue
	} from '$lib/stores/browserStore';
	import GradientText from './gradientText.svelte';
	import { Input } from '../ui/input';
	import Spinner from './spinner.svelte';
	import RadioTower from 'lucide-svelte/icons/radio-tower';
	import * as Popover from '../ui/popover';

	// Lifecycle
	onMount(async () => {
		browserStore.connectWebSocket();
		await browserStore.startBrowser();
	});

	onDestroy(async () => {
		browserStore.disconnectWebSocket();
		await browserStore.stopBrowser();
	});
</script>

<div class="h-12 border-b">
	<div class="flex h-full items-center justify-evenly px-4">
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
			<Popover.Content align="start">Place content for the popover here.</Popover.Content>
		</Popover.Root>
		<Input
			type="text"
			bind:value={$urlInput}
			placeholder="https://example.com"
			class="flex-1 rounded border-none text-center text-sm shadow-none"
			disabled={$browserStatus !== 'running'}
		/>
		<Button
			onclick={() => browserStore.navigateToUrl($urlInput)}
			variant="outline"
			disabled={$browserStatus !== 'running'}
		>
			Go
		</Button>
	</div>
</div>

<div class="flex max-h-full min-h-full flex-col border-b">
	<!-- Browser View -->

	{#if $browserScreenshot}
		<div
			class="relative flex h-full w-full grow items-center justify-center overflow-hidden bg-contain bg-center bg-no-repeat"
			style="background-image: url({$browserScreenshot})"
		></div>
		<!-- <img
				src={$browserScreenshot}
				alt="Browser View"
				class="h-full w-auto object-scale-down"
			/> -->
	{:else}
		<div class="relative flex h-full w-full grow items-center justify-center">
			{#if $isLoading}
				<div class="flex h-full items-center gap-3">
					<GradientText>Loading browser</GradientText>
				</div>
			{:else}
				<GradientText>Waiting for browser to start</GradientText>
			{/if}
		</div>
	{/if}

	<!-- Controls Section -->
	{#if true}
		<div class="space-y-3 border-t p-3">
			<div class="flex flex-wrap gap-2">
				<div
					class="connection-status {$connected
						? 'bg-green-100 text-green-800'
						: 'bg-red-100 text-red-800'} rounded px-2 py-1 text-xs"
				>
					WebSocket: {$connected ? 'Connected' : 'Disconnected'}
				</div>

				<Button
					onclick={browserStore.startBrowser}
					variant="outline"
					size="sm"
					disabled={$browserStatus === 'running' || $browserStatus === 'starting'}
				>
					Start Browser
				</Button>

				<Button
					onclick={browserStore.stopBrowser}
					variant="outline"
					size="sm"
					disabled={$browserStatus === 'idle' || $browserStatus === 'stopping'}
				>
					Stop Browser
				</Button>

				<div class="flex flex-1 gap-2">
					<Input
						type="text"
						bind:value={$urlInput}
						placeholder="https://example.com"
						class="flex-1 rounded border px-3 py-1 text-sm"
						disabled={$browserStatus !== 'running'}
					/>
					<Button
						onclick={() => browserStore.navigateToUrl($urlInput)}
						variant="outline"
						size="sm"
						disabled={$browserStatus !== 'running'}
					>
						Navigate
					</Button>
				</div>
			</div>

			<div class="flex items-center gap-2">
				<label for="fps-control" class="text-sm">Speed (FPS):</label>
				<input
					id="fps-control"
					type="range"
					min="1"
					max="30"
					step="1"
					bind:value={$fpsValue}
					class="w-32"
					disabled={$browserStatus !== 'running'}
				/>
				<span class="text-sm">{$fpsValue} FPS</span>
				<Button
					onclick={() => browserStore.setFps($fpsValue)}
					variant="outline"
					size="sm"
					disabled={$browserStatus !== 'running'}
				>
					Apply
				</Button>
			</div>

			<div class="flex flex-col gap-2">
				<Textarea
					bind:value={$promptInput}
					placeholder="Enter prompt for the AI agent"
					rows={2}
					class="resize-none"
					disabled={$browserStatus !== 'running'}
				/>
				<Button
					onclick={() => browserStore.runAgent($promptInput)}
					variant="default"
					class="w-full"
					disabled={$browserStatus !== 'running'}
				>
					Run Agent
				</Button>
			</div>

			<div class="h-32 overflow-y-auto rounded border bg-gray-50 p-2 text-sm">
				{#each $messages as message}
					<div class="mb-1 border-b border-gray-100 pb-1">{message}</div>
				{/each}
			</div>
		</div>
	{/if}
</div>
