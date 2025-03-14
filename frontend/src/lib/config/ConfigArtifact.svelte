<script lang="ts">
	import Dropdown from '$lib/components/Dropdown.svelte';
	import type { ArtifactSettingType, Setting } from '$lib/state';
	import type { Artifact } from '../../routes/(authenticated)/artifacts/[...rest]/+page';
	import ArtifactTreeOptions from './ArtifactTreeOptions.svelte';

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
		<ArtifactTreeOptions
			{artifacts}
			onSelect={(artifact) => {
				console.log(artifact.path);
				onChange?.(artifact.path);
			}}
		/>
	{/snippet}
</Dropdown>
