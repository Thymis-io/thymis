import { simpleGit } from 'simple-git';

/** @type {import('./$types').RequestHandler} */
export async function GET() {
	const log = await simpleGit().log();

	return new Response(JSON.stringify(log.all));
}
