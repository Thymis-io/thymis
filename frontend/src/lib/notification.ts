import { invalidate } from '$app/navigation';
import { toast } from '@zerodevx/svelte-toast';

export type Notification = {
	inner: ShouldInvalidate | FrontendToast;
};

export type ShouldInvalidate = {
	kind: 'should_invalidate';
	should_invalidate_paths: string[];
};

export type FrontendToast = {
	kind: 'frontend_toast';
	message: string;
};

let socket: WebSocket | undefined;

export const startNotificationSocket = () => {
	const scheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
	socket = new WebSocket(`${scheme}://${window.location.host}/api/notification`);
	socket.onmessage = async (event) => {
		const notification = JSON.parse(event.data) as Notification;
		if (notification.inner.kind === 'frontend_toast') {
			toast.push(notification.inner.message, { pausable: true });
		} else if (notification.inner.kind === 'should_invalidate') {
			const paths = notification.inner.should_invalidate_paths;
			await invalidate((url: URL) => {
				return paths.some((path: string) => url.pathname.startsWith(path));
			});
		} else {
			const _: never = notification.inner;
		}
	};
};
