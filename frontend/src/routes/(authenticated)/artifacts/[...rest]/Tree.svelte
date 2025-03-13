<script lang="ts">
	import { t } from 'svelte-i18n';
	import Tree from './Tree.svelte';
	import type { Artifact, File, Folder } from './+page';
	import ChevronDown from 'lucide-svelte/icons/chevron-down';
	import ChevronRight from 'lucide-svelte/icons/chevron-right';
	import FileIcon from 'lucide-svelte/icons/file';
	import FolderIcon from 'lucide-svelte/icons/folder';
	import { goto, invalidate } from '$app/navigation';

	interface Props {
		artifacts: (Folder | File)[];
		depth?: number;
	}

	let { artifacts, depth = 0 }: Props = $props();

	let hidden = $state<string[]>([]);
	let drag = $state<Artifact>();

	let elementClass =
		'flex items-center gap-1 w-full ' +
		'hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer rounded p-1 text-start whitespace-nowrap overflow-x-hidden text-ellipsis ';

	const dropHandler = async (event: DragEvent) => {
		event.preventDefault();

		if (!drag) {
			return;
		}

		const formData = new FormData();

		for (const file of event.dataTransfer?.files || []) {
			formData.append('files', file);
		}

		let dragPath: string;

		if (drag.type === 'folder') {
			dragPath = drag.path;
		} else {
			dragPath = drag.path.split('/').slice(0, -1).join('/');
		}

		await fetch(`/api/artifacts/${dragPath}`, {
			method: 'POST',
			body: formData
		});

		await invalidate((url) => url.pathname.startsWith('/api/artifacts'));
		drag = undefined;
	};

	const dragOverHandler = (event: DragEvent) => {
		event.preventDefault();
	};

	const dragEnterHandler = (event: DragEvent, artifact: Artifact) => {
		drag = artifact;
	};

	const dragLeaveHandler = (event: DragEvent, artifact: Artifact) => {
		if (drag?.name === artifact?.name) {
			drag = undefined;
		}
	};
</script>

{#each artifacts as artifact}
	{#if artifact.type === 'folder'}
		<button
			class={elementClass +
				'drop-zone ' +
				(drag?.name === artifact?.name ? 'bg-gray-100 dark:bg-gray-700 ' : ' ')}
			onclick={() => {
				hidden = hidden.includes(artifact.name)
					? hidden.filter((a) => a !== artifact.name)
					: [...hidden, artifact.name];
			}}
			ondrop={dropHandler}
			ondragover={dragOverHandler}
			ondragenter={(event) => dragEnterHandler(event, artifact)}
			ondragleave={(event) => dragLeaveHandler(event, artifact)}
		>
			<div class="shrink-0" style="width: {depth * 1.5}rem"></div>
			{#if hidden.includes(artifact.name)}
				<ChevronRight class="w-4 h-4 shrink-0" />
			{:else}
				<ChevronDown class="w-4 h-4 shrink-0" />
			{/if}
			<FolderIcon class="w-4 h-4 shrink-0" />
			<span>{artifact.name}</span>
		</button>
		{#if !hidden.includes(artifact.name)}
			<Tree artifacts={artifact.children} depth={depth + 1} />
		{/if}
	{:else}
		<button
			class={elementClass +
				'drop-zone ' +
				(drag?.name === artifact?.name ? 'bg-gray-100 dark:bg-gray-700 ' : ' ')}
			onclick={() => goto(`/artifacts/${artifact.path}`)}
			ondrop={dropHandler}
			ondragover={dragOverHandler}
			ondragenter={(event) => dragEnterHandler(event, artifact)}
			ondragleave={(event) => dragLeaveHandler(event, artifact)}
		>
			<div class="shrink-0" style="width: {depth * 1.5}rem"></div>
			<div class="w-4 h-4 shrink-0"></div>
			<FileIcon class="w-4 h-4 shrink-0" />
			<span>{artifact.name}</span>
		</button>
	{/if}
{/each}

<style>
	.drop-zone * {
		pointer-events: none;
	}
</style>
