import { writable } from 'svelte/store';

type BuildStatus = {
	status: string;
	stdout: string;
	stderr: string;
};

export let buildStatus = writable<BuildStatus | undefined>();

setInterval(async () => {
	const response = await fetch('http://localhost:8000/build_status');
	buildStatus.set(await response.json());
}, 200);
