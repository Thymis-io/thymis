<script lang="ts">
	import { t } from 'svelte-i18n';
	import { page } from '$app/stores';
	import BookOpen from 'lucide-svelte/icons/book-open';
	import Globe from 'lucide-svelte/icons/globe';
	import Menu from 'lucide-svelte/icons/menu';
	import GlobalSearch from './GlobalSearch.svelte';
	import GithubIcon from './GithubIcon.svelte';
	import type { GlobalState } from '$lib/state.svelte';
	import type { Nav } from '../../routes/(authenticated)/+layout';

	interface Props {
		nav?: Nav;
		globalState?: GlobalState;
		authenticated?: boolean;
		drawerHidden: boolean;
		class?: string;
	}

	let {
		nav,
		globalState,
		authenticated = true,
		drawerHidden = $bindable(),
		class: clazz = ''
	}: Props = $props();

	// Map the current route to a readable breadcrumb label.
	const titleFor = (path: string): string => {
		const map: [string, string][] = [
			['/overview', $t('nav.overview')],
			['/configuration/list', $t('nav.configurations')],
			['/configuration', $t('nav.configure')],
			['/tags', $t('nav.tags')],
			['/devices', $t('nav.devices')],
			['/vnc', $t('nav.global-vnc')],
			['/history', $t('nav.history')],
			['/external-repositories', $t('nav.external-repositories')],
			['/secrets', $t('nav.secrets')],
			['/artifacts', $t('nav.artifacts')],
			['/auto-update', $t('nav.auto-update')]
		];
		for (const [prefix, label] of map) {
			if (path === prefix || path.startsWith(prefix + '/')) return label;
		}
		return $t('nav.overview');
	};

	let pageTitle = $derived(titleFor($page.url.pathname));
</script>

<div class="ds-topbar {clazz || ''}">
	{#if authenticated}
		<button
			class="ds-icon-btn ds-hamburger"
			aria-label="Toggle navigation"
			onclick={() => (drawerHidden = !drawerHidden)}
		>
			<Menu size={18} />
		</button>
	{/if}

	<div class="breadcrumb">
		<b>{pageTitle}</b>
	</div>

	{#if authenticated && globalState && nav}
		<div class="search-wrap">
			<GlobalSearch {globalState} {nav} />
		</div>
	{/if}

	<div class="topbar-actions">
		<a
			class="ds-icon-btn"
			href="https://thymis.io/"
			aria-label="Thymis Website"
			title={$t('common.website')}
		>
			<Globe size={18} />
		</a>
		<a
			class="ds-icon-btn"
			href="https://thymis.io/docs/"
			aria-label="Thymis Documentation"
			title={$t('common.documentation')}
		>
			<BookOpen size={18} />
		</a>
		<a
			class="ds-icon-btn"
			href="https://github.com/thymis-io/thymis"
			aria-label="Star Thymis on GitHub"
			title={$t('common.github')}
		>
			<GithubIcon />
		</a>
	</div>
</div>

<style lang="postcss">
	.ds-topbar {
		height: var(--navbar-height);
		border-bottom: 1px solid var(--ds-border);
		background: var(--ds-surface);
		display: flex;
		align-items: center;
		gap: 12px;
		padding: 0 16px;
		flex-shrink: 0;
	}
	.breadcrumb {
		display: flex;
		align-items: center;
		gap: 8px;
		font-size: 13.5px;
		color: var(--ds-text-dim);
		flex-shrink: 0;
	}
	.breadcrumb b {
		color: var(--ds-text);
		font-weight: 500;
	}
	.search-wrap {
		margin-left: auto;
		min-width: 0;
		flex: 1;
		max-width: 360px;
		display: flex;
		justify-content: flex-end;
	}
	.topbar-actions {
		display: flex;
		align-items: center;
		gap: 2px;
		flex-shrink: 0;
	}
	.ds-icon-btn {
		width: 32px;
		height: 32px;
		display: grid;
		place-items: center;
		border-radius: 7px;
		color: var(--ds-text-dim);
		transition:
			background 0.12s,
			color 0.12s;
	}
	.ds-icon-btn:hover {
		background: var(--ds-surface-2);
		color: var(--ds-text);
	}
	.dark .ds-icon-btn:hover {
		background: var(--ds-surface-3);
	}
	@media (min-width: 1024px) {
		.ds-hamburger {
			display: none;
		}
	}
</style>
