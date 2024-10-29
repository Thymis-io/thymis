export type Commit = {
	message: string;
	author: string;
	date: string;
	SHA: string;
	SHA1: string;
	state_diff: string[];
};

export type EditRemote = {
	name: string;
	url: string;
};

export type Remote = {
	name: string;
	url: string;
	branches: string[];
};

export type GitInfo = {
	active_branch: string;
	remote_branch: string | null;
	ahead: number;
	behind: number;
	remotes: Remote[];
};
