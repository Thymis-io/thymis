<script lang="ts">
	import type { PageData } from './$types';

	export let data: PageData;

	$: devices = data.devices;
</script>

<div class="border rounded-lg p-4 pb-2 bg-surface-100">
	<table class="table-auto w-full text-left">
		<thead>
			<tr class="">
				<th class="border-b border-slate-100 p-2">Name</th>
				<th class="border-b border-slate-100 p-2">Hostname</th>
				<th class="border-b border-slate-100 p-2">Tags</th>
				<th class="border-b border-slate-100 p-2">Actions</th>
				<th class="border-b border-slate-100 p-2">Status</th>
			</tr>
		</thead>
		<tbody>
			{#each devices as device}
				<tr>
					<td class="border-t border-slate-200 p-2">{device.displayName}</td>
					<td class="border-t border-slate-200 p-2">{device.hostname}</td>
					<td class="border-t border-slate-200 p-2">
						{#each device.tags as tag, i}
							<a class="underline" href="/config?tag={tag}">{tag}</a
							>{#if i < device.tags.length - 1}{', '}{/if}
						{/each}
					</td>
					<td class="border-t border-slate-200 p-2">
						<a class="btn variant-filled" href="/config?device={device.hostname}">Edit</a>
						<a class="btn variant-filled">Download Image</a>
					</td>
					<td class="border-t border-slate-200 p-2">Online</td>
				</tr>
			{/each}
		</tbody>
	</table>
</div>
