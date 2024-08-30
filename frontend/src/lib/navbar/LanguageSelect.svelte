<script lang="ts">
	import { locale, t } from 'svelte-i18n';
	import { browser } from '$app/environment';
	import { Select } from 'flowbite-svelte';
	import { onMount } from 'svelte';

	let locales = [
		{ name: $t('language.en'), value: 'en' },
		{ name: $t('language.de'), value: 'de' }
	];

	onMount(() => {
		if (browser) {
			let cookie = document.cookie.split(';').find((c) => c.trim().startsWith('locale='));
			if (cookie) {
				$locale = cookie.split('=')[1];
			}
		}
	});

	$: {
		if (browser) {
			document.cookie = `locale=${$locale || 'en'};path=/;max-age=31536000`;
		}
	}
</script>

<Select
	class="ml-2 w-32"
	size="sm"
	items={locales}
	bind:value={$locale}
	placeholder={$t('language.select')}
/>
