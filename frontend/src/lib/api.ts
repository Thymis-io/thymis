import { PUBLIC_CONTROLLER_HOST, PUBLIC_CONTROLLER_PROTOCOL } from '$env/static/public';

export const controllerHost = PUBLIC_CONTROLLER_HOST || '127.0.0.1:8000';
export const controllerProtocol = PUBLIC_CONTROLLER_PROTOCOL || 'http';

if (!PUBLIC_CONTROLLER_HOST) {
	console.warn('No PUBLIC_CONTROLLER_HOST provided, using default');
}

if (!PUBLIC_CONTROLLER_PROTOCOL) {
	console.warn('No PUBLIC_CONTROLLER_PROTOCOL provided, using default');
}
