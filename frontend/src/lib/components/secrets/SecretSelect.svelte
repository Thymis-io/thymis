<script lang="ts">
	import type { SecretType } from '$lib/state';
	import { Select } from 'flowbite-svelte';
	import type { SecretShort } from './secretUtils';
	import { t } from 'svelte-i18n';
	import X from 'lucide-svelte/icons/x';

	interface Props {
		secret: SecretShort | undefined;
		onChange?: (secret: SecretShort | undefined) => void;
		secrets: SecretShort[];
		allowedTypes?: SecretType[];
		placeholder?: string;
		disabled?: boolean;
	}

	let {
		secret = $bindable(undefined),
		onChange,
		secrets,
		allowedTypes = ['single_line', 'multi_line', 'env_list', 'file'],
		placeholder,
		disabled = false
	}: Props = $props();

	let filteredSecrets = $derived(
		secrets
			.filter((secret) => allowedTypes.includes(secret.type))
			.sort((a, b) => a.display_name.localeCompare(b.display_name))
	);

	const selectSecret = (event: Event) => {
		const select = event.target as HTMLSelectElement;
		const selectedId = select.value;
		secret = secrets.find((s) => s.id === selectedId);
		onChange?.(secret);
	};
</script>

<div class="flex gap-2">
	<Select
		value={secret?.id}
		on:change={selectSecret}
		items={filteredSecrets.map((secret) => ({
			name: `${secret.display_name} (${secret.type})`,
			value: secret.id
		}))}
		placeholder={placeholder || $t('secrets.select')}
		{disabled}
		class={`h-8 px-2 py-1 ${disabled ? 'opacity-70' : ''}`}
	/>
	{#if secret}
		<button
			class="m-0 p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600"
			{disabled}
			onclick={() => {
				secret = undefined;
				onChange?.(undefined);
			}}
		>
			<X size="20" />
		</button>
	{/if}
</div>
