<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Button, Label, Select, Toggle } from 'flowbite-svelte';
	import PageHead from '$lib/components/layout/PageHead.svelte';
	import { fetchWithNotify } from '$lib/fetchWithNotify';
	import { onMount } from 'svelte';
	import type { PageData } from './$types';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	type Frequency = 'hourly' | 'daily' | 'weekly' | 'monthly' | 'monthly_weekday';

	const WEEKDAYS = [
		{ value: 0, labelKey: 'auto-update.weekdays.mon' },
		{ value: 1, labelKey: 'auto-update.weekdays.tue' },
		{ value: 2, labelKey: 'auto-update.weekdays.wed' },
		{ value: 3, labelKey: 'auto-update.weekdays.thu' },
		{ value: 4, labelKey: 'auto-update.weekdays.fri' },
		{ value: 5, labelKey: 'auto-update.weekdays.sat' },
		{ value: 6, labelKey: 'auto-update.weekdays.sun' }
	];

	let enabled = $state(false);
	let frequency = $state<Frequency>('weekly');
	let time = $state('03:00');
	let weekdays = $state<number[]>([0, 1, 2, 3]);
	let dayOfMonth = $state(1);
	let nthWeekday = $state(1);
	let weekday = $state(0);
	let loading = $state(false);
	let saving = $state(false);

	async function loadSettings() {
		loading = true;
		try {
			const res = await fetch('/api/controller-settings');
			if (res.ok) {
				const settings = await res.json();
				enabled = settings.auto_update_enabled;
				const s = settings.auto_update_schedule;
				frequency = s.frequency ?? 'weekly';
				time = s.time ?? '03:00';
				weekdays = s.weekdays ?? [0, 1, 2, 3];
				dayOfMonth = s.day_of_month ?? 1;
				nthWeekday = s.nth_weekday ?? 1;
				weekday = s.weekday ?? 0;
			}
		} finally {
			loading = false;
		}
	}

	async function saveSettings() {
		saving = true;
		try {
			const schedule: Record<string, unknown> = { frequency, time };
			if (frequency === 'weekly') schedule.weekdays = weekdays;
			if (frequency === 'monthly') schedule.day_of_month = dayOfMonth;
			if (frequency === 'monthly_weekday') {
				schedule.nth_weekday = nthWeekday;
				schedule.weekday = weekday;
			}

			await fetchWithNotify('/api/controller-settings', {
				method: 'PATCH',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ auto_update_enabled: enabled, auto_update_schedule: schedule })
			});
		} finally {
			saving = false;
		}
	}

	async function triggerNow() {
		await fetchWithNotify('/api/action/auto-update', { method: 'POST' });
	}

	function toggleWeekday(day: number) {
		if (weekdays.includes(day)) {
			weekdays = weekdays.filter((d) => d !== day);
		} else {
			weekdays = [...weekdays, day].sort();
		}
	}

	onMount(loadSettings);

	const frequencyOptions = $derived([
		{ value: 'hourly', name: $t('auto-update.frequency.hourly') },
		{ value: 'daily', name: $t('auto-update.frequency.daily') },
		{ value: 'weekly', name: $t('auto-update.frequency.weekly') },
		{ value: 'monthly', name: $t('auto-update.frequency.monthly') },
		{ value: 'monthly_weekday', name: $t('auto-update.frequency.monthly-weekday') }
	]);

	const dayOfMonthOptions = Array.from({ length: 28 }, (_, i) => ({
		value: i + 1,
		name: String(i + 1)
	}));

	const nthWeekdayOptions = $derived([
		{ value: 1, name: $t('auto-update.nth-weekday.first') },
		{ value: 2, name: $t('auto-update.nth-weekday.second') },
		{ value: 3, name: $t('auto-update.nth-weekday.third') },
		{ value: 4, name: $t('auto-update.nth-weekday.fourth') },
		{ value: 5, name: $t('auto-update.nth-weekday.fifth') },
		{ value: -1, name: $t('auto-update.nth-weekday.last') }
	]);

	const weekdayOptions = $derived(
		WEEKDAYS.map(({ value, labelKey }) => ({ value, name: $t(labelKey) }))
	);
</script>

<PageHead
	title={$t('nav.auto-update')}
	repoStatus={data.repoStatus}
	globalState={data.globalState}
	nav={data.nav}
/>

<div class="flex flex-col gap-6">
	<!-- Description -->
	<p class="text-sm text-gray-600 dark:text-gray-400">
		{$t('auto-update.description')}
	</p>

	<!-- Info about working state -->
	<p class="text-sm text-gray-600 dark:text-gray-400">
		{$t('auto-update.working-state-warning')}
	</p>

	<!-- Enabled toggle -->
	<div class="flex items-center gap-3">
		<Toggle bind:checked={enabled} disabled={loading} />
		<span class="text-sm font-medium text-gray-900 dark:text-white">
			{$t('auto-update.enabled')}
		</span>
	</div>

	<!-- Frequency -->
	<div>
		<Label class="mb-2">{$t('auto-update.frequency.label')}</Label>
		<Select bind:value={frequency} items={frequencyOptions} disabled={loading} />
	</div>

	<!-- Time of day (not shown for hourly) -->
	{#if frequency !== 'hourly'}
		<div>
			<Label class="mb-2">{$t('auto-update.time-of-day')}</Label>
			<input
				type="time"
				bind:value={time}
				disabled={loading}
				class="block w-full rounded-lg border border-gray-300 bg-gray-50 p-2.5 text-sm text-gray-900 focus:border-primary-500 focus:ring-primary-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 dark:focus:border-primary-500 dark:focus:ring-primary-500 disabled:cursor-not-allowed disabled:opacity-50"
			/>
		</div>
	{/if}

	<!-- Weekday picker (weekly) -->
	{#if frequency === 'weekly'}
		<div>
			<Label class="mb-2">{$t('auto-update.weekdays.label')}</Label>
			<div class="flex flex-wrap gap-2">
				{#each WEEKDAYS as { value, labelKey }}
					<button
						type="button"
						onclick={() => toggleWeekday(value)}
						disabled={loading}
						class="rounded-lg border px-3 py-1.5 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50
							{weekdays.includes(value)
							? 'border-primary-500 bg-primary-100 text-primary-700 dark:bg-primary-900 dark:text-primary-300'
							: 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'}"
					>
						{$t(labelKey)}
					</button>
				{/each}
			</div>
		</div>
	{/if}

	<!-- Day of month picker (monthly) -->
	{#if frequency === 'monthly'}
		<div>
			<Label class="mb-2">{$t('auto-update.day-of-month')}</Label>
			<Select bind:value={dayOfMonth} items={dayOfMonthOptions} disabled={loading} />
		</div>
	{/if}

	<!-- Nth weekday of month picker (monthly_weekday) -->
	{#if frequency === 'monthly_weekday'}
		<div class="flex gap-3">
			<div class="flex-1">
				<Label class="mb-2">{$t('auto-update.nth-weekday.label')}</Label>
				<Select bind:value={nthWeekday} items={nthWeekdayOptions} disabled={loading} />
			</div>
			<div class="flex-1">
				<Label class="mb-2">{$t('auto-update.weekday.label')}</Label>
				<Select bind:value={weekday} items={weekdayOptions} disabled={loading} />
			</div>
		</div>
	{/if}

	<!-- Actions -->
	<div class="flex justify-between gap-2">
		<Button color="alternative" onclick={triggerNow} disabled={loading}>
			{$t('auto-update.trigger-now')}
		</Button>
		<Button onclick={saveSettings} disabled={saving || loading}>
			{$t('auto-update.save')}
		</Button>
	</div>
</div>
