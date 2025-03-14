import type { Artifact } from '../../../artifacts/[...rest]/+page';
import type { PageLoad } from './$types';

export const load = (async ({ fetch }) => {
	const artifactsResponse = await fetch(`/api/artifacts`, { method: 'GET' });
	return {
		artifacts: (await artifactsResponse.json()) as Artifact[]
	};
}) satisfies PageLoad;
