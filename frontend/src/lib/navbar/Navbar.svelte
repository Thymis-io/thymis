<script lang="ts">
	import { t } from 'svelte-i18n';
	import { page } from '$app/stores';
	import BookOpen from 'lucide-svelte/icons/book-open';
	import Globe from 'lucide-svelte/icons/globe';
	import Menu from 'lucide-svelte/icons/menu';
	import GlobalSearch from './GlobalSearch.svelte';
	import GithubIcon from './GithubIcon.svelte';
	import type { GlobalState } from '$lib/state.svelte';
	import { type DeploymentInfo } from '$lib/deploymentInfo';
	import type { Nav } from '../../routes/(authenticated)/+layout';
	import TaskbarName from '$lib/taskbar/TaskbarName.svelte';
	import type { Task, TaskShort } from '$lib/taskstatus';

	interface Props {
		nav?: Nav;
		globalState?: GlobalState;
		deploymentInfos?: DeploymentInfo[];
		authenticated?: boolean;
		drawerHidden: boolean;
		class?: string;
	}

	let {
		nav,
		globalState,
		deploymentInfos = [],
		authenticated = true,
		drawerHidden = $bindable(),
		class: clazz = ''
	}: Props = $props();

	type Crumb = { label: string; href?: string; task?: TaskShort };

	// Build a breadcrumb trail (parent section + leaf) from the current route so
	// the top bar shows hierarchy instead of just repeating the page title.
	let crumbs = $derived.by<Crumb[]>(() => {
		const path = $page.url.pathname;
		const sections: { prefix: string; label: string; href?: string }[] = [
			{ prefix: '/overview', label: $t('nav.overview') },
			{ prefix: '/configuration', label: $t('nav.configurations'), href: '/configuration/list' },
			{ prefix: '/tags', label: $t('nav.tags') },
			{ prefix: '/devices', label: $t('nav.devices') },
			{ prefix: '/deployment_info', label: $t('nav.devices'), href: '/devices' },
			{ prefix: '/vnc', label: $t('nav.global-vnc') },
			{ prefix: '/tasks', label: $t('nav.tasks') },
			{ prefix: '/history', label: $t('nav.history') },
			{ prefix: '/external-repositories', label: $t('nav.external-repositories') },
			{ prefix: '/secrets', label: $t('nav.secrets') },
			{ prefix: '/artifacts', label: $t('nav.artifacts') },
			{ prefix: '/auto-update', label: $t('nav.auto-update') }
		];
		const section = sections.find((s) => path === s.prefix || path.startsWith(s.prefix + '/'));
		if (!section) return [{ label: $t('nav.overview'), href: '/overview' }];

		const trail: Crumb[] = [{ label: section.label, href: section.href ?? section.prefix }];

		const deviceMatch = path.match(/^\/devices\/([^/]+)/);
		if (deviceMatch) {
			const id = decodeURIComponent(deviceMatch[1]);
			const di = deploymentInfos.find((d) => d.id === id);
			trail.push({ label: di?.name || id });
		} else if (path.startsWith('/configuration/') && path !== '/configuration/list') {
			const name = nav?.selectedConfig?.displayName ?? nav?.selectedTarget?.displayName;
			if (name) trail.push({ label: name });
		} else if (path.startsWith('/deployment_info/')) {
			const segs = path.split('/').filter(Boolean); // [deployment_info, <id>, logs?]
			const id = segs[1] ? decodeURIComponent(segs[1]) : '';
			const di = deploymentInfos.find((d) => d.id === id);
			if (id) trail.push({ label: di?.name || id, href: `/devices/${id}` });
			if (segs[2] === 'logs') trail.push({ label: $t('logs.title') });
		} else if (path.startsWith('/tasks/')) {
			const id = decodeURIComponent(path.split('/').filter(Boolean)[1] ?? '');
			const taskData = ($page.data?.task as Task | undefined) ?? undefined;
			if (taskData && globalState) {
				trail.push({ label: id, task: taskData as TaskShort });
			} else if (id) {
				trail.push({ label: id });
			}
		}
		return trail;
	});
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

	<nav class="breadcrumb" aria-label="Breadcrumb">
		{#each crumbs as crumb, i (i)}
			{#if i > 0}
				<span class="breadcrumb-sep" aria-hidden="true">/</span>
			{/if}
			{#if crumb.href && i < crumbs.length - 1}
				<a href={crumb.href}>{crumb.label}</a>
			{:else if crumb.task && globalState}
				<b aria-current="page" class="crumb-task">
					<TaskbarName {globalState} {deploymentInfos} task={crumb.task} iconSize={15} />
				</b>
			{:else}
				<b aria-current="page">{crumb.label}</b>
			{/if}
		{/each}
	</nav>

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
		min-width: 0;
	}
	.breadcrumb a {
		color: var(--ds-text-dim);
		transition: color 0.12s;
	}
	.breadcrumb a:hover {
		color: var(--ds-text);
		text-decoration: underline;
	}
	.breadcrumb b {
		color: var(--ds-text);
		font-weight: 500;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.breadcrumb b.crumb-task {
		display: inline-flex;
		align-items: center;
		min-width: 0;
		font-weight: 500;
	}
	.breadcrumb-sep {
		color: var(--ds-text-mute);
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
