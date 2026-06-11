<script lang="ts">
	import { afterNavigate } from '$app/navigation';
	import { page } from '$app/stores';
	import { t, locale } from 'svelte-i18n';
	import { DarkMode, Popover } from 'flowbite-svelte';
	import ChartBar from 'lucide-svelte/icons/chart-bar';
	import Server from 'lucide-svelte/icons/server';
	import GitBranch from 'lucide-svelte/icons/git-graph';
	import ScreenShare from 'lucide-svelte/icons/screen-share';
	import TagIcon from 'lucide-svelte/icons/tag';
	import FileCode from 'lucide-svelte/icons/file-code-2';
	import FileLock from 'lucide-svelte/icons/file-lock-2';
	import FolderOpen from 'lucide-svelte/icons/folder-open';
	import FolderGit2 from 'lucide-svelte/icons/folder-git-2';
	import RefreshCcwDot from 'lucide-svelte/icons/refresh-ccw-dot';
	import Logout from 'lucide-svelte/icons/log-out';
	import type { GlobalState } from '$lib/state.svelte';
	import { targetShouldShowVNC } from '$lib/vnc/vnc';
	import LanguageSelect from '$lib/navbar/LanguageSelect.svelte';

	interface Props {
		globalState: GlobalState;
		drawerHidden: boolean;
		asideClass?: string;
	}

	let { globalState, drawerHidden = $bindable(), asideClass = '' }: Props = $props();

	const closeDrawer = () => {
		drawerHidden = true;
	};

	let activeUrl: string = $state($page.url.pathname);

	afterNavigate((navigation) => {
		// this fixes https://github.com/themesberg/flowbite-svelte/issues/364
		document.getElementById('svelte')?.scrollTo({ top: 0 });
		closeDrawer();
		activeUrl = navigation.to?.url.pathname ?? '';
	});

	const isActive = (href: string) => activeUrl === href || activeUrl.startsWith(href + '/');

	type NavItem = {
		name: string;
		icon: any;
		href: string;
		hidden?: boolean;
		badge?: string | number;
		badgeDanger?: boolean;
	};

	type NavSection = {
		title: string;
		items: NavItem[];
	};

	let anyTargetHasVNC = $derived(
		globalState.configs.some((config) => targetShouldShowVNC(config, globalState)) ||
			globalState.tags.some((tag) => targetShouldShowVNC(tag, globalState))
	);

	let sections: NavSection[] = $derived([
		{
			title: $t('nav.overview'),
			items: [
				{ name: $t('nav.overview'), icon: ChartBar, href: '/overview' },
				{
					name: $t('nav.configurations'),
					icon: FileCode,
					href: '/configuration/list',
					badge: globalState.configs.length
				},
				{
					name: $t('nav.tags'),
					icon: TagIcon,
					href: '/tags',
					badge: globalState.tags.length
				},
				{ name: $t('nav.devices'), icon: Server, href: '/devices' },
				{
					name: $t('nav.global-vnc'),
					icon: ScreenShare,
					href: '/vnc',
					hidden: !anyTargetHasVNC
				},
				{ name: $t('nav.history'), icon: GitBranch, href: '/history' }
			]
		},
		{
			title: $t('nav.data'),
			items: [
				{ name: $t('nav.secrets'), icon: FileLock, href: '/secrets' },
				{ name: $t('nav.artifacts'), icon: FolderOpen, href: '/artifacts' }
			]
		},
		{
			title: $t('nav.settings'),
			items: [
				{
					name: $t('nav.external-repositories'),
					icon: FolderGit2,
					href: '/external-repositories'
				},
				{ name: $t('nav.auto-update'), icon: RefreshCcwDot, href: '/auto-update' }
			]
		}
	]);
</script>

<aside class="ds-sidebar {drawerHidden ? 'drawer-hidden' : ''} {asideClass}">
	<div class="brand">
		<a href="/" class="brand-link" aria-label="Thymis Home">
			<img src="/favicon.png" class="brand-mark" alt="Thymis Logo" />
			<span class="brand-name">Thymis</span>
		</a>
	</div>

	<nav class="nav">
		{#each sections as section (section.title)}
			<div class="nav-section">
				<div class="nav-section-title">{section.title}</div>
				{#each section.items as item (item.name)}
					{#if !item.hidden}
						{@const Icon = item.icon}
						<a
							href={item.href}
							lang={$locale}
							class="nav-item {isActive(item.href) ? 'active' : ''}"
						>
							<Icon size={16} />
							<span class="nav-label">{item.name}</span>
							{#if item.badge !== undefined}
								<span class="nav-badge {item.badgeDanger ? 'danger' : ''}">{item.badge}</span>
							{/if}
						</a>
					{/if}
				{/each}
			</div>
		{/each}
	</nav>

	<div class="sidebar-footer">
		<button class="user-trigger" id="sidebar-user-trigger" aria-label="User menu">
			<span class="avatar">A</span>
			<span class="user-info">
				<span class="user-name">Admin</span>
				<span class="user-email">{$t('common.logout')}</span>
			</span>
		</button>
		<DarkMode class="ds-icon-btn" />
	</div>
	<Popover
		triggeredBy="#sidebar-user-trigger"
		arrow={false}
		trigger="click"
		placement="top"
		class="z-50"
	>
		<div class="flex flex-col gap-2 p-2">
			<div class="flex items-center justify-center w-max">
				<LanguageSelect />
			</div>
			<a
				href="/auth/logout"
				class="flex p-2 gap-2 items-center rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600"
			>
				<Logout size={18} />
				{$t('common.logout')}
			</a>
		</div>
	</Popover>
</aside>

<style lang="postcss">
	.ds-sidebar {
		width: 232px;
		background: var(--ds-surface);
		border-right: 1px solid var(--ds-border);
		display: flex;
		flex-direction: column;
		overflow: hidden;
		height: 100%;
	}

	/* ---- Brand ---- */
	.brand {
		padding: 16px 18px 12px;
		display: flex;
		align-items: center;
	}
	.brand-link {
		display: flex;
		align-items: center;
		gap: 10px;
	}
	.brand-mark {
		width: 28px;
		height: 28px;
		min-width: 28px;
		object-fit: contain;
		display: block;
	}
	.brand-name {
		font-weight: 600;
		font-size: 15px;
		letter-spacing: -0.01em;
		color: var(--ds-text);
	}

	/* ---- Nav ---- */
	.nav {
		flex: 1;
		overflow-y: auto;
		padding: 4px 10px 10px;
	}
	.nav-section {
		margin-top: 14px;
	}
	.nav-section-title {
		padding: 0 8px 6px;
		font-size: 10.5px;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.07em;
		color: var(--ds-text-mute);
	}
	.nav-item {
		display: flex;
		align-items: center;
		gap: 10px;
		padding: 7px 9px;
		margin: 1px 0;
		border-radius: 7px;
		color: var(--ds-text-dim);
		font-size: 13.5px;
		cursor: pointer;
		transition:
			background 0.12s,
			color 0.12s;
	}
	.nav-item:hover {
		background: var(--ds-surface-2);
		color: var(--ds-text);
	}
	.dark .nav-item:hover {
		background: var(--ds-surface-2);
	}
	.nav-item.active {
		background: var(--ds-accent-dim);
		color: var(--ds-accent-strong);
		font-weight: 500;
	}
	.nav-item :global(svg) {
		width: 16px;
		height: 16px;
		flex-shrink: 0;
	}
	.nav-label {
		min-width: 0;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
	.nav-badge {
		margin-left: auto;
		font-size: 11px;
		padding: 1px 6px;
		border-radius: 999px;
		background: var(--ds-surface-3);
		color: var(--ds-text-dim);
	}
	.nav-item.active .nav-badge {
		background: var(--ds-accent-dim);
		color: var(--ds-accent-strong);
	}
	.nav-badge.danger {
		background: var(--ds-danger-dim);
		color: var(--ds-danger);
	}

	/* ---- Footer ---- */
	.sidebar-footer {
		border-top: 1px solid var(--ds-border);
		padding: 10px 12px;
		display: flex;
		align-items: center;
		gap: 10px;
	}
	.user-trigger {
		display: flex;
		align-items: center;
		gap: 10px;
		flex: 1;
		min-width: 0;
		padding: 2px;
		border-radius: 8px;
		text-align: left;
	}
	.user-trigger:hover {
		background: var(--ds-surface-2);
	}
	.avatar {
		width: 28px;
		height: 28px;
		border-radius: 50%;
		background: linear-gradient(135deg, #4f8cff, #8a4fff);
		display: grid;
		place-items: center;
		color: #fff;
		font-weight: 600;
		font-size: 12px;
		flex-shrink: 0;
	}
	.user-info {
		display: flex;
		flex-direction: column;
		min-width: 0;
		line-height: 1.2;
	}
	.user-name {
		font-size: 13px;
		font-weight: 500;
		color: var(--ds-text);
	}
	.user-email {
		font-size: 11px;
		color: var(--ds-text-mute);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.sidebar-footer :global(.ds-icon-btn) {
		width: 30px;
		height: 30px;
		display: grid;
		place-items: center;
		border-radius: 6px;
		color: var(--ds-text-dim);
		flex-shrink: 0;
	}
	.sidebar-footer :global(.ds-icon-btn:hover) {
		background: var(--ds-surface-2);
		color: var(--ds-text);
	}

	/* ---- Mobile drawer ---- */
	@media (max-width: 1023px) {
		.ds-sidebar {
			position: fixed;
			top: 0;
			left: 0;
			bottom: 0;
			z-index: 60;
			box-shadow: var(--ds-shadow-lg);
			transition: transform 0.2s ease;
		}
		.ds-sidebar.drawer-hidden {
			transform: translateX(-100%);
		}
	}
</style>
