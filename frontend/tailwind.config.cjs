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
		require('path').join(require.resolve('@skeletonlabs/skeleton'), '../**/*.{html,js,svelte,ts}', './node_modules/flowbite-svelte/**/*.{html,js,svelte,ts}')
	],
	theme: {
		extend: {
			colors: {
				// flowbite-svelte
				primary: {
				  50: '#FFF5F2',
				  100: '#FFF1EE',
				  200: '#FFE4DE',
				  300: '#FFD5CC',
				  400: '#FFBCAD',
				  500: '#FE795D',
				  600: '#EF562F',
				  700: '#EB4F27',
				  800: '#CC4522',
				  900: '#A5371B'
				}
			}
		}
	},
	plugins: [
		forms,
		skeleton({
			themes: { preset: ['hamlindigo'] }
		}),
		require('flowbite/plugin')
	]
};
