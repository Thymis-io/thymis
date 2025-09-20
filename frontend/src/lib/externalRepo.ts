export type FlakeReference =
	| IndirectFlakeReference
	| GitFlakeReference
	| GithubFlakeReference
	| GitlabFlakeReference;

export type IndirectFlakeReference = {
	type: 'indirect';
	flake_id: string;
	rev: string | null;
	ref: string | null;
};

export type GitFlakeReference = {
	type: 'git';
	protocol: 'http' | 'https' | 'ssh' | 'git' | 'file';
	url: string;
	host: string;
	owner: string | null;
	repo: string;
	ref: string | null;
	rev: string | null;
};

export type GithubFlakeReference = {
	type: 'github';
	host: string | null;
	owner: string;
	repo: string;
	ref: string | null;
	rev: string | null;
};

export type GitlabFlakeReference = {
	type: 'gitlab';
	host: string | null;
	owner: string;
	repo: string;
	ref: string | null;
	rev: string | null;
};
