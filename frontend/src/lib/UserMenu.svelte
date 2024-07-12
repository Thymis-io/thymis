<script lang="ts">
	import { MegaMenu, ToolbarButton } from 'flowbite-svelte';
	import ArrowRightToBracketOutline from 'flowbite-svelte-icons/ArrowRightToBracketOutline.svelte';
	import GridSolid from 'flowbite-svelte-icons/GridSolid.svelte';
	import UserSolid from 'flowbite-svelte-icons/UserSolid.svelte';
	import ProfileCardOutline from 'flowbite-svelte-icons/ProfileCardOutline.svelte';
	import UsersGroupSolid from 'flowbite-svelte-icons/UsersGroupSolid.svelte';
	import UserSettingsSolid from 'flowbite-svelte-icons/UserSettingsSolid.svelte';

	const menu = [
		{ name: 'Team', href: '#', icon: UsersGroupSolid },
		{ name: 'Profile', href: '#', icon: ProfileCardOutline },
		{ name: 'Settings', href: '#', icon: UserSettingsSolid },
		{ name: 'Overview', href: '/overview', icon: GridSolid },
		{ name: 'Logout', href: '#', icon: ArrowRightToBracketOutline }
	];
</script>

<ToolbarButton size="lg"><UserSolid /></ToolbarButton>
<MegaMenu items={menu} let:item>
	<a
		href={item.href}
		class="block rounded-lg p-4 text-center hover:bg-gray-100 dark:hover:bg-gray-600"
	>
		<svelte:component
			this={item.icon}
			class="mx-auto mb-1 h-7 w-7 text-gray-500 dark:text-gray-400"
		/>
		<div class="text-sm font-medium text-gray-900 dark:text-white">{item.name}</div>
	</a>
</MegaMenu>
