// See https://svelte.dev/docs/kit/types#app.d.ts
// for information about these interfaces
declare global {
	namespace App {
		// interface Error {}
		// interface Locals {}
		// interface PageData {}
		// interface PageState {}
		// interface Platform {}
	}
	declare module '*.md' {
		import type { SvelteComponent } from 'svelte'
		const component: typeof SvelteComponent
		export default component
		export const metadata: Record<string, unknown>
	}
}



export {};
