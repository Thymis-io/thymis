<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { PageData } from './$types';
	import { Heading, P } from 'flowbite-svelte';

	export let data: PageData;
</script>

<Heading tag="h3">{$t('nav.settings')}</Heading>
<P>{JSON.stringify(data.state.repositories)}</P>
