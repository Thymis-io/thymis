export const load = async ({ params }: { params: Record<string, string | string[]> }) => {
	return {
		path: params.path,
	};
};
