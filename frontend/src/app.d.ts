// See https://kit.svelte.dev/docs/types#app
// for information about these interfaces
declare global {
	namespace App {
		// interface Error {}
		// interface Locals {}
		// interface PageData {}
		// interface Platform {}
	}
	// eslint-disable-next-line no-var
	var terminals: TerminalType[];
	declare const __THYMIS_PACKAGE_VERSION__;
}

export {};
