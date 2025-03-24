<script lang="ts">
	import { t } from 'svelte-i18n';
	import Tree from './Tree.svelte';
	import type { Artifact, File, Folder } from './+page';
	import ChevronDown from 'lucide-svelte/icons/chevron-down';
	import ChevronRight from 'lucide-svelte/icons/chevron-right';
	import FileIcon from 'lucide-svelte/icons/file';
	import FolderIcon from 'lucide-svelte/icons/folder';
	import Trash from 'lucide-svelte/icons/trash';
	import { goto, invalidate } from '$app/navigation';
	import DeleteConfirm from '$lib/components/DeleteConfirm.svelte';

	interface Props {
		artifacts: (Folder | File)[];
		depth?: number;
	}

	let { artifacts, depth = 0 }: Props = $props();

	let hidden = $state<string[]>([]);
	let drag = $state<Artifact>();

	let pressedKeys = $state<{ [key: string]: boolean }>({});
	let deleteConfirmTarget = $state<Artifact | undefined>();

	let elementClass =
		'flex items-center gap-1 w-full text-base ' +
		'hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer rounded p-1 text-start whitespace-nowrap ';
	let overflowClass = 'overflow-hidden text-ellipsis ';

	$effect(() => {
		const keydownHandler = (event: KeyboardEvent) => {
			pressedKeys[event.key] = true;
		};

		const keyupHandler = (event: KeyboardEvent) => {
			delete pressedKeys[event.key];
		};

		window.addEventListener('keydown', keydownHandler);
		window.addEventListener('keyup', keyupHandler);

		return () => {
			window.removeEventListener('keydown', keydownHandler);
			window.removeEventListener('keyup', keyupHandler);
		};
	});

	const dropHandler = async (event: DragEvent) => {
		event.preventDefault();

		if (!drag) {
			return;
		}

		const formData = new FormData();

		if (event.dataTransfer?.files?.length === 0) {
			return;
		}

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

	const clickDelete = (e: MouseEvent, artifact: Artifact) => {
		e.stopPropagation();
		e.preventDefault();
		if (pressedKeys['Shift']) {
			deleteArtifact(artifact);
		} else {
			deleteConfirmTarget = artifact;
		}
	};

	const deleteArtifact = async (artifact: Artifact) => {
		await fetch(`/api/artifacts/${artifact.path}`, {
			method: 'DELETE'
		});

		await invalidate((url) => url.pathname.startsWith('/api/artifacts'));
	};
</script>

<DeleteConfirm
	target={deleteConfirmTarget?.name}
	description={$t('deleteConfirm.text', { values: { target: deleteConfirmTarget?.path } })}
	on:cancel={() => (deleteConfirmTarget = undefined)}
	on:confirm={() => deleteConfirmTarget && deleteArtifact(deleteConfirmTarget)}
/>
{#each artifacts as artifact}
	{#if artifact.type === 'folder'}
		<div
			role="button"
			tabindex="0"
			class={elementClass +
				'drop-zone hover-visible-parent ' +
				(drag?.name === artifact?.name ? 'bg-gray-100 dark:bg-gray-700 ' : ' ')}
			onclick={() => {
				hidden = hidden.includes(artifact.name)
					? hidden.filter((a) => a !== artifact.name)
					: [...hidden, artifact.name];
			}}
			onkeydown={(event) => {
				if (event.key === 'Enter') {
					hidden = hidden.includes(artifact.name)
						? hidden.filter((a) => a !== artifact.name)
						: [...hidden, artifact.name];
				}
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
			<span class={overflowClass}>{artifact.name}</span>
			<button
				class={'ml-auto hover-visible-child rounded bg-gray-100 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-500 ' +
					(pressedKeys['Shift'] ? 'text-red-500 ' : '')}
				onclick={(e) => clickDelete(e, artifact)}
			>
				<Trash size="20" />
			</button>
		</div>
		{#if !hidden.includes(artifact.name)}
			<Tree artifacts={artifact.children} depth={depth + 1} />
		{/if}
	{:else}
		<div
			role="button"
			tabindex="0"
			class={elementClass +
				'drop-zone hover-visible-parent ' +
				(drag?.name === artifact?.name ? 'bg-gray-100 dark:bg-gray-700 ' : ' ')}
			onclick={() => goto(`/artifacts/${artifact.path}`)}
			onkeydown={(event) => {
				if (event.key === 'Enter') {
					goto(`/artifacts/${artifact.path}`);
				}
			}}
			ondrop={dropHandler}
			ondragover={dragOverHandler}
			ondragenter={(event) => dragEnterHandler(event, artifact)}
			ondragleave={(event) => dragLeaveHandler(event, artifact)}
		>
			<div class="shrink-0" style="width: {depth * 1.5}rem"></div>
			<div class="w-4 h-4 shrink-0"></div>
			<FileIcon class="w-4 h-4 shrink-0" />
			<span class={overflowClass}>{artifact.name}</span>
			<button
				class={'ml-auto hover-visible-child rounded bg-gray-100 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-500 ' +
					(pressedKeys['Shift'] ? 'text-red-500 ' : '')}
				onclick={(e) => clickDelete(e, artifact)}
			>
				<Trash size="18" />
			</button>
		</div>
	{/if}
{/each}

<style>
	.drop-zone * {
		pointer-events: none;
	}

	.hover-visible-parent > .hover-visible-child {
		display: none;
	}

	.hover-visible-parent:hover > .hover-visible-child {
		display: block;
		pointer-events: auto;
	}
</style>
