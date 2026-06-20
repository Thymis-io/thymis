<script lang="ts">
	import { locale, t } from 'svelte-i18n';
	import { browser } from '$app/environment';
	import { Select } from 'flowbite-svelte';
	import { onMount } from 'svelte';
	import { invalidate } from '$app/navigation';

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

	const saveLocale = (evt: Event) => {
		let event_target = evt.target as HTMLSelectElement;
		if (!event_target) {
			return;
		}
		// Use the selected value directly: `locale.set` updates `$locale` asynchronously,
		// so reading `$locale` here would persist the previous locale in the cookie.
		const newLocale = event_target.value || 'en';
		$locale = newLocale;
		if (browser) {
			document.cookie = `locale=${newLocale};path=/;max-age=31536000`;
			invalidate((url) => url.pathname === '/api/available_modules');
		}
	};
</script>

<Select
	class="w-32"
	size="sm"
	items={locales}
	value={$locale}
	on:change={saveLocale}
	placeholder={$t('language.select')}
/>
