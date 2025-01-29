<script lang="ts">
	import { t } from 'svelte-i18n';
	import { globalNavSelectedTargetType, globalNavSelectedTarget } from '$lib/state';
	import Tabbar from '$lib/components/Tabbar.svelte';
	import PageHead from '$lib/components/PageHead.svelte';

	$: selectedTargetName = $globalNavSelectedTarget?.displayName ?? '';
	$: titleMap = {
		config: `${$t('configurations.details-title')}: ${selectedTargetName}`,
		tag: `${$t('tags.details-title')}: ${selectedTargetName}`,
		null: selectedTargetName
	};
	$: title = titleMap[$globalNavSelectedTargetType ?? 'null'];
</script>

<PageHead {title} />
<Tabbar />
<slot />
