<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Button, Input, Label, Modal, Toggle } from 'flowbite-svelte';
	import { fetchWithNotify } from '$lib/fetchWithNotify';
	import Settings2 from 'lucide-svelte/icons/settings-2';

	interface Props {
		open?: boolean;
	}

	let { open = $bindable(false) }: Props = $props();

	let enabled = $state(false);
	let schedule = $state('daily');
	let loading = $state(false);

	async function loadSettings() {
		const res = await fetch('/api/controller-settings');
		if (res.ok) {
			const data = await res.json();
			enabled = data.auto_update_enabled;
			schedule = data.auto_update_schedule;
		}
	}

	async function saveSettings() {
		loading = true;
		try {
			await fetchWithNotify('/api/controller-settings', {
				method: 'PATCH',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					auto_update_enabled: enabled,
					auto_update_schedule: schedule
				})
			});
		} finally {
			loading = false;
			open = false;
		}
	}

	async function triggerNow() {
		await fetchWithNotify('/api/action/auto-update', { method: 'POST' });
		open = false;
	}
</script>

<Modal bind:open title={$t('auto-update.title')} size="md" outsideclose on:open={loadSettings}>
	<div class="flex flex-col gap-6">
		<div class="flex items-center gap-4">
			<Toggle bind:checked={enabled} />
			<span class="text-sm font-medium text-gray-900 dark:text-white">
				{$t('auto-update.enabled')}
			</span>
		</div>
		<div>
			<Label for="schedule" class="mb-2">{$t('auto-update.schedule')}</Label>
			<Input
				id="schedule"
				bind:value={schedule}
				placeholder={$t('auto-update.schedule-placeholder')}
				disabled={!enabled}
			/>
		</div>
		<div class="flex justify-between gap-2">
			<Button color="alternative" on:click={triggerNow}>
				{$t('auto-update.trigger-now')}
			</Button>
			<Button on:click={saveSettings} disabled={loading}>
				{$t('auto-update.save')}
			</Button>
		</div>
	</div>
</Modal>
