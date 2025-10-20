<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Button, Input, Label, Toggle, Tooltip } from 'flowbite-svelte';
	import type { SystemdTimerSetting, SystemdTimerSettingType } from '$lib/state';
	import Dropdown from '$lib/components/Dropdown.svelte';
	import SystemdTimeSpanInput from '$lib/components/SystemdTimeSpanInput.svelte';
	import SystemdCalendarInput from '$lib/components/SystemdCalendarInput.svelte';
	interface Props {
		name: string;
		value?: SystemdTimerSetting | undefined;
		onChange?: (value: SystemdTimerSetting) => void;
		disabled: boolean;
	}

	let { name, value = { timer_type: 'realtime' }, onChange = () => {}, disabled }: Props = $props();

	$effect(() => {
		if (value?.timer_type === 'realtime' && value.on_calendar === undefined) {
			onChange({ ...value, on_calendar: [''] });
		}
	});
</script>

<div class="flex flex-col w-full gap-2 text-base text-gray-900 dark:text-white">
	<Dropdown
		selected={value?.timer_type}
		values={[
			{ value: 'realtime', label: $t('config.timer-type-realtime-long') },
			{ value: 'monotonic', label: $t('config.timer-type-monotonic-long') }
		]}
		onSelected={(timerType: 'realtime' | 'monotonic') => {
			onChange({ ...value, timer_type: timerType });
			return timerType;
		}}
		class="flex-full  w-full"
		innerClass="px-2"
	/>
	{#if value.timer_type === 'realtime'}
		<div>
			<span>{$t('config.timer-on-calendar')}</span>
			<div class="flex flex-col gap-1">
				{#each value.on_calendar as calendar, i}
					<div class="flex gap-2">
						<SystemdCalendarInput
							value={calendar}
							onChange={(newValue) => {
								const newOnCalendar = [...value.on_calendar!];
								newOnCalendar[i] = newValue;
								onChange({ ...value, on_calendar: newOnCalendar });
							}}
						/>
						<Button
							class="w-8"
							color="alternative"
							on:click={() => {
								const newOnCalendar = [...value.on_calendar!];
								newOnCalendar.splice(i, 1);
								onChange({ ...value, on_calendar: newOnCalendar });
							}}
						>
							-
						</Button>
					</div>
				{/each}
				<Button
					class="w-8"
					color="alternative"
					on:click={() => {
						const newOnCalendar = value.on_calendar ? [...value.on_calendar, ''] : [''];
						onChange({ ...value, on_calendar: newOnCalendar });
					}}
				>
					+
				</Button>
			</div>
		</div>
	{:else if value.timer_type === 'monotonic'}
		<div>
			<span>{$t('config.timer-on-boot')}</span>
			<SystemdTimeSpanInput
				value={value.on_boot_sec}
				onChange={(newValue) => onChange({ ...value, on_boot_sec: newValue })}
			/>
			<span>{$t('config.timer-on-unit-active')}</span>
			<SystemdTimeSpanInput
				value={value.on_unit_active_sec}
				onChange={(newValue) => onChange({ ...value, on_unit_active_sec: newValue })}
			/>
		</div>
	{/if}
	{#if disabled}
		<Tooltip type="auto" placement={'top-start'}>{$t('config.editDisabled')}</Tooltip>
	{/if}
</div>
