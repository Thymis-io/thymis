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
		require('path').join(require.resolve('@skeletonlabs/skeleton'), '../**/*.{html,js,svelte,ts}'),
		'./node_modules/flowbite-svelte/**/*.{html,js,svelte,ts}'
	],
	theme: {
		extend: {
			colors: {
				// flowbite-svelte
				primary: {
					50: '#f9dce2',
					100: '#f6d0d8',
					200: '#f4c5ce',
					300: '#eea2b1',
					400: '#e15c77',
					500: '#d4163c',
					600: '#bf1436',
					700: '#9f112d',
					800: '#7f0d24',
					900: '#680b1d'
				}
			},
			minWidth: {
				0: '0px',
				1: '0.25rem',
				2: '0.5rem',
				3: '0.75rem',
				4: '1rem',
				5: '1.25rem',
				6: '1.5rem',
				7: '1.75rem',
				8: '2rem',
				9: '2.25rem',
				10: '2.5rem',
				11: '2.75rem',
				12: '3rem',
				14: '3.5rem',
				16: '4rem',
				20: '5rem',
				24: '6rem',
				28: '7rem',
				32: '8rem',
				36: '9rem',
				40: '10rem',
				44: '11rem',
				48: '12rem',
				56: '14rem',
				60: '15rem',
				64: '16rem',
				72: '18rem',
				80: '20rem',
				96: '24rem',
				0.5: '0.125rem',
				1.5: '0.375rem',
				2.5: '0.625rem',
				3.5: '0.875rem',
				full: '100%',
				min: 'min-content',
				max: 'max-content',
				fit: 'fit-content'
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
