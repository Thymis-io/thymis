<script lang="ts">
	import { ListBox, ListBoxItem } from '@skeletonlabs/skeleton';
	import ConfigBool from '$lib/config/ConfigBool.svelte';
	import ConfigString from '$lib/config/ConfigString.svelte';
	import type { PageData } from './$types';
	import { queryParam } from 'sveltekit-search-params';
	const selected = queryParam<number>('selected', {
		decode: (value) => (value ? parseInt(value, 10) : 0),
		encode: (value) => value.toString()
	});
	export let data: PageData;

	$: state = data.state;

	async function saveConfig() {
		await fetch('http://localhost:8000/state', {
			method: 'PATCH',
			headers: {
				'content-type': 'application/json'
			},
			body: JSON.stringify(state)
		});
	}

	$: console.log(selected);
</script>

<div class="grid grid-flow-row grid-cols-5 gap-12">
	<div>
		<ListBox>
			{#each state.modules as module, i}
				<ListBoxItem bind:group={$selected} value={i} name={module.name}>
					{module.name}
				</ListBoxItem>
			{/each}
		</ListBox>
		<button type="button" class="btn variant-filled mt-8" on:click={() => saveConfig()}>
			save
		</button>
	</div>
	<div class="col-span-4 grid grid-cols-4 gap-8 gap-x-10">
		{#if $selected != null && $selected < state.modules.length}
			{#each Object.keys(state.modules[$selected]) as settingKey}
				{#if settingKey !== 'name' && settingKey !== 'type'}
					<div class="col-span-1">{state.modules[$selected][settingKey].name}</div>
					<div class="col-span-1">
						{#if state.modules[$selected][settingKey].type == 'bool'}
							<ConfigBool
								bind:value={state.modules[$selected][settingKey].value}
								name={state.modules[$selected][settingKey].name}
							/>
						{:else if state.modules[$selected][settingKey].type == 'string'}
							<ConfigString
								bind:value={state.modules[$selected][settingKey].value}
								placeholder={state.modules[$selected][settingKey].default}
							/>
						{/if}
					</div>
					<div class="col-span-2">{state.modules[$selected][settingKey].description}</div>
				{/if}
			{/each}
		{/if}
	</div>
</div>
