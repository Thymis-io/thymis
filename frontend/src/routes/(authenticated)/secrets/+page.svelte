<script lang="ts">
	import { t } from 'svelte-i18n';
	import { saveState, state } from '$lib/state';
	import TableBodyEditCell from '$lib/components/TableBodyEditCell.svelte';
	import {
		Button,
		Table,
		TableHead,
		TableHeadCell,
		TableBody,
		TableBodyRow,
		TableBodyCell
	} from 'flowbite-svelte';
	import PageHead from '$lib/components/PageHead.svelte';
	import type { PageData } from './$types';

	export let data: PageData;

	let secrets = [];
</script>

<PageHead title={$t('nav.secrets')} repoStatus={data.repoStatus} />

<Table shadow>
	<TableHead theadClass="text-xs normal-case">
		<TableHeadCell padding="p-2">{$t('secrets.name')}</TableHeadCell>
		<TableHeadCell padding="p-2">{$t('secrets.type')}</TableHeadCell>
		<TableHeadCell padding="p-2">{$t('secrets.actions')}</TableHeadCell>
	</TableHead>
	<TableBody>
		{#each secrets as [name, secret]}
			<TableBodyRow>
				<TableBodyEditCell
					bind:value={name}
					onEnter={(newName) => changeSecretName(name, newName)}
				/>
				<TableBodyCell tdClass="p-2">{secret.type}</TableBodyCell>
				<TableBodyCell tdClass="p-2">
					<div class="flex gap-1">
						<Button on:click={() => openEditSecret(name)}>
							{$t('secrets.edit')}
						</Button>
						<Button on:click={() => copySecretId(name)}>
							{$t('secrets.copy-id')}
						</Button>
						<Button on:click={() => deleteSecret(name)}>
							{$t('secrets.delete')}
						</Button>
					</div>
				</TableBodyCell>
			</TableBodyRow>
		{/each}
	</TableBody>
</Table>
<Button color="alternative" class="mt-4" on:click={() => addSecret()}>+</Button>
