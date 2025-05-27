import type { PageLoad } from './$types';

export type Artifact = {
	name: string;
	media_type?: string | null;
	size: number;
	created_at: string;
	modified_at: string;
};

export const load = (async ({ fetch }) => {
	const artifactsResponse = await fetch(`/api/artifacts`, { method: 'GET' });
	return {
		artifacts: (await artifactsResponse.json()) as Artifact[]
	};
}) satisfies PageLoad;
