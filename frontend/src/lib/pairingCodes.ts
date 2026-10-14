import { fetchWithNotify } from './fetchWithNotify';

export type PairingCode = {
	id: string;
	code: string;
	revoked: boolean;
	created_at: string;
	expires_at: string;
	redeemed_at: string | null;
};

export type PairingCodeList = {
	/** Redeemable. */
	active: PairingCode[];
	/** Redeemed, expired or revoked in the last days. */
	recent: PairingCode[];
};

export const getPairingCodes = async (fetch: typeof window.fetch = window.fetch) => {
	const response = await fetchWithNotify('/api/pairing-codes', undefined, {}, fetch);
	if (response.ok) return (await response.json()) as PairingCodeList;
	return { active: [], recent: [] } satisfies PairingCodeList;
};

export const createPairingCode = async () => {
	const response = await fetchWithNotify('/api/pairing-code/create', { method: 'POST' });
	if (response.ok) return (await response.json()) as PairingCode;
	return undefined;
};

export const revokePairingCode = async (id: string) => {
	return fetchWithNotify('/api/pairing-code/revoke', {
		method: 'POST',
		headers: { 'content-type': 'application/json' },
		body: JSON.stringify({ id })
	});
};
