import type { Device, ModuleSettings, State } from '$lib/state';

export const isVNCModule = (module: ModuleSettings) => module.type.toLowerCase().includes('vnc');

export const deviceHasVNCModule = (device: Device, state: State) =>
	device.modules.some(isVNCModule) ||
	device.tags.some((tag) =>
		state.tags.find((t) => t.identifier === tag)?.modules.some(isVNCModule)
	);
