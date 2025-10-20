<script lang="ts">
	import { Input, Button, Dropdown, DropdownItem, Tooltip } from 'flowbite-svelte';
	import ClockIcon from 'lucide-svelte/icons/clock';
	import ChevronDownIcon from 'lucide-svelte/icons/chevron-down';
	import CheckCircleIcon from 'lucide-svelte/icons/check-circle';
	import XCircleIcon from 'lucide-svelte/icons/x-circle';
	import { t } from 'svelte-i18n';

	interface Props {
		value?: string;
		onChange?: (newValue: string) => void;
	}

	let { value = $bindable(''), onChange = () => {} }: Props = $props();

	let validationState: 'valid' | 'invalid' | 'pending' | null = $state(null);
	let validationError = $state('');
	let validationResult: string | null = $state(null);
	let debounceTimer: number | null = null;

	const commonTimeSpans = [
		{ label: $t('systemd.timespan.templates.30-seconds'), value: '30s' },
		{ label: $t('systemd.timespan.templates.5-minutes'), value: '5min' },
		{ label: $t('systemd.timespan.templates.30-minutes'), value: '30min' },
		{ label: $t('systemd.timespan.templates.1-hour'), value: '1h' },
		{ label: $t('systemd.timespan.templates.1-hour-30-minutes'), value: '1h 30min' },
		{ label: $t('systemd.timespan.templates.6-hours'), value: '6h' },
		{ label: $t('systemd.timespan.templates.1-day'), value: '1d' },
		{ label: $t('systemd.timespan.templates.1-week'), value: '1w' },
		{ label: $t('systemd.timespan.templates.1-month'), value: '1M' }
	];

	const validateTimeSpan = async (inputValue: string) => {
		if (!inputValue.trim()) {
			validationState = null;
			validationResult = null;
			return;
		}

		validationState = 'pending';
		try {
			const response = await fetch(
				`/api/config/check-systemd-timer?timer_type=timespan&value=${encodeURIComponent(inputValue)}`
			);
			const result = await response.json();

			if (response.ok) {
				validationState = 'valid';
				validationResult = result;
			} else {
				validationState = 'invalid';
				validationError = result.detail || 'Invalid time span';
				validationResult = null;
			}
		} catch {
			validationState = 'invalid';
			validationError = $t('systemd.timespan.tooltip.validation-failed');
			validationResult = null;
		}
	};

	const debouncedValidate = (inputValue: string) => {
		if (debounceTimer) {
			clearTimeout(debounceTimer);
		}
		debounceTimer = setTimeout(() => validateTimeSpan(inputValue), 500);
	};

	const selectTimeSpan = (selectedValue: string) => {
		value = selectedValue;
		onChange(selectedValue);
		validateTimeSpan(selectedValue);
	};

	// Validate when value changes
	$effect(() => {
		debouncedValidate(value);
	});
</script>

<div class="flex gap-2">
	<div class="relative flex-1">
		<Input
			bind:value
			placeholder={$t('systemd.timespan.placeholder')}
			on:input={(e) => onChange(e.target?.value as string)}
			class="flex-1"
		/>
		{#if validationState === 'valid'}
			<CheckCircleIcon
				class="absolute right-2 top-1/2 transform -translate-y-1/2 text-green-500"
				size={16}
				id="timespan-valid-icon"
			/>
			<Tooltip
				triggeredBy="#timespan-valid-icon"
				class="w-64 text-base text-gray-900 dark:text-white"
			>
				{#if validationResult}
					<div class="text-sm">
						<div class="font-medium mb-2">{$t('systemd.timespan.tooltip.parsed-as')}</div>
						<div class="font-mono text-xs">{validationResult}</div>
					</div>
				{/if}
			</Tooltip>
		{:else if validationState === 'invalid'}
			<XCircleIcon
				class="absolute right-2 top-1/2 transform -translate-y-1/2 text-red-500"
				size={16}
				id="timespan-invalid-icon"
			/>
			<Tooltip
				triggeredBy="#timespan-invalid-icon"
				class="w-64 text-base text-gray-900 dark:text-white"
			>
				{validationError}
			</Tooltip>
		{/if}
	</div>
	<Button color="alternative" class="px-3">
		<ClockIcon size={16} />
		<ChevronDownIcon size={16} class="ml-1" />
	</Button>
	<Dropdown class="w-48">
		{#each commonTimeSpans as timeSpan}
			<DropdownItem on:click={() => selectTimeSpan(timeSpan.value)}>
				{timeSpan.label}
			</DropdownItem>
		{/each}
	</Dropdown>
</div>
