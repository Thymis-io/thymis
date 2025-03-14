<script lang="ts">
	import ArtifactTreeOptions from './ArtifactTreeOptions.svelte';
	import type { Artifact } from '../../routes/(authenticated)/artifacts/[...rest]/+page';
	import FileIcon from 'lucide-svelte/icons/file';
	import FolderIcon from 'lucide-svelte/icons/folder';

	interface Props {
		artifacts: Artifact[];
		onSelect: (artifact: Artifact) => void;
		depth?: number;
	}

	let { artifacts, onSelect, depth = 0 }: Props = $props();
</script>

{#each artifacts as artifact}
	<option
		value={artifact.path}
		class="flex items-center gap-1 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600"
		style="padding-left: {0.5 + depth * 1.5}rem;"
		onclick={() => onSelect(artifact)}
	>
		{#if artifact.type === 'folder'}
			<FolderIcon class="w-4 h-4" />
		{:else}
			<FileIcon class="w-4 h-4" />
		{/if}
		{artifact.name}
	</option>
	{#if artifact.type === 'folder'}
		<ArtifactTreeOptions artifacts={artifact.children} {onSelect} depth={depth + 1} />
	{/if}
{/each}
