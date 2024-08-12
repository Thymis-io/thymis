import type { PageLoad } from './$types';
import { controllerHost, controllerProtocol } from '$lib/api';

export const load = (async ({ fetch }) => {
	const response = await fetch(`${controllerProtocol}://${controllerHost}/history`, {
		method: 'GET',
		headers: {
			'content-type': 'application/json'
		}
	});
	return {
		history: response.json() as Promise<
			{ message: string; author: string; date: string; SHA: string; SHA1: string }[]
		>
	};
}) satisfies PageLoad;
