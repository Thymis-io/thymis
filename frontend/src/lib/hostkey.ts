import { fetchWithNotify } from './fetchWithNotify';

export type Hostkey = {
	identifier: string;
	public_key: string;
	device_host: string;
};

export const getHostkey = async (fetch: typeof window.fetch, identifier: string) => {
	let hostkey: Hostkey | null = null;
	const response = await fetchWithNotify(
		`/api/hostkey/${identifier}`,
		undefined,
		{ 404: null },
		fetch
	);
	if (response.ok) {
		hostkey = await response.json();
	}
	return hostkey;
};
