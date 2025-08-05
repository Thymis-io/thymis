import { mdsvex } from 'mdsvex';
import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';
import { fileURLToPath } from 'node:url';
import { dirname } from 'node:path';
import rehypeSlug from 'rehype-slug';
import relativeImages from "mdsvex-relative-images";


const remarkExtractToc = (options) => {
	return (tree, vFile) => {
		if (!vFile.data) {
			vFile.data = {};
		}
		if (!vFile.data.fm) {
			vFile.data.fm = {};
		}
		vFile.data.fm.toc = vFile.data.fm.toc || [];
		let headings = [];
		tree.children.forEach((node) => {
			if (node.type === 'heading') {
				const heading = {
					level: node.depth,
					text: node.children.map((child) => child.value).join(''),
					id:
						node.data && node.data.hProperties && node.data.hProperties.id
							? node.data.hProperties.id
							: null
				};
				headings.push(heading);
			}
		});
		vFile.data.fm.toc = headings;
	};
};

/** @type {import('@sveltejs/kit').Config} */
const config = {
	// Consult https://svelte.dev/docs/kit/integrations
	// for more information about preprocessors
	preprocess: [
		vitePreprocess(),
		mdsvex({
			extensions: ['.svx', '.md'],
			remarkPlugins: [remarkExtractToc, relativeImages],
			rehypePlugins: [rehypeSlug],
			layout: {
				// github.com/pngwn/MDsveX/issues/556
				summary: dirname(fileURLToPath(import.meta.url)) + '/src/lib/components/SummaryLayout.svelte',
				_: dirname(fileURLToPath(import.meta.url)) + '/src/lib/components/MarkdownLayout.svelte'
			}
		})
	],
	kit: {
		adapter: adapter({
			// Enable SPA mode with fallback
			fallback: 'index.html'
		})
	},
	extensions: ['.svelte', '.svx', '.md']
};

export default config;
