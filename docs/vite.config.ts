import { mdsvex, code_highlighter } from 'mdsvex';
import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';
import { fileURLToPath } from 'node:url';
import { dirname } from 'node:path';
import rehypeSlug from 'rehype-slug';
import relativeImages from 'mdsvex-relative-images';
import rehypeAutolinkHeadings from 'rehype-autolink-headings';
import { fromHtmlIsomorphic } from 'hast-util-from-html-isomorphic';
import { visit } from 'unist-util-visit';
import devtoolsJson from 'vite-plugin-devtools-json';
import tailwindcss from '@tailwindcss/vite';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export const remarkExtractToc = (options) => {
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

		// Now, recursively visit
		// to get all links
		let links = [];

		visit(tree, 'link', (node) => {
			// get all links in the document
			links.push({
				href: node.url,
				text: node.children.map((child) => child.value).join('')
			});
		});

		vFile.data.fm.links = links;

		// also save vFile.contents
		vFile.data.fm.contents = vFile.contents;
	};
};

export default defineConfig({
	plugins: [
		tailwindcss(),
		sveltekit({
			// Consult https://svelte.dev/docs/kit/integrations
			// for more information about preprocessors
			preprocess: [
				mdsvex({
					extensions: ['.svx', '.md'],
					remarkPlugins: [remarkExtractToc, relativeImages],
					rehypePlugins: [
						rehypeSlug,
						[
							rehypeAutolinkHeadings,
							{
								behavior: 'append',
								headingProperties: { class: 'group' },
								content: fromHtmlIsomorphic(
									'<span class="fa-solid fa-link ml-3 lg:!hidden group-hover:!inline-block !text-black"></span>',
									{ fragment: true }
								).children
							}
						]
					],
					layout: {
						// github.com/pngwn/MDsveX/issues/556
						summary:
							dirname(fileURLToPath(import.meta.url)) + '/src/lib/components/SummaryLayout.svelte',
						_:
							dirname(fileURLToPath(import.meta.url)) +
							'/src/lib/components/DefaultMarkdownLayout.svelte'
					},
					highlight: {
						highlighter: async (code, lang, _meta, _filename, optimise) => {
							const result = await code_highlighter(code, lang, _meta, _filename, optimise);

							if (lang === 'mermaid') {
								return `<div class="not-prose"><pre class="mermaid">${code}</pre></div>`;
							}

							if (_filename.includes('src/lib/docs') && !_filename.includes('SUMMARY.md')) {
								return result
									.replace(
										/^<pre/g,
										`<Components.pre lang={"${lang}"} code={"${encodeURIComponent(code).replace(/\%([0-9A-F]{2})/g, '\\x$1')}"}`
									)
									.replace(/pre>$/g, 'Components.pre>');
							}

							return result;
						}
					}
				}),
				vitePreprocess()
			],
			extensions: ['.svelte', '.svx', '.md'],
			compilerOptions: {
				warningFilter: (warning) => {
					if (warning.code === 'a11y_img_redundant_alt') {
						return false;
					}

					return true;
				}
			},

			adapter: adapter({
				// Enable SPA mode with fallback
				fallback: 'index.html'
			}),
			prerender: { entries: ['*', '/'] }
		}),
		devtoolsJson()
	],
	test: {
		projects: [
			{
				extends: './vite.config.ts',
				test: {
					name: 'client',
					environment: 'browser',
					browser: {
						enabled: true,
						provider: 'playwright',
						instances: [{ browser: 'chromium' }]
					},
					include: ['src/**/*.svelte.{test,spec}.{js,ts}'],
					exclude: ['src/lib/server/**'],
					setupFiles: ['./vitest-setup-client.ts']
				}
			},
			{
				extends: './vite.config.ts',
				test: {
					name: 'server',
					environment: 'node',
					include: ['src/**/*.{test,spec}.{js,ts}'],
					exclude: ['src/**/*.svelte.{test,spec}.{js,ts}']
				}
			}
		]
	},
	server: {
		allowedHosts: ['localhost', '.ngrok-free.app']
	}
});
