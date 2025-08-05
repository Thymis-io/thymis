<script lang="ts">
	import Breadcrumb from '$lib/components/Breadcrumb.svelte';
	import Search from '$lib/components/Search.svelte';
	import TableOfContents from '$lib/components/TableOfContents.svelte';
	import PageNavigation from '$lib/components/PageNavigation.svelte';
	import Footer from '$lib/components/Footer.svelte';
	import NavigationSidebar from '$lib/components/NavigationSidebar.svelte';
	import DocsContent from '$lib/components/DocsContent.svelte';

	let { data } = $props();

	// Cast the content as a Svelte component constructor
	const currentPath = $derived(data.currentPath);
	const allModules = $derived(data.allModules);
	const path = $derived(data.path);

	let mobileMenuOpen = $state(false);
</script>

<!-- Modern Documentation Layout -->

<div class="min-h-screen bg-gray-50">
	<!-- Mobile menu button -->
	<div class="border-b border-gray-200 bg-white px-4 py-3 lg:hidden">
		<button
			type="button"
			onclick={() => (mobileMenuOpen = !mobileMenuOpen)}
			aria-label="Toggle menu"
			class="inline-flex items-center justify-center rounded-md p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500"
		>
			<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M4 6h16M4 12h16M4 18h16"
				/>
			</svg>
		</button>
		<span class="ml-2 text-lg font-semibold text-gray-900">Thymis Documentation</span>
	</div>

	<div class="mx-auto flex max-w-7xl">
		<!-- Sidebar -->
		<aside
			class="sticky top-0 hidden min-h-screen w-64 overflow-y-auto border-r border-gray-200 bg-white shadow-sm lg:block"
		>
			<div class="p-6">
				<h1 class="mb-6 text-xl font-bold text-gray-900">Thymis Documentation</h1>

				<Search {allModules} />

				<NavigationSidebar {allModules} />
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
				<div class="relative flex w-full max-w-xs flex-1 flex-col bg-white">
					<div class="absolute right-0 top-0 -mr-12 pt-2">
						<button
							type="button"
							onclick={() => (mobileMenuOpen = false)}
							aria-label="Close menu"
							class="ml-1 flex h-10 w-10 items-center justify-center rounded-full focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white"
						>
							<svg class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M6 18L18 6M6 6l12 12"
								/>
							</svg>
						</button>
					</div>
					<div class="h-0 flex-1 overflow-y-auto pb-4 pt-5">
						<div class="px-6">
							<h1 class="mb-6 text-xl font-bold text-gray-900">Thymis Documentation</h1>

							<Search {allModules} />

							<NavigationSidebar />
						</div>
					</div>
				</div>
			</div>
		{/if}

		<!-- Main Content -->
		<main class="flex-1 p-4 lg:p-8">
			<div class="max-w-4xl">
				<Breadcrumb {currentPath} />

				<TableOfContents />
				<article class="prose prose-lg max-w-none">
					<DocsContent {path} />
				</article>
				<PageNavigation {allModules} {currentPath} />

				<Footer />
			</div>
		</main>
	</div>
</div>
