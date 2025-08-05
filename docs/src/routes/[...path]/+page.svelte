<script lang="ts">
	import "prismjs/themes/prism.css";
	import "@fortawesome/fontawesome-free/css/all.css";
	import Footer from '$lib/components/Footer.svelte';
	import NavigationSidebar from '$lib/components/NavigationSidebar.svelte';
	import TableOfContents from '$lib/components/TableOfContents.svelte';
	import getModuleForPath from '$lib/docs/getModuleForPath.js';

	let { data } = $props();

	// Cast the content as a Svelte component constructor
	const path = $derived(data.path);

	let mobileMenuOpen = $state(false);

	const {
		contentModule,
		resolvedFilePath
	} = $derived(getModuleForPath(path));
</script>

<!-- Modern Documentation Layout -->

<div class="min-h-screen bg-gray-50">
	<!-- Mobile menu button -->
	<div class="sticky top-0 border-b border-gray-200 bg-white px-4 py-3 lg:hidden">
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

	<div class="mx-auto flex max-w-screen-2xl h-screen">
		<!-- Left Sidebar -->
		<aside
			class="sticky top-0 hidden w-64 border-r border-gray-200 bg-white shadow-sm lg:flex lg:flex-col"
		>
			<div class="flex-1 overflow-y-auto">
				<div class="p-6">
					<h1 class="mb-6 text-xl font-bold text-gray-900">Thymis Documentation</h1>

					<NavigationSidebar />
				</div>
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
					<div class="flex h-full flex-1 flex-col overflow-hidden">
						<div class="flex-shrink-0 border-b border-gray-200 px-6 py-4">
							<h1 class="text-xl font-bold text-gray-900">Thymis Documentation</h1>
						</div>
						<div class="flex-1 overflow-y-auto px-6 py-4">
							<NavigationSidebar onNavigate={() => (mobileMenuOpen = false)} />
						</div>
					</div>
				</div>
			</div>
		{/if}

		<!-- Main Content -->
		<main class="flex-1 min-w-0 overflow-y-auto">
			<div class="p-4 lg:p-8">
				<div class="max-w-4xl">
					<article class="prose prose-headings:group max-w-none">
						<contentModule.default />
					</article>

					<Footer {resolvedFilePath} />
				</div>
			</div>
		</main>

		<!-- Right Sidebar - Table of Contents -->
		<aside
			class="sticky top-0 hidden w-64 xl:flex xl:flex-col"
		>
			<div class="flex-1 overflow-y-auto">
				<div class="p-6">
					<TableOfContents toc={contentModule.metadata?.toc} />
				</div>
			</div>
		</aside>
	</div>
</div>
