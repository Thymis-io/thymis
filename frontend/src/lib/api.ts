import { env } from '$env/dynamic/public';

export const controllerHost = env.PUBLIC_CONTROLLER_HOST || '127.0.0.1:8000';
export const controllerProtocol = env.PUBLIC_CONTROLLER_PROTOCOL || 'http';

if (!env.PUBLIC_CONTROLLER_HOST) {
	console.warn('No PUBLIC_CONTROLLER_HOST provided, using default');
}

if (!env.PUBLIC_CONTROLLER_PROTOCOL) {
	console.warn('No PUBLIC_CONTROLLER_PROTOCOL provided, using default');
}
