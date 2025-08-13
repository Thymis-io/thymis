<script lang="ts">
	import 'prismjs/themes/prism.css';
	import '@fortawesome/fontawesome-free/css/all.css';
	import Footer from './Footer.svelte';
	import NavigationSidebar from './NavigationSidebar.svelte';
	import TableOfContents from './TableOfContents.svelte';
	import Breadcrumbs from './Breadcrumbs.svelte';
	import getModuleForPath, { allModules } from '../docs/getModuleForPath';
	import { onMount, setContext } from 'svelte';
	import { writable } from 'svelte/store';
	import mermaid from 'mermaid';
	import { afterNavigate } from '$app/navigation';

	onMount(() => {
		mermaid.initialize({});
	});
	afterNavigate(() => {
		mermaid.run();
	});

	let {
		shortPath,
		prefix = '',
		prefixedPath = ''
	}: {
		prefix?: string;
		shortPath: string | string[];
		prefixedPath?: string;
	} = $props();

	// set context for prefix
	setContext('prefix', prefix);

	let mobileMenuOpen = $state(false);

	// Convert path to string for components that expect string type
	const pathString = $derived(typeof shortPath === 'string' ? shortPath : shortPath.join('/'));

	// Get content module and resolved file path
	const { contentModule, resolvedFilePath, breadcrumbs } = $derived(getModuleForPath(shortPath));
	// set context for resolved file path
	let prefixedPathStore = writable(prefixedPath);
	// Update the prefixedPath store whenever prefixedPath changes
	$effect(() => {
		prefixedPathStore.set(prefixedPath);
	});
	setContext('prefixedPath', prefixedPathStore);
</script>

<!-- Modern Documentation Layout -->

<div class="bg-gray-50">
	<!-- Mobile menu button -->
	<div
		class="sticky top-0 z-50 border-b border-gray-200 bg-white px-4 py-3 lg:hidden"
		class:hidden={mobileMenuOpen}
	>
		<button
			type="button"
			onclick={() => (mobileMenuOpen = !mobileMenuOpen)}
			aria-label="Toggle menu"
			class="inline-flex items-center justify-center rounded-md p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500"
		>
			<i class="fas fa-bars h-6 w-6"></i>
		</button>
		<span class="ml-2 text-lg font-semibold text-gray-900">Thymis Documentation</span>
	</div>

	<div class="mx-auto flex max-w-screen-2xl">
		<!-- Left Sidebar -->
		<aside
			class="sticky top-0 z-10 hidden w-72 self-start border-r border-gray-200 bg-white shadow-sm lg:flex lg:flex-col"
		>
			<div class="p-6">
				<h1 class="mb-6 text-xl font-bold text-gray-900">Thymis Documentation</h1>

				<NavigationSidebar {prefixedPath} {allModules} />
			</div>
		</aside>

		<!-- Mobile sidebar overlay -->
		{#if mobileMenuOpen}
			<div class="fixed inset-0 z-40 lg:hidden">
				<div
					class="fixed inset-0 bg-gray-600 bg-opacity-75"
					onclick={() => (mobileMenuOpen = false)}
					role="button"
					tabindex="0"
					onkeydown={(e) => e.key === 'Escape' && (mobileMenuOpen = false)}
					aria-label="Close menu"
				></div>
				<div class="relative flex h-full w-80 max-w-sm flex-col bg-white shadow-xl">
					<div class="absolute right-0 top-0 -mr-12 pt-2">
						<button
							type="button"
							onclick={() => (mobileMenuOpen = false)}
							aria-label="Close menu"
							class="ml-1 flex h-10 w-10 items-center justify-center rounded-full focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white"
						>
							<i class="fas fa-times h-6 w-6 text-white"></i>
						</button>
					</div>
					<div class="flex h-full flex-1 flex-col overflow-hidden">
						<div class="flex-shrink-0 border-b border-gray-200 px-6 py-4">
							<h1 class="text-xl font-bold text-gray-900">Thymis Documentation</h1>
						</div>
						<div class="flex-1 overflow-y-auto px-6 py-4">
							<NavigationSidebar
								onNavigate={() => (mobileMenuOpen = false)}
								{prefixedPath}
								{allModules}
							/>
						</div>
					</div>
				</div>
			</div>
		{/if}

		<!-- Main Content -->
		<main class="min-w-0 flex-1">
			<div class="p-4 lg:p-8">
				<div class="max-w-4xl">
					<!-- Breadcrumbs -->
					<Breadcrumbs path={pathString} {breadcrumbs} />

					<!-- Mobile Table of Contents -->
					<div class="mb-4 xl:hidden">
						<div class="rounded-lg border border-gray-200 bg-white p-3">
							<TableOfContents toc={contentModule.metadata?.toc} />
						</div>
					</div>

					<article
						class="prose prose-a:text-blue-600 prose-a:visited:text-purple-600 prose-code:before:hidden prose-code:after:hidden prose-code:p-1 prose-code:rounded prose-code:font-normal prose-code:bg-gray-200 mt-4 max-w-none"
					>
						<contentModule.default />
					</article>

					<Footer {resolvedFilePath} {prefixedPath} />
				</div>
			</div>
		</main>

		<!-- Right Sidebar - Table of Contents -->
		<aside class="sticky top-0 hidden w-64 self-start xl:flex xl:flex-col">
			<div class="p-6">
				<TableOfContents toc={contentModule.metadata?.toc} />
			</div>
		</aside>
	</div>
</div>
