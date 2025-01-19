import { toast } from '@zerodevx/svelte-toast';
import { browser } from '$app/environment';

export type CustomResponseMessage = {
	[statusCode: number]: string | null;
};

export const fetchWithNotify = async (
	url: string,
	init?: RequestInit,
	customResponse?: CustomResponseMessage,
	fetch: typeof window.fetch = window.fetch,
	acceptableStatus: number[] = [200, 201, 204]
) => {
	const response = await fetch(url, init);

	if (!acceptableStatus.includes(response.status)) {
		console.error(`fetch ${url}: ${response.status} ${response.statusText}`);
		let message = null;

		if (customResponse && response.status in customResponse) {
			message = customResponse[response.status];
		} else {
			message = url + ': ' + response.status + ' ' + response.statusText;
		}

		if (message !== null) {
			toast.push(message);
		}
	}

	return response;
};
