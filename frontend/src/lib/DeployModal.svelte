<script lang="ts">
	import { getModalStore } from '@skeletonlabs/skeleton';
	const modalStore = getModalStore();

	$: summary = '';

	const deploy = async () => {
		await fetch(`http://localhost:8000/action/deploy?summary=${summary}`, {
			method: 'POST'
		});

		modalStore.close();
	};
</script>

{#if $modalStore[0]}
	<div class="modal-example-form card p-4 w-modal shadow-xl space-y-4">
		<header class="text-2xl font-bold">{$modalStore[0].title ?? '(title missing)'}</header>
		<!-- Show summary text box and push button on the right -->
		<div class="flex flex-wrap gap-2">
			<input type="text" bind:value={summary} class="input input-bordered" placeholder="Summary" />
			<div class="flex-grow" />
			<button class="btn variant-filled" on:click={deploy}>Deploy</button>
		</div>
	</div>
{/if}
