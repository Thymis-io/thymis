<script lang="ts">
	import '../../app.postcss';
	import Navbar from '$lib/navbar/Navbar.svelte';
	import { page } from '$app/state';
	import { ProgressBar } from '@prgm/sveltekit-progress-bar';

	const redirectString = page.url.searchParams.get('redirect');
	const redirectStringDecoded = redirectString ? decodeURI(redirectString) : null;
	const authError = page.url.searchParams.get('authError');
</script>

<svelte:head>
	<title>Thymis - Sign in</title>
</svelte:head>

<ProgressBar class="text-primary-500" zIndex={100} />

<section class="bg-gray-50 dark:bg-gray-900 dark:text-white">
	<header
		class="fixed top-0 z-40 mx-auto w-full flex-none border-b border-gray-200 bg-white dark:border-gray-600 dark:bg-gray-800"
	>
		<Navbar
			class="h-[calc(var(--navbar-height))] max-h-[calc(var(--navbar-height))]"
			drawerHidden={false}
			authenticated={false}
		/>
	</header>
	<div class="flex flex-col items-center justify-center px-6 py-8 mx-auto h-screen lg:py-0">
		<div
			class="w-full bg-white rounded-lg shadow dark:border md:mt-0 sm:max-w-md xl:p-0 dark:bg-gray-800 dark:border-gray-700"
		>
			<div class="p-6 space-y-4 md:space-y-6 sm:p-8">
				<h1
					class="text-xl font-bold leading-tight tracking-tight text-gray-900 md:text-2xl dark:text-white"
				>
					Sign in to your account
				</h1>
				{#if authError}
					<div
						class="p-4 text-sm text-red-500 bg-red-100 rounded-lg dark:bg-red-700 dark:text-red-200"
					>
						You have entered an invalid username or password.
					</div>
				{/if}
				<form class="space-y-4 md:space-y-6" action="/auth/login/basic" method="POST">
					<div>
						<label
							for="username"
							class="block mb-2 text-sm font-medium text-gray-900 dark:text-white"
							>Your username</label
						>
						<input
							type="text"
							name="username"
							id="username"
							class="bg-gray-50 border border-gray-300 text-gray-900 rounded-lg focus:ring-primary-600 focus:border-primary-600 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500"
							placeholder="username"
							required
						/>
					</div>
					<div>
						<label
							for="password"
							class="block mb-2 text-sm font-medium text-gray-900 dark:text-white">Password</label
						>
						<input
							type="password"
							name="password"
							id="password"
							placeholder="••••••••"
							class="bg-gray-50 border border-gray-300 text-gray-900 rounded-lg focus:ring-primary-600 focus:border-primary-600 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500"
							required
						/>
					</div>
					<button
						type="submit"
						class="w-full text-white bg-primary-600 hover:bg-primary-700 focus:ring-4 focus:outline-none focus:ring-primary-300 font-medium rounded-lg text-sm px-5 py-2.5 text-center dark:bg-primary-600 dark:hover:bg-primary-700 dark:focus:ring-primary-800"
						>Sign in</button
					>
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
