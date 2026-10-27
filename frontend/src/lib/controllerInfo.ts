import { fetchWithNotify } from '#lib/fetchWithNotify.js';

export type ControllerInfo = {
	/** THYMIS_AGENT_ACCESS_URL, falling back to THYMIS_BASE_URL. */
	agent_access_url: string;
};

export const getControllerInfo = async (fetch: typeof window.fetch = window.fetch) => {
	const response = await fetchWithNotify('/api/controller-info', undefined, {}, fetch);
	return (await response.json()) as ControllerInfo;
};
