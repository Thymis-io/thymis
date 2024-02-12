<script lang="ts">
	import { buildStatus } from '$lib/buildstatus';
	import { getModalStore, popup, type PopupSettings } from '@skeletonlabs/skeleton';
	import { AlertTriangle, CloudCog, Info, Play } from 'lucide-svelte';
	import '../app.postcss';
	import { controllerHost, controllerProtocol } from './api';

	let modalStore = getModalStore();

	const build = async () => {
		await fetch(`${controllerProtocol}://${controllerHost}/action/build`, { method: 'POST' });
	};

	const update = async () => {
		await fetch(`${controllerProtocol}://${controllerHost}/action/update`, { method: 'POST' });
	};

	const openDeploy = () => {
		modalStore.trigger({
			type: 'component',
			component: 'DeployModal',
			title: 'Deploy'
		});
	};

	function openStdoutModal() {
		modalStore.trigger({
			type: 'component',
			component: 'LogModal',
			title: 'Stdout',
			meta: { log: $buildStatus?.stdout }
		});
	}

	function openStderrModal() {
		modalStore.trigger({
			type: 'component',
			component: 'LogModal',
			title: 'Stderr',
			meta: { log: $buildStatus?.stderr }
		});
	}

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
<button class="btn variant-filled" on:click={build}>
	<span><Play /></span><span>Build</span>
</button>
<button class="btn variant-filled" on:click={openDeploy}>
	<span><CloudCog /></span><span>Deploy</span>
</button>
<button class="btn variant-filled" on:click={update}>
	<span><CloudCog /></span><span>Update</span>
</button>
