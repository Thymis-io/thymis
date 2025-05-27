<script lang="ts">
	import Dropdown from '$lib/components/Dropdown.svelte';
	import type { ArtifactSettingType, Setting } from '$lib/state';
	import type { Artifact } from '../../routes/(authenticated)/artifacts/[...rest]/+page';
	import FileIcon from 'lucide-svelte/icons/file';

	interface Props {
		value?: string | null;
		placeholder?: string | undefined;
		disabled?: boolean;
		setting: Setting<ArtifactSettingType>;
		onChange?: (value: string | null) => void;
		artifacts: Artifact[];
	}

	let { value, placeholder, disabled = false, setting, onChange, artifacts }: Props = $props();
</script>

<Dropdown
	values={[]}
	selected={value}
	{disabled}
	showBox={true}
	onSelected={(selectedValue) => onChange?.(selectedValue)}
	class="min-w-10 text-base"
	innerClass="px-2 py-1"
>
	{#snippet options()}
		{#each artifacts as artifact}
			<option
				value={artifact.name}
				class="flex items-center px-1 gap-1 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600"
				onclick={() => onChange?.(artifact.name)}
			>
				<FileIcon class="w-4 h-4 shrink-0" />
				{artifact.name}
			</option>
		{/each}
	{/snippet}
</Dropdown>
