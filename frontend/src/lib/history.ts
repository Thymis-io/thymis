export type Commit = {
	message: string;
	author: string;
	date: string;
	SHA: string;
	SHA1: string;
};

export type Remote = {
	name: string;
	url: string;
};
