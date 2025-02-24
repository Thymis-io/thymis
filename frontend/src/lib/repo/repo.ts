export type FileChange = {
	file: string;
	diff: string;
};

export type RepoStatus = {
	changes: FileChange[];
};
