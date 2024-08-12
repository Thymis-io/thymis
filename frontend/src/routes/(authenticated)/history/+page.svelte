<script lang="ts">
	import type { PageData } from './$types';
	export let data: PageData;

	// history: response.json() as Promise<{ message: string; author: string, date: string , hash: string }[]>
</script>

<div class="flex justify-between mb-4">
	<h1 class="text-3xl font-bold dark:text-white">History</h1>
</div>
{#await data.history}
	<p>Loading...</p>
{:then history}
	<ul class="list-disc ml-4">
		{#each history as h}
			<!-- simple left-bound list -->
			<li class="mb-2 text-gray-600">
				<!-- {h.message} by {h.author} on {h.date} with hash {h.hash} -->
				<span class="text-gray-600">{h.message}</span>
				<span class="text-gray-400"> by {h.author}</span>
				<span class="text-gray-400"> on {h.date}</span>
				<span class="text-gray-400"> with hash {h.SHA1}</span>
			</li>
		{/each}
	</ul>
{/await}
