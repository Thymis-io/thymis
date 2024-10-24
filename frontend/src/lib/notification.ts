import { toast } from '@zerodevx/svelte-toast';

export type Notification = {
	message: string;
};

let socket: WebSocket | undefined;

export const startNotificationSocket = () => {
	const scheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
	socket = new WebSocket(`${scheme}://${window.location.host}/api/notification`);
	socket.onmessage = (event) => {
		const notification = JSON.parse(event.data);
		toast.push(notification.message, { pausable: true });
	};
};
