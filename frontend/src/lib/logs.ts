export const getLogs = async (
	fetch: typeof window.fetch = window.fetch,
	deploymentId: string,
	to: Date,
	from: Date,
	limit: number,
	offset: number
) => {
	const response = await fetch(
		`/api/logs/${deploymentId}?from_datetime=${from.toISOString()}&to_datetime=${to.toISOString()}&limit=${limit}&offset=${offset}`,
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
	const logs = await response.json();
	return logs;
};
