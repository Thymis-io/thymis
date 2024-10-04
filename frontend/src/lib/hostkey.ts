export type Hostkey = {
	identifier: string;
	publicKey: string;
	deviceHost: string;
};

export const getHostkey = async (fetch: Window.fetch, identifier: string) => {
	let hostkey: Hostkey = null;
	const response = await fetch(`/api/hostkey/${identifier}`);
	if (response.ok) {
		hostkey = await response.json();
	} else if (response.status === 404) {
		hostkey = null;
	} else {
		console.log(
			'Unrecognized Error. Failed to fetch hostkey:',
			response.status,
			response.statusText
		);
	}
	return hostkey;
};
