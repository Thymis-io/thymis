import { derived, writable } from 'svelte/store';

type VncScreenshotCapture = () => Promise<File>;

const activeCapture = writable<VncScreenshotCapture | null>(null);

export const vncScreenshotAvailable = derived(activeCapture, Boolean);

export const registerVncScreenshotCapture = (capture: VncScreenshotCapture) => {
	activeCapture.set(capture);

	return () => {
		activeCapture.update((currentCapture) => (currentCapture === capture ? null : currentCapture));
	};
};

export const captureActiveVncScreenshot = async () => {
	let capture: VncScreenshotCapture | null = null;
	const unsubscribe = activeCapture.subscribe((currentCapture) => (capture = currentCapture));
	unsubscribe();

	if (!capture) {
		throw new Error('Open a connected VNC session before attaching a screenshot.');
	}

	return capture();
};
