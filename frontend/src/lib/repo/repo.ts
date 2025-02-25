export type FileChange = {
	path: string;
	dir: string;
	file: string;
	diff: string;
};

export type RepoStatus = {
	changes: FileChange[];
};
