import { should404 } from "$lib/docs/getModuleForPath";
import { error } from "@sveltejs/kit";
export const load = async ({ params }: { params: Record<string, string | string[]> }) => {
	const pathString = Array.isArray(params.path) ? params.path.join('/') : params.path;
	const notFound = should404(pathString);
	if (notFound) {
		error(404, "Not Found");
	}
	return {
		path: params.path,
	};
};
