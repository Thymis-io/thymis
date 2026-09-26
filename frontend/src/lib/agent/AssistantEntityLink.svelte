<script lang="ts">
	import ListTodo from 'lucide-svelte/icons/list-todo';
	import IdentifierLink from '$lib/IdentifierLink.svelte';
	import type { GlobalState } from '$lib/state.svelte';
	import type { AssistantEntityLink } from './entityLink';

	interface Props {
		globalState: GlobalState;
		entity: AssistantEntityLink;
	}

	let { globalState, entity }: Props = $props();
</script>

{#if entity.entityType === 'configuration'}
	<IdentifierLink
		{globalState}
		identifier={entity.identifier}
		context="config"
		showLinkHover={false}
		iconSize={14}
		class="assistant-entity-link"
	/>
{:else if entity.entityType === 'device'}
	<IdentifierLink
		{globalState}
		identifier={entity.identifier}
		context="device"
		showLinkHover={false}
		iconSize={14}
		class="assistant-entity-link"
	/>
{:else if entity.entityType === 'tag'}
	<IdentifierLink
		{globalState}
		identifier={entity.identifier}
		context="tag"
		showLinkHover={false}
		iconSize={14}
		class="assistant-entity-link"
	/>
{:else}
	<a class="assistant-entity-link" href={`/tasks/${entity.identifier}`}>
		<ListTodo size={14} />
		{entity.label ?? entity.identifier}
	</a>
{/if}

<style>
	.assistant-entity-link :global(a),
	.assistant-entity-link {
		display: inline-flex;
		align-items: center;
		gap: 5px;
		max-width: 100%;
		margin-top: 8px;
		padding: 4px 7px;
		border: 1px solid var(--ds-border);
		border-radius: 6px;
		color: var(--ds-accent-strong);
		background: var(--ds-surface);
		font-size: 12px;
		line-height: 1.3;
		text-decoration: none;
	}

	.assistant-entity-link :global(a:hover),
	.assistant-entity-link:hover {
		background: var(--ds-surface-3);
		text-decoration: underline;
	}
</style>
