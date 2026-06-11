<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { SystemdTimerSetting } from '$lib/state';
	import Dropdown from '$lib/components/Dropdown.svelte';
	import SystemdTimeSpanInput from '$lib/components/SystemdTimeSpanInput.svelte';
	import SystemdCalendarInput from '$lib/components/SystemdCalendarInput.svelte';
	import ConfigBool from './ConfigBool.svelte';
	import X from 'lucide-svelte/icons/x';
	import Plus from 'lucide-svelte/icons/plus';

	interface Props {
		key: string;
		value?: SystemdTimerSetting | undefined;
		onChange?: (value: SystemdTimerSetting) => void;
		disabled: boolean;
	}

	let { key, value = { timer_type: 'realtime' }, onChange = () => {}, disabled }: Props = $props();

	$effect(() => {
		if (value?.timer_type === 'realtime' && value.on_calendar === undefined) {
			onChange({ ...value, on_calendar: [''] });
		}
	});
</script>

<div
	class="flex w-full max-w-full flex-col gap-4 rounded-lg border border-[var(--ds-border)] bg-[var(--ds-surface-2)] p-4 text-[var(--ds-text)]"
>
	<div class="flex flex-col gap-2">
		<span id="{key}-timer-type" class="ds-form-label">{$t('config.timer-type')}</span>
		<Dropdown
			selected={value?.timer_type}
			values={[
				{ value: 'realtime', label: $t('config.timer-type-realtime-long') },
				{ value: 'monotonic', label: $t('config.timer-type-monotonic-long') },
				{ value: 'continuous', label: $t('config.timer-type-continuous-long') }
			]}
			onSelected={(timerType: 'realtime' | 'monotonic' | 'continuous') => {
				onChange({ ...value, timer_type: timerType });
				return timerType;
			}}
			{disabled}
			class="w-full"
			innerClass="px-2"
		/>
	</div>
	{#if value.timer_type === 'realtime'}
		<div class="flex flex-col gap-2">
			<span class="ds-form-label">{$t('config.timer-on-calendar')}</span>
			<div class="flex flex-col gap-2">
				{#each value.on_calendar as calendar, i}
					<div class="flex items-center gap-2">
						<div class="flex-1">
							<SystemdCalendarInput
								value={calendar}
								onChange={(newValue) => {
									const newOnCalendar = [...value.on_calendar!];
									newOnCalendar[i] = newValue;
									onChange({ ...value, on_calendar: newOnCalendar });
								}}
								{disabled}
							/>
						</div>
						<button
							class="ds-icon-btn"
							onclick={() => {
								const newOnCalendar = [...value.on_calendar!];
								newOnCalendar.splice(i, 1);
								onChange({ ...value, on_calendar: newOnCalendar });
							}}
							{disabled}
							aria-label={$t('config.remove_list_element')}
						>
							<X size={18} />
						</button>
					</div>
				{/each}
				<button
					class="flex w-full items-center justify-center gap-2 rounded-lg border border-dashed border-[var(--ds-border-strong)] p-2 text-sm font-medium text-[var(--ds-text-dim)] transition-colors hover:border-[var(--ds-accent)] hover:bg-[var(--ds-accent-dim)] hover:text-[var(--ds-accent-strong)] disabled:cursor-not-allowed disabled:opacity-50"
					onclick={() => {
						const newOnCalendar = value.on_calendar ? [...value.on_calendar, ''] : [''];
						onChange({ ...value, on_calendar: newOnCalendar });
					}}
					{disabled}
				>
					<Plus size={18} />
					{$t('config.add_list_element')}
				</button>
			</div>
		</div>
		<div class="flex flex-col gap-2">
			<span id="{key}-timer-persistent" class="ds-form-label">{$t('config.timer-persistent')}</span>
			<ConfigBool
				name="persistent"
				aria-labelledby="{key}-timer-persistent"
				value={value.persistent}
				onChange={(newValue) => onChange({ ...value, persistent: newValue })}
				{disabled}
			/>
		</div>
	{:else if value.timer_type === 'monotonic'}
		<div class="flex flex-col gap-2">
			<span id="{key}-timer-on-boot" class="ds-form-label">{$t('config.timer-on-boot')}</span>
			<SystemdTimeSpanInput
				aria-labelledby="{key}-timer-on-boot"
				value={value.on_boot_sec}
				onChange={(newValue) => onChange({ ...value, on_boot_sec: newValue })}
				{disabled}
			/>
		</div>
		<div class="flex flex-col gap-2">
			<span id="{key}-timer-on-unit-active" class="ds-form-label"
				>{$t('config.timer-on-unit-active')}</span
			>
			<SystemdTimeSpanInput
				aria-labelledby="{key}-timer-on-unit-active"
				value={value.on_unit_active_sec}
				onChange={(newValue) => onChange({ ...value, on_unit_active_sec: newValue })}
				{disabled}
			/>
		</div>
	{:else if value.timer_type === 'continuous'}
		<p class="ds-form-hint">{$t('config.timer-type-continuous-description')}</p>
	{/if}
	{#if value.timer_type !== 'continuous'}
		<div class="flex flex-col gap-2">
			<span id="{key}-timer-accuracy-sec" class="ds-form-label"
				>{$t('config.timer-accuracy-sec')}</span
			>
			<SystemdTimeSpanInput
				aria-labelledby="{key}-timer-accuracy-sec"
				value={value.accuracy_sec}
				placeholder="1min"
				onChange={(newValue) => onChange({ ...value, accuracy_sec: newValue })}
				{disabled}
			/>
		</div>
		<div class="flex flex-col gap-2">
			<span id="{key}-timer-randomized-delay-sec" class="ds-form-label"
				>{$t('config.timer-randomized-delay-sec')}</span
			>
			<SystemdTimeSpanInput
				aria-labelledby="{key}-timer-randomized-delay-sec"
				value={value.randomized_delay_sec}
				onChange={(newValue) => onChange({ ...value, randomized_delay_sec: newValue })}
				{disabled}
			/>
		</div>
	{/if}
</div>
