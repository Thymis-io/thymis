<script lang="ts">
	import type { DefaultLogFields } from 'simple-git';

	let history: DefaultLogFields[] = [];

	async function loadHistory() {
		const response = await fetch('/api/history', {
			method: 'GET',
			headers: {
				'content-type': 'application/json'
			}
		});

		history = await response.json();
		console.log(history);
	}

	loadHistory();
</script>

{#each history as h}
	<p>{h.message}</p>
{/each}
