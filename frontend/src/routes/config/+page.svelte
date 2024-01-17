<script lang="ts">
	import { ListBox, ListBoxItem } from '@skeletonlabs/skeleton';
	import ConfigBool from '$lib/config/ConfigBool.svelte';
	import ConfigString from '$lib/config/ConfigString.svelte';
	import type { PageData } from './$types';
	import { queryParam } from 'sveltekit-search-params';
	import { saveState } from '$lib/state';

	const selected = queryParam<number>('selected', {
		decode: (value) => (value ? parseInt(value, 10) : 0),
		encode: (value) => value.toString()
	});

	export let data: PageData;
	$: state = data.state;
	$: console.log(selected);
</script>

<div class="grid grid-flow-row grid-cols-5 gap-12">
	<div>
		<div>
			Available Modules
			<ul class="list">
				{#each data.availableModules as module}
					<li>
						<span>(icon)</span>
						<span class="flex-auto">{module.name}</span>
						<button
							class="btn"
							on:click={() => {
								state.modules = [...state.modules, module];
							}}
						>
							add
						</button>
					</li>
				{:else}
					<li>no modules available</li>
				{/each}
			</ul>
		</div>
		<div>
			Installed Modules
			<ListBox>
				{#each state.modules as module, i}
					<ListBoxItem bind:group={$selected} value={i} name={module.name}>
						<div class="flex place-content-between">
							<div>{module.name}</div>
							<button
								class="btn"
								on:click={() => {
									state.modules = state.modules.filter((_, index) => index !== i);
								}}
							>
								delete
							</button>
						</div>
					</ListBoxItem>
				{/each}
			</ListBox>
			<button type="button" class="btn variant-filled mt-8" on:click={() => saveState(state)}>
				save
			</button>
		</div>
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
