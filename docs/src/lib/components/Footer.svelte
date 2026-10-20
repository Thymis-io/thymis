<script lang="ts">
	import { metadata } from '../docs/SUMMARY.md';
	import A from './defaultMarkdown/a.svelte';
	import { getContext } from 'svelte';

	// Type definitions for the metadata structure
	interface Link {
		href: string;
		text: string;
	}

	interface Metadata {
		links: Link[];
	}

	// Cast metadata to the proper type
	const typedMetadata = metadata as unknown as Metadata;

	const prefix = getContext<string>('prefix') || '';

	const currentYear = new Date().getFullYear();

	let {
		resolvedFilePath,
		prefixedPath = ''
	}: { resolvedFilePath?: string; prefixedPath?: string } = $props();

	const normalizeHref = (href: string) => {
		// Remove .md
		const hrefWithoutMd = href.endsWith('.md') ? href.slice(0, -3) : href;
		// Remove index.md
		const hrefWithoutIndex = hrefWithoutMd.endsWith('index')
			? hrefWithoutMd.slice(0, -5)
			: hrefWithoutMd;
		// Remove trailing slash
		const cleanHref = hrefWithoutIndex === '/' ? '/' : hrefWithoutIndex.replace(/\/$/, '');
		// add leading slash if not present
		return cleanHref.startsWith('/') ? cleanHref : `/${cleanHref}`;
	};

	// Navigation logic
	const currentPageIndex = $derived.by(() => {
		const cleanPrefixedPath = prefixedPath === '/' ? '/' : prefixedPath.replace(/\/$/, '');
		return typedMetadata.links.findIndex((link: Link) => {
			const linkPath = normalizeHref(link.href);
			let prefixedLinkPath = prefix + linkPath;
			// Handle the case where linkPath is '/' and we have a prefix
			if (linkPath === '/' && prefix) {
				prefixedLinkPath = prefix === '/' ? '/' : prefix.replace(/\/$/, '');
			}
			return prefixedLinkPath === cleanPrefixedPath;
		});
	});

	const previousPage = $derived.by(() => {
		if (currentPageIndex > 0) {
			return typedMetadata.links[currentPageIndex - 1];
		}
		return null;
	});

	const nextPage = $derived.by(() => {
		if (currentPageIndex >= 0 && currentPageIndex < typedMetadata.links.length - 1) {
			return typedMetadata.links[currentPageIndex + 1];
		}
		return null;
	});

	const githubEditUrl = $derived.by(() => {
		if (!resolvedFilePath) return null;
		// Remove leading slash and convert to full GitHub edit URL
		const cleanPath = resolvedFilePath.startsWith('/')
			? resolvedFilePath.slice(1)
			: resolvedFilePath;
		return `https://github.com/Thymis-io/thymis/edit/master/docs/src/lib/docs/${cleanPath}`;
	});
</script>

<footer class="mt-16 border-t border-gray-200">
	<!-- Page Navigation -->
	{#if previousPage || nextPage}
		<div class="mb-4 max-w-4xl">
			<div class="flex items-center justify-between">
				<div class="flex-1">
					{#if previousPage}
						<A
							href={normalizeHref(previousPage.href)}
							class="group flex items-center space-x-2 py-4 text-sm text-gray-600 transition-colors hover:text-gray-900"
						>
							<i
								class="fas fa-chevron-left h-4 w-4 transform transition-transform group-hover:-translate-x-1"
							></i>
							<div class="text-left">
								<div class="text-xs tracking-wide text-gray-400 uppercase">Previous</div>
								<div class="font-medium">{previousPage.text}</div>
							</div>
						</A>
					{/if}
				</div>

				<div class="flex-1 text-right">
					{#if nextPage}
						<A
							href={normalizeHref(nextPage.href)}
							class="group flex items-center justify-end space-x-2 py-4 text-sm text-gray-600 transition-colors hover:text-gray-900"
						>
							<div class="text-right">
								<div class="text-xs tracking-wide text-gray-400 uppercase">Next</div>
								<div class="font-medium">{nextPage.text}</div>
							</div>
							<i
								class="fas fa-chevron-right h-4 w-4 transform transition-transform group-hover:translate-x-1"
							></i>
						</A>
					{/if}
				</div>
			</div>
		</div>
	{/if}

	<div class="max-w-4xl">
		<div class="flex flex-col items-center justify-between text-sm text-gray-600 md:flex-row">
			<div class="mb-4 flex items-center space-x-4 md:mb-0"></div>

			<div class="flex items-center space-x-4">
				{#if githubEditUrl}
					<a
						href={githubEditUrl}
						target="_blank"
						rel="noopener noreferrer"
						class="flex items-center space-x-1 text-xs transition-colors hover:text-gray-900"
					>
						<i class="fab fa-github h-4 w-4"></i>
						<span>Edit on GitHub</span>
					</a>
				{/if}
			</div>
		</div>
	</div>
</footer>
