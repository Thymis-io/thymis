<script lang="ts">
	import { ListBox, ListBoxItem } from '@skeletonlabs/skeleton';
	import ConfigBool from './config/ConfigBool.svelte';
	import ConfigString from './config/ConfigString.svelte';

	interface Setting {
		name: string;
		value: any;
		default: string;
		description: string;
		example: string | null;
		type: string;
	}

	interface Module {
		name: string;

		[x: string]: Setting;
	}

	let state: Module[] = [];
	let selected: number | null = null;

	async function loadConfig() {
		const response = await fetch('http://localhost:8000/state', {
			method: 'GET',
			headers: {
				'content-type': 'application/json'
			}
		});

		state = await response.json();
		console.log(state);

		if (state.length >= 1) {
			selected = 0;
		}
	}

	async function saveConfig() {
		const response = await fetch('http://localhost:8000/state', {
			method: 'PATCH',
			headers: {
				'content-type': 'application/json'
			},
			body: JSON.stringify(state)
		});
	}

	loadConfig();
</script>

<div class="grid grid-flow-row grid-cols-5 gap-12">
	<div>
		<ListBox>
			{#each state as module}
				<ListBoxItem bind:group={selected} value={state.indexOf(module)} name={module.name}>
					{module.name}
				</ListBoxItem>
			{/each}
		</ListBox>
		<button type="button" class="btn variant-filled mt-8" on:click={() => saveConfig()}>
			save
		</button>
	</div>
	<div class="col-span-4 grid grid-cols-4 gap-8 gap-x-10">
		{#if selected}
			{#each Object.keys(state[selected]) as settingKey}
				{#if settingKey !== 'name' && settingKey !== 'type'}
					<div class="col-span-1">{state[selected][settingKey].name}</div>
					<div class="col-span-1">
						{#if state[selected][settingKey].type == 'bool'}
							<ConfigBool name={state[selected][settingKey].name} />
						{:else if state[selected][settingKey].type == 'string'}
							<ConfigString
								bind:value={state[selected][settingKey].value}
								placeholder={state[selected][settingKey].default}
							/>
						{/if}
					</div>
					<div class="col-span-2">{state[selected][settingKey].description}</div>
				{/if}
			{/each}
		{/if}
	</div>
</div>
