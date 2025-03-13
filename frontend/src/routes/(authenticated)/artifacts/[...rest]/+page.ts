import type { PageLoad } from './$types';

export type Folder = {
	type: 'folder';
	name: string;
	path: string;
	children: Artifact[];
};

export type File = {
	type: 'file';
	name: string;
	path: string;
};

export type Artifact = Folder | File;

export const load = (async ({ fetch, params }) => {
	const artifactsResponse = await fetch(`/api/artifacts`, { method: 'GET' });
	const selectedArtifactResponse = await fetch(`/api/artifacts/${params.rest}`, { method: 'GET' });
	const hasSelectedArtifact = selectedArtifactResponse.status === 200;
	const selectedArtifactBlob = hasSelectedArtifact
		? await selectedArtifactResponse.blob()
		: undefined;
	return {
		artifacts: (await artifactsResponse.json()) as Artifact[],
		selectedArtifact: hasSelectedArtifact
			? {
					blob: selectedArtifactBlob,
					text: await selectedArtifactBlob?.text(),
					path: params.rest,
					mediaType: selectedArtifactResponse.headers.get('content-type')
				}
			: undefined
	};
}) satisfies PageLoad;
