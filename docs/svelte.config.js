import { mdsvex } from 'mdsvex';
import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';
import { fileURLToPath } from 'node:url';
import { dirname } from 'node:path';
import rehypeSlug from 'rehype-slug';
import relativeImages from "mdsvex-relative-images";
import rehypeAutolinkHeadings from 'rehype-autolink-headings';
import {fromHtmlIsomorphic} from 'hast-util-from-html-isomorphic'



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
			rehypePlugins: [rehypeSlug, [rehypeAutolinkHeadings,{
				behavior: 'append',
				headingProperties: {
					class:'group'
				},
				content: fromHtmlIsomorphic('<span class="fa-solid fa-link ml-3 lg:!hidden group-hover:!inline-block"></span>', {fragment: true}).children,
			}]],
			layout: {
				// github.com/pngwn/MDsveX/issues/556
				summary: dirname(fileURLToPath(import.meta.url)) + '/src/lib/components/SummaryLayout.svelte',
				_: dirname(fileURLToPath(import.meta.url)) + '/src/lib/components/DefaultMarkdownLayout.svelte'
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
