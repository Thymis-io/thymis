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

	type Frequency = 'daily' | 'weekly' | 'monthly' | 'monthly_weekday';

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
	let frequency = $state<Frequency>('daily');
	let time = $state('03:00');
	let weekdays = $state<number[]>([0, 1, 2, 3]); // for daily (multi)
	let weekday = $state(0); // for weekly (single)
	let dayOfMonth = $state(1);
	let nthWeekday = $state(1);
	let monthlyWeekday = $state(0); // weekday for monthly_weekday
	let loading = $state(false);
	let saving = $state(false);
	let dirty = $state(false);

	// Track the last saved snapshot to detect unsaved changes
	let savedSnapshot = $state('');

	function snapshot() {
		return JSON.stringify({
			enabled,
			frequency,
			time,
			weekdays,
			weekday,
			dayOfMonth,
			nthWeekday,
			monthlyWeekday
		});
	}

	$effect(() => {
		// Re-run whenever any form value changes
		dirty = snapshot() !== savedSnapshot;
	});

	async function loadSettings() {
		loading = true;
		try {
			const res = await fetch('/api/controller-settings');
			if (res.ok) {
				const settings = await res.json();
				enabled = settings.auto_update_enabled;
				const s = settings.auto_update_schedule;
				frequency = s.frequency ?? 'daily';
				time = s.time ?? '03:00';
				weekdays = s.weekdays ?? [0, 1, 2, 3];
				weekday = s.weekday ?? 0;
				dayOfMonth = s.day_of_month ?? 1;
				nthWeekday = s.nth_weekday ?? 1;
				monthlyWeekday = s.weekday ?? 0;
				savedSnapshot = snapshot();
				dirty = false;
			}
		} finally {
			loading = false;
		}
	}

	async function saveSettings() {
		saving = true;
		try {
			const schedule: Record<string, unknown> = { frequency, time };
			if (frequency === 'daily') schedule.weekdays = weekdays;
			if (frequency === 'weekly') schedule.weekday = weekday;
			if (frequency === 'monthly') schedule.day_of_month = dayOfMonth;
			if (frequency === 'monthly_weekday') {
				schedule.nth_weekday = nthWeekday;
				schedule.weekday = monthlyWeekday;
			}

			const response = await fetchWithNotify('/api/controller-settings', {
				method: 'PATCH',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ auto_update_enabled: enabled, auto_update_schedule: schedule })
			});
			if (response.ok) {
				savedSnapshot = snapshot();
				dirty = false;
			}
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

	// ---------------------------------------------------------------------------
	// Local-time helpers
	// ---------------------------------------------------------------------------

	/**
	 * Parse "HH:MM" UTC time and return a Date on the Unix epoch day (1970-01-05,
	 * which is a Monday) so weekday arithmetic works cleanly.
	 * Returns null on bad input.
	 */
	function utcTimeToDate(utcTime: string): Date | null {
		const match = utcTime.match(/^(\d{1,2}):(\d{2})$/);
		if (!match) return null;
		const hh = parseInt(match[1], 10);
		const mm = parseInt(match[2], 10);
		if (hh > 23 || mm > 59) return null;
		// 1970-01-05 is a Monday (weekday index 0 in our 0=Mon scheme)
		return new Date(Date.UTC(1970, 0, 5, hh, mm, 0));
	}

	/**
	 * Format a Date to "HH:MM" in the local timezone.
	 */
	function formatLocalTime(d: Date): string {
		return d.toLocaleTimeString(undefined, {
			hour: '2-digit',
			minute: '2-digit',
			hour12: false
		});
	}

	/**
	 * Return the local timezone abbreviation (e.g. "CET", "EST").
	 */
	function localTzName(): string {
		return Intl.DateTimeFormat().resolvedOptions().timeZone;
	}

	/**
	 * Given a UTC weekday index (0=Mon) and the UTC time string, compute the local
	 * weekday index accounting for midnight crossings.
	 * Returns the local weekday index (0=Mon … 6=Sun).
	 */
	function utcWeekdayToLocal(utcWeekdayIdx: number, utcTime: string): number {
		const base = utcTimeToDate(utcTime);
		if (!base) return utcWeekdayIdx;
		// 1970-01-05 is Monday=0, so offset by utcWeekdayIdx days
		const d = new Date(base.getTime() + utcWeekdayIdx * 86400000);
		// getDay(): 0=Sun,1=Mon...6=Sat → convert to 0=Mon…6=Sun
		const jsDay = d.getDay(); // local day
		return (jsDay + 6) % 7;
	}

	/**
	 * Returns the day-shift caused by UTC→local conversion: -1, 0, or +1.
	 */
	function dayShift(utcTime: string): number {
		const base = utcTimeToDate(utcTime);
		if (!base) return 0;
		const utcDay = base.getUTCDay();
		const localDay = base.getDay();
		const diff = (localDay - utcDay + 7) % 7;
		// diff is 0, 1 (next day), or 6 (previous day → -1)
		if (diff === 0) return 0;
		if (diff === 1) return 1;
		return -1;
	}

	// Reactive derived values
	const localTimeDate = $derived(utcTimeToDate(time));
	const localTimeStr = $derived(localTimeDate ? formatLocalTime(localTimeDate) : null);
	const tzName = $derived(localTzName());
	const shift = $derived(dayShift(time));

	// For each UTC weekday chip, what is its local weekday label?
	const localWeekdayLabels = $derived(
		WEEKDAYS.map(({ value, labelKey }) => {
			const localIdx = utcWeekdayToLocal(value, time);
			const localLabelKey = WEEKDAYS[localIdx]?.labelKey ?? labelKey;
			return { value, labelKey, localLabelKey, shifted: localIdx !== value };
		})
	);

	const frequencyOptions = $derived([
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

	// weekday options annotated with local day name when shifted
	const weekdayOptionsLocal = $derived(
		localWeekdayLabels.map(({ value, labelKey, localLabelKey, shifted }) => ({
			value,
			name: shifted
				? `${$t(labelKey)} (${$t('auto-update.local-day')}: ${$t(localLabelKey)})`
				: $t(labelKey)
		}))
	);
</script>

<PageHead
	title={$t('nav.auto-update')}
	repoStatus={data.repoStatus}
	globalState={data.globalState}
	nav={data.nav}
/>

<div class="max-w-xl mx-auto flex flex-col gap-6">
	<!-- Description -->
	<p class="text-sm text-gray-600 dark:text-gray-400">
		{$t('auto-update.description')}
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

	<!-- Time of day (UTC) with local-time hint -->
	<div>
		<Label class="mb-2">{$t('auto-update.time-of-day')}</Label>
		<input
			type="time"
			bind:value={time}
			disabled={loading}
			class="block w-full rounded-lg border border-gray-300 bg-gray-50 p-2.5 text-sm text-gray-900 focus:border-primary-500 focus:ring-primary-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 dark:focus:border-primary-500 dark:focus:ring-primary-500 disabled:cursor-not-allowed disabled:opacity-50"
		/>
		{#if localTimeStr}
			<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
				{localTimeStr}
				{tzName}
				{#if shift === 1}
					(+1 {$t('auto-update.local-next-day')})
				{:else if shift === -1}
					(−1 {$t('auto-update.local-prev-day')})
				{/if}
			</p>
		{/if}
	</div>

	<!-- Weekday chip-buttons (daily = multi-select) -->
	{#if frequency === 'daily'}
		<div>
			<Label class="mb-2">{$t('auto-update.weekdays.label')}</Label>
			<div class="flex flex-wrap gap-2">
				{#each localWeekdayLabels as { value, labelKey, localLabelKey, shifted } (labelKey)}
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
						{#if shifted}
							<span class="opacity-60 text-xs">({$t(localLabelKey)})</span>
						{/if}
					</button>
				{/each}
			</div>
			{#if shift !== 0}
				<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
					{$t('auto-update.weekday-day-shift-note', { values: { tz: tzName } })}
				</p>
			{/if}
		</div>
	{/if}

	<!-- Single weekday selector (weekly = pick one) -->
	{#if frequency === 'weekly'}
		<div>
			<Label class="mb-2">{$t('auto-update.weekday.label')}</Label>
			<Select bind:value={weekday} items={weekdayOptionsLocal} disabled={loading} />
			{#if shift !== 0}
				<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
					{$t('auto-update.weekday-day-shift-note', { values: { tz: tzName } })}
				</p>
			{/if}
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
				<Select bind:value={monthlyWeekday} items={weekdayOptionsLocal} disabled={loading} />
			</div>
		</div>
		{#if shift !== 0}
			<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
				{$t('auto-update.weekday-day-shift-note', { values: { tz: tzName } })}
			</p>
		{/if}
	{/if}

	<!-- Actions -->
	<div class="flex items-center justify-between gap-2">
		<Button color="alternative" onclick={triggerNow} disabled={loading}>
			{$t('auto-update.trigger-now')}
		</Button>
		<div class="flex items-center gap-3">
			{#if dirty}
				<span class="text-sm text-gray-500 dark:text-gray-400"
					>{$t('auto-update.unsaved-changes')}</span
				>
			{/if}
			<Button onclick={saveSettings} disabled={saving || loading || !dirty}>
				{$t('auto-update.save')}
			</Button>
		</div>
	</div>
</div>
