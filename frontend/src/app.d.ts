// See https://kit.svelte.dev/docs/types#app
// for information about these interfaces
// import type { toast } from '@zerodevx/svelte-toast';
declare global {
	namespace App {
		// interface Error {}
		// interface Locals {}
		// interface PageData {}
		// interface Platform {}
	}
	// eslint-disable-next-line no-var
	var terminals: TerminalType[];
	// eslint-disable-next-line no-var
	var toast: typeof import('@zerodevx/svelte-toast').toast;
	declare const __THYMIS_PACKAGE_VERSION__;
}

export {};
