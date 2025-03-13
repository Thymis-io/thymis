<script lang="ts">
	import { t } from 'svelte-i18n';
	import PageHead from '$lib/components/layout/PageHead.svelte';
	import type { PageData } from './$types';
	import Tree from './Tree.svelte';
	import SplitPane from '$lib/splitpane/SplitPane.svelte';
	import MonospaceText from '$lib/components/MonospaceText.svelte';
	import { invalidate } from '$app/navigation';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	const dropHandler = async (event: DragEvent) => {
		event.preventDefault();

		const formData = new FormData();

		for (const file of event.dataTransfer?.files || []) {
			formData.append('files', file);
		}

		await fetch(`/api/artifacts/`, {
			method: 'POST',
			body: formData
		});

		await invalidate((url) => url.pathname.startsWith('/api/artifacts'));
	};

	const dragOverHandler = (event: DragEvent) => {
		event.preventDefault();
	};
</script>

<PageHead
	title={$t('nav.artifacts')}
	repoStatus={data.repoStatus}
	globalState={data.globalState}
	nav={data.nav}
/>

<div>
	<SplitPane type="horizontal" pos="16rem" min="12rem" max="80%">
		{#snippet a()}
			<div
				class="rounded bg-gray-100 dark:bg-gray-800"
				role="button"
				tabindex="0"
				ondrop={dropHandler}
				ondragover={dragOverHandler}
			>
				<Tree artifacts={data.artifacts} />
				<div class="p-4 text-center text-gray-500 dark:text-gray-400">
					{$t('artifacts.drag_drop')}
				</div>
			</div>
		{/snippet}
		{#snippet b()}
			<div class="p-4">
				{#if data.selectedArtifact}
					{#if data.selectedArtifact.mediaType?.startsWith('image/')}
						<img
							src={`/api/artifacts/${data.selectedArtifact.path}`}
							alt={data.selectedArtifact.path}
						/>
					{:else if data.selectedArtifact.mediaType?.startsWith('text/')}
						<MonospaceText code={data.selectedArtifact.text} />
					{:else}
						<pre>{data.selectedArtifact.mediaType}</pre>
					{/if}
				{/if}
			</div>
		{/snippet}
	</SplitPane>
</div>
