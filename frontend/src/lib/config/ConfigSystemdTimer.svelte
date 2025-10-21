<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Button, Card } from 'flowbite-svelte';
	import type { SystemdTimerSetting } from '$lib/state';
	import Dropdown from '$lib/components/Dropdown.svelte';
	import SystemdTimeSpanInput from '$lib/components/SystemdTimeSpanInput.svelte';
	import SystemdCalendarInput from '$lib/components/SystemdCalendarInput.svelte';
	import ConfigBool from './ConfigBool.svelte';
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

<Card
	class="flex flex-col w-full max-w-full drop-shadow z-10 gap-1 text-base text-gray-900 dark:text-white"
>
	<p>{$t('config.timer-type')}</p>
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
		{disabled}
		class="flex-full w-full mb-2"
		innerClass="px-2"
	/>
	{#if value.timer_type === 'realtime'}
		<p>{$t('config.timer-on-calendar')}</p>
		<div class="flex flex-col gap-1 mb-2">
			{#each value.on_calendar as calendar, i}
				<div class="flex gap-2">
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
					<Button
						class="w-8"
						color="alternative"
						on:click={() => {
							const newOnCalendar = [...value.on_calendar!];
							newOnCalendar.splice(i, 1);
							onChange({ ...value, on_calendar: newOnCalendar });
						}}
						{disabled}
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
				{disabled}
			>
				+
			</Button>
		</div>
		<p>{$t('config.timer-persistent')}</p>
		<ConfigBool
			name="persistent"
			value={value.persistent}
			onChange={(newValue) => onChange({ ...value, persistent: newValue })}
			{disabled}
		/>
	{:else if value.timer_type === 'monotonic'}
		<p>{$t('config.timer-on-boot')}</p>
		<SystemdTimeSpanInput
			class="mb-2"
			value={value.on_boot_sec}
			onChange={(newValue) => onChange({ ...value, on_boot_sec: newValue })}
			{disabled}
		/>
		<p>{$t('config.timer-on-unit-active')}</p>
		<SystemdTimeSpanInput
			class="mb-2"
			value={value.on_unit_active_sec}
			onChange={(newValue) => onChange({ ...value, on_unit_active_sec: newValue })}
			{disabled}
		/>
	{/if}
	<p>{$t('config.timer-accuracy-sec')}</p>
	<SystemdTimeSpanInput
		class="mb-2"
		value={value.accuracy_sec}
		placeholder="1min"
		onChange={(newValue) => onChange({ ...value, accuracy_sec: newValue })}
		{disabled}
	/>
	<p>{$t('config.timer-randomized-delay-sec')}</p>
	<SystemdTimeSpanInput
		value={value.randomized_delay_sec}
		onChange={(newValue) => onChange({ ...value, randomized_delay_sec: newValue })}
		{disabled}
	/>
</Card>
