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
	let drop = $state<Artifact>();
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

		try {
			if (!drop) {
				return;
			}

			let dragPath: string;

			if (drop.type === 'folder') {
				dragPath = drop.path;
			} else {
				dragPath = drop.path.split('/').slice(0, -1).join('/');
			}

			if (event.dataTransfer?.files && event.dataTransfer.files.length > 0) {
				const formData = new FormData();

				for (const file of event.dataTransfer?.files || []) {
					formData.append('files', file);
				}

				await fetch(`/api/artifacts/upload/${dragPath}`, {
					method: 'POST',
					body: formData
				});
			} else if (event.dataTransfer?.items !== undefined && event.dataTransfer.items.length > 0) {
				if (
					event.dataTransfer.items.length !== 1 ||
					event.dataTransfer.items[0].type !== 'text/plain'
				) {
					return;
				}

				event.dataTransfer.items[0].getAsString((artifact) => {
					const data = JSON.parse(artifact);
					fetch(`/api/artifacts/move/${dragPath}`, {
						method: 'POST',
						headers: {
							'Content-Type': 'application/json'
						},
						body: JSON.stringify(data)
					});
				});
			}
		} finally {
			drop = undefined;
			drag = undefined;
		}
	};

	const dragStartHandler = (event: DragEvent, artifact: Artifact) => {
		drag = artifact;

		if (event.dataTransfer) {
			event.dataTransfer.setData('text/plain', JSON.stringify({ artifact: artifact.path }));
			event.dataTransfer.dropEffect = 'move';
		}
	};

	const dragOverHandler = (event: DragEvent) => {
		event.preventDefault();
	};

	const dragEnterHandler = (event: DragEvent, artifact: Artifact) => {
		drop = artifact;
	};

	const dragLeaveHandler = (event: DragEvent, artifact: Artifact) => {
		if (drop?.name === artifact?.name) {
			drop = undefined;
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
				(drop?.name === artifact?.name ? 'bg-gray-100 dark:bg-gray-700 ' : ' ')}
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
			draggable="true"
			ondragstart={(event) => dragStartHandler(event, artifact)}
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
					(pressedKeys['Shift'] ? 'text-red-500 ' : ' ') +
					(drag?.path === artifact.path ? '!hidden ' : '')}
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
				(drop?.name === artifact?.name ? 'bg-gray-100 dark:bg-gray-700 ' : ' ')}
			onclick={() => goto(`/artifacts/${artifact.path}`)}
			onkeydown={(event) => {
				if (event.key === 'Enter') {
					goto(`/artifacts/${artifact.path}`);
				}
			}}
			draggable="true"
			ondragstart={(event) => dragStartHandler(event, artifact)}
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
					(pressedKeys['Shift'] ? 'text-red-500 ' : ' ') +
					(drag?.path === artifact.path ? '!hidden ' : '')}
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
