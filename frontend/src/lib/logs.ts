export type LogLine = {
	id: string;
	hostname: string;
	severity: number;
	syslogtag: string;
	ssh_public_key: string;
	message: string;
	timestamp: string;
	facility: number;
	programname: string;
	deployment_info_id: string;
};

export type LogResponse = {
	total_count: number;
	logs: LogLine[];
};

export const getLogs = async (
	fetch: typeof window.fetch = window.fetch,
	deploymentId: string,
	to: Date | null,
	from: Date | null,
	limit: number,
	offset: number
) => {
	const fromParam = from ? `&from_datetime=${from.toISOString()}` : '';
	const toParam = to ? `&to_datetime=${to.toISOString()}` : '';

	const response = await fetch(
		`/api/logs/${deploymentId}?limit=${limit}&offset=${offset}${fromParam}${toParam}`,
		{
			method: 'GET',
			headers: {
				'Content-Type': 'application/json'
			}
		}
	);
	if (!response.ok) {
		throw new Error(`Failed to fetch logs: ${response.statusText}`);
	}
	const logs = (await response.json()) as LogResponse;
	return logs;
};
