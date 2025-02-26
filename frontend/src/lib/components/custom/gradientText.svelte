<script lang="ts">
	let { children } = $props();
</script>

<div class="wrapper">
	<p>{@render children()}</p>
</div>

<style>
	.wrapper {
		font-family: sans-serif;
		color: #3c3c3c;
		display: flex;
		align-items: center;
		justify-content: center;
		height: 100%;
		flex-direction: column;
	}

	@keyframes textShine {
		0% {
			background-position: 200% 50%;
		}
		100% {
			background-position: 0% 50%;
		}
	}

	p {
		background: linear-gradient(
			to right,
			oklch(0.869 0.005 56.366) 0%,
			/* stone-300 */ oklch(0.216 0.006 56.043) 10%,
			/* stone-900 */ oklch(0.216 0.006 56.043) 90%,
			/* stone-900 */ oklch(0.869 0.005 56.366) 100% /* stone-300 */
		);
		-webkit-background-clip: text;
		background-clip: text;
		-webkit-text-fill-color: transparent;
		background-size: 200% auto;
		background-repeat: repeat;
		animation: textShine 2s cubic-bezier(0.55, 0, 0.65, 1) infinite;
	}
</style>
