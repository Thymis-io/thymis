// @ts-check

// 1. Import the Skeleton plugin
const { skeleton } = require('@skeletonlabs/tw-plugin');
import forms from '@tailwindcss/forms';

/** @type {import('tailwindcss').Config} */
module.exports = {
	// 2. Opt for dark mode to be handled via the class method
	darkMode: 'class',
	content: [
		'./src/**/*.{html,js,svelte,ts}',
		// 3. Append the path to the Skeleton package
		require('path').join(require.resolve('@skeletonlabs/skeleton'), '../**/*.{html,js,svelte,ts}')
	],
	theme: {
		extend: {
			height: {
				'10v': '10vh',
				'20v': '20vh',
				'30v': '30vh',
				'40v': '40vh',
				'50v': '50vh',
				'60v': '60vh',
				'70v': '70vh',
				'80v': '80vh',
				'90v': '90vh',
				'100v': '100vh'
			}
		}
	},
	plugins: [
		forms,
		skeleton({
			themes: { preset: ['hamlindigo'] }
		})
	]
};
