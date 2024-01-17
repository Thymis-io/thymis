<script lang="ts">
	import type { SvelteComponent } from 'svelte';
	import { getModalStore } from '@skeletonlabs/skeleton';

	export let parent: SvelteComponent;
	const modalStore = getModalStore();

	const formData = {
		displayName: '',
		hostname: ''
	};

	function onFormSubmit(): void {
		if ($modalStore[0].response) $modalStore[0].response(formData);
		modalStore.close();
	}
</script>

{#if $modalStore[0]}
	<div class="modal-example-form card p-4 w-modal shadow-xl space-y-4">
		<header class="text-2xl font-bold">{$modalStore[0].title ?? '(title missing)'}</header>
		<!-- <article>{$modalStore[0].body ?? '(body missing)'}</article> -->
		<form class="modal-form space-y-4">
			<label class="label">
				<span>Name</span>
				<input
					class="input"
					type="text"
					bind:value={formData.displayName}
					placeholder="Enter name..."
				/>
			</label>
			<label class="label">
				<span>Hostname</span>
				<input
					class="input"
					type="text"
					bind:value={formData.hostname}
					placeholder="Enter hostname..."
				/>
			</label>
		</form>
		<footer class="modal-footer {parent.regionFooter}">
			<button class="btn {parent.buttonNeutral}" on:click={parent.onClose}
				>{parent.buttonTextCancel}</button
			>
			<button class="btn {parent.buttonPositive}" on:click={onFormSubmit}>Create</button>
		</footer>
	</div>
{/if}
