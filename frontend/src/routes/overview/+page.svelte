<script lang="ts">
	import type { PageData } from './$types';
	import { Card } from 'flowbite-svelte';

	export let data: PageData;
</script>

<div class="flex justify-between mb-4">
	<h1 class="text-3xl font-bold dark:text-white">Übersicht</h1>
</div>

<!-- container for a bunch of cards -->
<div class="grid grid-cols-4 gap-4 md:grid-cols-6 lg:grid-cols-6">
	<Card class="card p-4 bg-white rounded-lg shadow-md w-full">
		<!-- number of devices: data.state.devices.length -->
		<div class="flex items-center justify-around">
			<div class="flex items-center justify-center bg-primary-400 rounded-full p-5 w-full">
				<class class="text-2xl font-bold text-gray-800">Devices</class>
				<class class="text-2xl font-bold text-gray-800 ml-2">({data.state.devices.length})</class>
			</div>
		</div>
	</Card>

	<Card class="card p-4 bg-white rounded-lg shadow-md w-full">
		<div class="flex items-center justify-around">
			<div class="flex items-center justify-center bg-primary-400 rounded-full p-5 w-full">
				<class class="text-2xl font-bold text-gray-800">Tags</class>
				<class class="text-2xl font-bold text-gray-800 ml-2">({data.state.tags.length})</class>
			</div>
		</div>
	</Card>

	<Card class="card p-4 bg-white rounded-lg shadow-md w-full">
		<div class="flex items-center justify-around">
			<div class="flex items-center justify-center bg-primary-400 rounded-full p-5 w-full">
				<class class="text-2xl font-bold text-gray-800">Modules</class>
				<class class="text-2xl font-bold text-gray-800 ml-2">({data.state.modules.length})</class>
			</div>
		</div>
	</Card>
</div>
