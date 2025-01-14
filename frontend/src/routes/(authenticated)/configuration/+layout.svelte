<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Card } from 'flowbite-svelte';
	import ModuleList from '$lib/config/ModuleList.svelte';
	import {
		getDeviceByIdentifier,
		getTagByIdentifier,
		globalNavSelectedTargetType,
		saveState
	} from '$lib/state';
	import {
		type ModuleSettings,
		type ModuleSettingsWithOrigin,
		type Tag,
		type Device,
		type Module,
		type Origin,
		globalNavSelectedTarget,
		state,
		globalNavSelectedTag,
		globalNavSelectedConfig
	} from '$lib/state';
	import DeployActions from '$lib/components/DeployActions.svelte';
	import type { PageData } from './$types';
	import ConfigModuleCard from '$lib/config/ModuleCard.svelte';
	import HardDrive from 'lucide-svelte/icons/hard-drive';
	import TagIcon from 'lucide-svelte/icons/tag';
	import { queryParam } from 'sveltekit-search-params';
	import { derived } from 'svelte/store';
	import { page } from '$app/stores';
	import Tabbar from '$lib/components/Tabbar.svelte';

	export let data: PageData;
</script>

<div class="flex justify-between mb-4">
	<h1 class="text-3xl font-bold dark:text-white">{$globalNavSelectedTarget?.displayName}</h1>
	<DeployActions />
</div>
<Tabbar />
<slot />
