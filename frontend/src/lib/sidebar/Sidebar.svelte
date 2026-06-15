<script lang="ts">
	import { afterNavigate } from '$app/navigation';
	import { page } from '$app/stores';
	import { t, locale } from 'svelte-i18n';
	import { DarkMode, Popover } from 'flowbite-svelte';
	import ChartBar from 'lucide-svelte/icons/chart-bar';
	import Server from 'lucide-svelte/icons/server';
	import GitBranch from 'lucide-svelte/icons/git-graph';
	import ListChecks from 'lucide-svelte/icons/list-checks';
	import ScreenShare from 'lucide-svelte/icons/screen-share';
	import TagIcon from 'lucide-svelte/icons/tag';
	import FileCode from 'lucide-svelte/icons/file-code-2';
	import FileLock from 'lucide-svelte/icons/file-lock-2';
	import FolderOpen from 'lucide-svelte/icons/folder-open';
	import FolderGit2 from 'lucide-svelte/icons/folder-git-2';
	import RefreshCcwDot from 'lucide-svelte/icons/refresh-ccw-dot';
	import Logout from 'lucide-svelte/icons/log-out';
	import ChevronUp from 'lucide-svelte/icons/chevron-up';
	import type { GlobalState } from '$lib/state.svelte';
	import { targetShouldShowVNC } from '$lib/vnc/vnc';
	import { type DeploymentInfo } from '$lib/deploymentInfo';
	import LanguageSelect from '$lib/navbar/LanguageSelect.svelte';

	type UserInfo = {
		username?: string | null;
		given_name?: string | null;
		family_name?: string | null;
		email?: string | null;
	};

	interface Props {
		globalState: GlobalState;
		deploymentInfos?: DeploymentInfo[];
		user?: UserInfo | null;
		drawerHidden: boolean;
		asideClass?: string;
	}

	let {
		globalState,
		deploymentInfos = [],
		user = null,
		drawerHidden = $bindable(),
		asideClass = ''
	}: Props = $props();

	let userName = $derived(
		[user?.given_name, user?.family_name].filter(Boolean).join(' ') ||
			user?.username ||
			$t('common.administrator')
	);
	let userSubtitle = $derived(user?.email ?? $t('common.administrator'));
	let userInitial = $derived(userName.trim().charAt(0).toUpperCase() || 'U');

	const closeDrawer = () => {
		drawerHidden = true;
	};

	let activeUrl: string = $state($page.url.pathname);
	// Config and tag detail pages share the /configuration/* routes and are only
	// distinguished by this query param, so track it to highlight the right item.
	let activeTargetType: string | null = $state(
		$page.url.searchParams.get('global-nav-target-type')
	);

	afterNavigate((navigation) => {
		// this fixes https://github.com/themesberg/flowbite-svelte/issues/364
		document.getElementById('svelte')?.scrollTo({ top: 0 });
		closeDrawer();
		activeUrl = navigation.to?.url.pathname ?? '';
		activeTargetType = navigation.to?.url.searchParams.get('global-nav-target-type') ?? null;
	});

	const isActive = (href: string) => activeUrl === href || activeUrl.startsWith(href + '/');

	const itemActive = (href: string) => {
		const underConfiguration = activeUrl.startsWith('/configuration');
		// Tag details live under /configuration/* with target type "tag".
		if (href === '/tags') {
			return isActive('/tags') || (underConfiguration && activeTargetType === 'tag');
		}
		// Everything else under /configuration/* belongs to Configs.
		if (href === '/configuration/list') {
			return underConfiguration && activeTargetType !== 'tag';
		}
		return isActive(href);
	};

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

	let vncDeviceCount = $derived(
		deploymentInfos.filter((deploymentInfo) => {
			const config = globalState.configs.find(
				(c) => c.identifier === deploymentInfo.deployed_config_id
			);
			return config && targetShouldShowVNC(config, globalState);
		}).length
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
				{
					name: $t('nav.devices'),
					icon: Server,
					href: '/devices',
					badge: deploymentInfos.length
				},
				{
					name: $t('nav.global-vnc'),
					icon: ScreenShare,
					href: '/vnc',
					hidden: !anyTargetHasVNC,
					badge: vncDeviceCount
				},
				{ name: $t('nav.tasks'), icon: ListChecks, href: '/tasks' },
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
		<a href="/" class="brand-link" aria-label={$t('common.home')}>
			<img src="/favicon.png" class="brand-mark" alt={$t('common.logo-alt')} />
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
							class="nav-item {itemActive(item.href) ? 'active' : ''}"
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
		<button class="user-trigger" id="sidebar-user-trigger" aria-label={$t('common.user-menu')}>
			<span class="avatar">{userInitial}</span>
			<span class="user-info">
				<span class="user-name">{userName}</span>
				<span class="user-role">{userSubtitle}</span>
			</span>
			<ChevronUp size={16} class="user-chevron" />
		</button>
	</div>
	<Popover
		triggeredBy="#sidebar-user-trigger"
		arrow={false}
		trigger="click"
		placement="top-start"
		class="z-50 user-popover"
	>
		<div class="user-menu">
			<div class="user-menu-header">
				<span class="avatar">{userInitial}</span>
				<span class="user-info">
					<span class="user-name">{userName}</span>
					<span class="user-role">{userSubtitle}</span>
				</span>
			</div>
			<div class="user-menu-divider"></div>
			<div class="user-menu-row">
				<span class="user-menu-label">{$t('common.theme')}</span>
				<DarkMode class="ds-icon-btn" />
			</div>
			<div class="user-menu-row">
				<span class="user-menu-label">{$t('common.language')}</span>
				<LanguageSelect />
			</div>
			<div class="user-menu-divider"></div>
			<a href="/auth/logout" class="user-menu-logout">
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
		padding: 6px 8px;
		border-radius: 8px;
		text-align: left;
		transition: background 0.12s;
	}
	.user-trigger:hover {
		background: var(--ds-surface-2);
	}
	.user-trigger :global(.user-chevron) {
		margin-left: auto;
		color: var(--ds-text-mute);
		flex-shrink: 0;
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
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
	.user-role {
		font-size: 11px;
		color: var(--ds-text-mute);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.user-menu {
		display: flex;
		flex-direction: column;
		gap: 2px;
		min-width: 220px;
	}
	.user-menu-header {
		display: flex;
		align-items: center;
		gap: 10px;
		padding: 4px 6px 6px;
	}
	.user-menu-divider {
		height: 1px;
		background: var(--ds-border);
		margin: 4px 0;
	}
	.user-menu-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 12px;
		padding: 4px 6px;
		min-height: 36px;
	}
	.user-menu-label {
		font-size: 13.5px;
		font-weight: 500;
		color: var(--ds-text);
	}
	.user-menu-logout {
		display: flex;
		align-items: center;
		gap: 10px;
		padding: 8px 6px;
		border-radius: 7px;
		color: var(--ds-text-dim);
		font-size: 13.5px;
		transition:
			background 0.12s,
			color 0.12s;
	}
	.user-menu-logout:hover {
		background: var(--ds-surface-2);
		color: var(--ds-text);
	}

	.user-menu :global(.ds-icon-btn) {
		width: 32px;
		height: 32px;
		padding: 0;
		display: inline-flex;
		align-items: center;
		justify-content: center;
		border-radius: 6px;
		color: var(--ds-text-dim);
		flex-shrink: 0;
	}
	.user-menu :global(.ds-icon-btn svg) {
		display: block;
		width: 18px;
		height: 18px;
	}
	.user-menu :global(.ds-icon-btn:hover) {
		background: var(--ds-surface-2);
		color: var(--ds-text);
	}

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
