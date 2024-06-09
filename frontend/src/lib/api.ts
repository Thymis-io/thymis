import { browser } from '$app/environment';
import { env } from '$env/dynamic/public';

export let controllerHost = env.PUBLIC_CONTROLLER_HOST
	? env.PUBLIC_CONTROLLER_HOST + '/api'
	: '127.0.0.1:8000/api'; // dev default
if (browser) {
	// set controllerHost to the current host/api
	controllerHost = window.location.host + '/api';
}
console.log('controllerHost:', controllerHost);
export const controllerProtocol = env.PUBLIC_CONTROLLER_PROTOCOL || 'http';

// if controllerHost is public and not localhost, and controllerProtocol is not https, error
const isLocalhost = (host: string) => {
	if (host.includes('localhost')) {
		return true;
	} else if (host.includes('127.0.0.1')) {
		return true;
	}
	return false;
};

if (!isLocalhost(controllerHost) && controllerProtocol !== 'https') {
	console.error('controllerHost is public and not localhost, but controllerProtocol is not https');
	// fail hard
	throw new Error(
		'controllerHost is public and not localhost, but controllerProtocol is not https'
	);
}

if (!env.PUBLIC_CONTROLLER_HOST) {
	console.warn('No PUBLIC_CONTROLLER_HOST provided, using default');
}

if (!env.PUBLIC_CONTROLLER_PROTOCOL) {
	console.warn('No PUBLIC_CONTROLLER_PROTOCOL provided, using default');
}
