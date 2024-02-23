<script lang="ts">
	import { getModalStore, popup, type PopupSettings } from '@skeletonlabs/skeleton';
	import Info from 'lucide-svelte/icons/info';
	import AlertTriangle from 'lucide-svelte/icons/alert-triangle';
	import { buildStatus } from './buildstatus';

	let modalStore = getModalStore();

	const openStdoutModal = () => {
		modalStore.trigger({
			type: 'component',
			component: 'LogModal',
			title: 'Stdout',
			meta: { log: 'stdout' }
		});
	};

	const openStderrModal = () => {
		modalStore.trigger({
			type: 'component',
			component: 'LogModal',
			title: 'Stderr',
			meta: { log: 'stderr' }
		});
	};

	const stdoutPopupHover: PopupSettings = {
		event: 'hover',
		target: 'stdoutPopup',
		placement: 'top'
	};

	const stderrPopupHover: PopupSettings = {
		event: 'hover',
		target: 'stderrPopup',
		placement: 'top'
	};
</script>

<span>
	Build Status: {$buildStatus?.status}
</span>
{#if $buildStatus?.stdout}
	<div class="mt-1.5 ml-2">
		<button
			class="btn p-0 [&>*]:pointer-events-none"
			use:popup={stdoutPopupHover}
			on:click={openStdoutModal}
		>
			<Info color="#0080c0" />
		</button>
		<div class="card p-4 variant-filled-primary z-40" data-popup="stdoutPopup">
			<pre>{$buildStatus?.stdout}</pre>
			<div class="arrow variant-filled-primary" />
		</div>
	</div>
{/if}
{#if $buildStatus?.stderr}
	<div class="mt-1.5 ml-2">
		<button
			class="btn p-0 [&>*]:pointer-events-none"
			use:popup={stderrPopupHover}
			on:click={openStderrModal}
		>
			<AlertTriangle color="#c4c400" />
		</button>
		<div class="card p-4 variant-filled-primary z-40" data-popup="stderrPopup">
			<pre>{$buildStatus?.stderr}</pre>
			<div class="arrow variant-filled-primary" />
		</div>
	</div>
{/if}
