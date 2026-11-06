// Plain JS (not TS): consumers import this from their vite config, which Vite loads
// as an external from node_modules, where Node refuses to strip TypeScript types.
import { visit } from 'unist-util-visit';

/** @typedef {import('mdast').Root} Root */
/**
 * mdsvex passes its own (legacy) VFile; only the fields used here are typed.
 * @typedef {{ data: { fm?: Record<string, unknown> }; contents?: unknown }} MdsvexVFile
 */

export const remarkExtractToc = () => {
	/**
	 * @param {Root} tree
	 * @param {MdsvexVFile} vFile
	 */
	return (tree, vFile) => {
		if (!vFile.data) {
			vFile.data = {};
		}

		if (!vFile.data.fm) {
			vFile.data.fm = {};
		}

		vFile.data.fm.toc = vFile.data.fm.toc || [];

		/** @type {{ level: number; text: string; id: unknown }[]} */
		const headings = [];

		tree.children.forEach((node) => {
			if (node.type === 'heading') {
				const heading = {
					level: node.depth,
					text: node.children.map((child) => ('value' in child ? child.value : '')).join(''),
					id:
						/** @type {{ hProperties?: { id?: unknown } } | undefined} */ (node.data)?.hProperties
							?.id || null
				};

				headings.push(heading);
			}
		});

		vFile.data.fm.toc = headings;

		// Now, recursively visit
		// to get all links
		/** @type {{ href: string; text: string }[]} */
		const links = [];

		visit(tree, 'link', (node) => {
			// get all links in the document
			links.push({
				href: node.url,
				text: node.children.map((child) => ('value' in child ? child.value : '')).join('')
			});
		});

		vFile.data.fm.links = links;

		// also save vFile.contents
		vFile.data.fm.contents = vFile.contents;
	};
};
