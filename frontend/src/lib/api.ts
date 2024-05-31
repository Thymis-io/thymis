import { browser } from '$app/environment';
import { env } from '$env/dynamic/public';

export let controllerHost = env.PUBLIC_CONTROLLER_HOST
	? env.PUBLIC_CONTROLLER_HOST + '/api'
	: '127.0.0.1:8000/api';
if (browser) {
	// set controllerHost to the current host/api
	controllerHost = window.location.host + '/api';
}
console.log('controllerHost:', controllerHost);
export const controllerProtocol = env.PUBLIC_CONTROLLER_PROTOCOL || 'http';

if (!env.PUBLIC_CONTROLLER_HOST) {
	console.warn('No PUBLIC_CONTROLLER_HOST provided, using default');
}

if (!env.PUBLIC_CONTROLLER_PROTOCOL) {
	console.warn('No PUBLIC_CONTROLLER_PROTOCOL provided, using default');
}
