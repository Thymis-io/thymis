import { browser } from '$app/environment';
import { env } from '$env/dynamic/public';

export let controllerHost = env.PUBLIC_CONTROLLER_HOST
	? env.PUBLIC_CONTROLLER_HOST
	: '127.0.0.1:8000'; // default
if (browser) {
	// set controllerHost to the current host/api
	controllerHost = window.location.host;
}
console.log('controllerHost:', controllerHost);

if (!env.PUBLIC_CONTROLLER_HOST) {
	console.warn('No PUBLIC_CONTROLLER_HOST provided, using default');
}
