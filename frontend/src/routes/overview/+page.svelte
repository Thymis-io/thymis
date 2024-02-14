<script lang="ts">
	import type { PageData } from './$types';
	import { getModalStore } from '@skeletonlabs/skeleton';
	import { saveState, type Device } from '$lib/state';
	// import { Pen } from 'lucide-svelte';
	import Pen from 'lucide-svelte/icons/pen';
	import { controllerHost, controllerProtocol } from '$lib/api';

	export let data: PageData;
</script>

<!-- container for a bunch of cards -->
<div class="grid grid-cols-4 gap-4 md:grid-cols-6 lg:grid-cols-6">
	<div class="card p-4 bg-white rounded-lg shadow-md w-full">
		<!-- number of devices: data.state.devices.length -->
		<div class="flex items-center justify-around">
			<div class="flex items-center justify-center bg-blue-100 rounded-full p-5">
				<class class="text-2xl font-bold text-gray-800">Devices</class>
				<class class="text-2xl font-bold text-gray-800 ml-2">({data.state.devices.length})</class>
			</div>
		</div>
	</div>

	<div class="card p-4 bg-white rounded-lg shadow-md w-full">
		<div class="flex items-center justify-around">
			<div class="flex items-center justify-center bg-blue-100 rounded-full p-5">
				<class class="text-2xl font-bold text-gray-800">Tags</class>
				<class class="text-2xl font-bold text-gray-800 ml-2">({data.state.tags.length})</class>
			</div>
		</div>
	</div>

	<div class="card p-4 bg-white rounded-lg shadow-md w-full">
		<div class="flex items-center justify-around">
			<div class="flex items-center justify-center bg-blue-100 rounded-full p-5">
				<class class="text-2xl font-bold text-gray-800">Modules</class>
				<class class="text-2xl font-bold text-gray-800 ml-2">({data.state.modules.length})</class>
			</div>
		</div>
	</div>
</div>
