<script lang="ts">
	import { locale, t } from 'svelte-i18n';
	import { browser } from '$app/environment';
	import { Select } from 'flowbite-svelte';

	let locales = [
		{ name: $t('language.en'), value: 'en' },
		{ name: $t('language.de'), value: 'de' }
	];

	let selected = $locale || 'en';

	$: {
		$locale = selected;
		// also set cookie if browser
		if (browser) {
			document.cookie = `locale=${selected};path=/;max-age=31536000`;
		}
	}
</script>

<Select
	class="ml-2 w-32"
	size="sm"
	items={locales}
	bind:value={selected}
	placeholder={$t('language.select')}
/>
