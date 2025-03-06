import { browser } from '$app/environment';
import { invalidate } from '$app/navigation';
import { toast } from '@zerodevx/svelte-toast';
import { fetchWithNotify } from './fetchWithNotify';
import { navigating } from '$app/state';

export type Notification = {
	inner: ShouldInvalidate | FrontendToast | ImageBuiltNotification;
};

export type ShouldInvalidate = {
	kind: 'should_invalidate';
	should_invalidate_paths: string[];
};

export type FrontendToast = {
	kind: 'frontend_toast';
	message: string;
};

export type ImageBuiltNotification = {
	kind: 'image_built';
	configuration_id: string;
	image_format: string;
};

let socket: WebSocket | undefined;

let isDownloadLeader = false;

if (browser && navigator.locks) {
	navigator.locks.request(
		'download-leader',
		(lock) =>
			new Promise(() => {
				isDownloadLeader = true;
			})
	);
}

type InvalidateParams = Parameters<typeof invalidate>;
type InvalidateReturn = ReturnType<typeof invalidate>;
const invalidateButDeferUntilNavigation = async (
	...params: InvalidateParams
): Promise<InvalidateReturn> => {
	// wait
	// navigating.to should be null when we call invalidate
	while (navigating.to) {
		await new Promise((r) => setTimeout(r, 100));
	}
	// call invalidate
	return await invalidate(...params);
};

export const startNotificationSocket = () => {
	console.log('starting notification socket');
	const scheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
	socket = new WebSocket(`${scheme}://${window.location.host}/api/notification`);
	socket.onmessage = async (event) => {
		const notification = JSON.parse(event.data) as Notification;
		if (notification.inner.kind === 'frontend_toast') {
			toast.push(notification.inner.message, { pausable: true });
		} else if (notification.inner.kind === 'should_invalidate') {
			const paths = notification.inner.should_invalidate_paths;
			await invalidateButDeferUntilNavigation((url: URL) => {
				return paths.some((path: string) => url.pathname.startsWith(path));
			});
		} else if (notification.inner.kind === 'image_built') {
			const inner: ImageBuiltNotification = notification.inner;
			if (browser && inner.image_format !== 'nixos-vm' && isDownloadLeader) {
				const downloadUrl = `/api/download-image?identifier=${inner.configuration_id}`;
				const response = await fetchWithNotify(downloadUrl, { method: 'HEAD' });
				if (response.ok) {
					const a = document.createElement('a');
					a.target = '_blank';
					a.href = downloadUrl;
					a.setAttribute('download', '');
					document.body.appendChild(a);
					a.onclick = (e) => {
						e.stopPropagation();
					};
					a.click();
					document.body.removeChild(a);
				}
			}
		} else {
			const _: never = notification.inner;
		}
	};
	socket.onclose = () => {
		console.log('notification socket closed');
		setTimeout(startNotificationSocket, 1000);
	};
};
