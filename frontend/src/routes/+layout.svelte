<script lang="ts">
	import '../app.postcss';
	import Navbar from './Navbar.svelte';
	import Sidebar from './Sidebar.svelte';
	import { arrow, autoUpdate, computePosition, flip, offset, shift } from '@floating-ui/dom';
	import { initializeStores, storePopup, Modal, type ModalComponent } from '@skeletonlabs/skeleton';
	import CreateDeviceModal from '$lib/CreateDeviceModal.svelte';
	import DeployModal from '$lib/DeployModal.svelte';
	import EditTagModal from '$lib/EditTagModal.svelte';
	import LogModal from '$lib/LogModal.svelte';
	import EditHostnameModal from '$lib/EditHostnameModal.svelte';

	const modalRegistry: Record<string, ModalComponent> = {
		CreateDeviceModal: { ref: CreateDeviceModal },
		EditTagModal: { ref: EditTagModal },
		EditHostnameModal: { ref: EditHostnameModal },
		DeployModal: { ref: DeployModal },
		LogModal: { ref: LogModal }
	};

	initializeStores();
	storePopup.set({ computePosition, autoUpdate, offset, shift, flip, arrow });
</script>

<Modal components={modalRegistry} />
<header
	class="sticky top-0 z-40 mx-auto w-full flex-none border-b border-gray-200 bg-white dark:border-gray-600 dark:bg-gray-800"
>
	<Navbar />
</header>
<div class="overflow-hidden lg:flex">
	<Sidebar />
	<div class="relative h-full w-full overflow-y-auto lg:ml-64">
		<slot />
	</div>
</div>
