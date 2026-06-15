<script lang="ts">
	import '../../app.css';
	import { t } from 'svelte-i18n';
	import Navbar from '$lib/navbar/Navbar.svelte';
	import { page } from '$app/state';
	import { ProgressBar } from '@prgm/sveltekit-progress-bar';

	const redirectString = page.url.searchParams.get('redirect');
	const redirectStringDecoded = redirectString ? decodeURI(redirectString) : null;
	const authError = page.url.searchParams.get('authError');
</script>

<svelte:head>
	<title>{$t('login.page-title')}</title>
</svelte:head>

<ProgressBar color="var(--ds-accent)" zIndex={100} />

<section style="background: var(--ds-bg); color: var(--ds-text);">
	<header
		class="fixed top-0 z-40 mx-auto w-full flex-none"
		style="border-bottom: 1px solid var(--ds-border); background: var(--ds-surface);"
	>
		<Navbar
			class="h-[calc(var(--navbar-height))] max-h-[calc(var(--navbar-height))]"
			drawerHidden={false}
			authenticated={false}
		/>
	</header>
	<div class="flex flex-col items-center justify-center px-6 py-8 mx-auto h-screen lg:py-0">
		<div class="ds-card w-full md:mt-0 sm:max-w-md">
			<div class="ds-card-pad space-y-4 md:space-y-6 sm:p-8">
				<h1 class="ds-page-title text-xl md:text-2xl">{$t('login.heading')}</h1>
				{#if authError}
					<div
						class="p-3 text-sm rounded-lg"
						style="color: var(--ds-danger); background: var(--ds-danger-dim);"
					>
						{$t('login.error')}
					</div>
				{/if}
				<form class="space-y-4 md:space-y-6" action="/auth/login/basic" method="POST">
					<div>
						<label for="username" class="ds-form-label">{$t('login.username-label')}</label>
						<input
							type="text"
							name="username"
							id="username"
							class="bg-gray-50 border border-gray-300 text-gray-900 rounded-lg focus:ring-primary-600 focus:border-primary-600 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500"
							placeholder={$t('login.username-placeholder')}
							required
						/>
					</div>
					<div>
						<label for="password" class="ds-form-label">{$t('login.password-label')}</label>
						<input
							type="password"
							name="password"
							id="password"
							placeholder="••••••••"
							class="bg-gray-50 border border-gray-300 text-gray-900 rounded-lg focus:ring-primary-600 focus:border-primary-600 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500"
							required
						/>
					</div>
					<button type="submit" class="ds-btn ds-btn-primary w-full justify-center">
						{$t('login.submit')}
					</button>
					{#if redirectString}
						<input type="text" name="redirect" value={redirectStringDecoded} hidden />
					{/if}
				</form>
			</div>
		</div>
	</div>
</section>

<style lang="postcss">
	:root {
		--navbar-height: 50px;
	}
</style>
