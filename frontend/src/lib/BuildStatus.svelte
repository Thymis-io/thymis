<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Button, Modal } from 'flowbite-svelte';
	import { CircleExclamationSolid, TriangleExclamationSolid } from 'svelte-awesome-icons';
	import { buildStatus } from './buildstatus';

	let stdoutModalOpen = false;
	let stderrModalOpen = false;

	let errorLinesInStderr: string[] = [];
	$: {
		const lines = $buildStatus?.stderr?.split('\n') ?? [];
		const trimmedLines = lines.map((line) => line.trim());
		const errorLines = trimmedLines.filter((line) => line.startsWith('error:'));
		const strippedErrorLines = errorLines.map((line) => line.replace('error:', ''));
		const trimmedStrippedErrorLines = strippedErrorLines.map((line) => line.trim());
		const nonEmptyErrorLines = trimmedStrippedErrorLines.filter((line) => line.length > 0);
		errorLinesInStderr = nonEmptyErrorLines;
	}
</script>

<div class="flex justify-between items-center gap-1">
	<span class="dark:text-white">
		{$t('deploy.build-status', { values: { status: $buildStatus?.status } })}
	</span>
	{#if $buildStatus?.stdout}
		<Button
			outline
			color={'alternative'}
			class="p-2"
			id="stderr"
			on:click={() => (stdoutModalOpen = true)}
		>
			<CircleExclamationSolid color="#0080c0" id="stdout" />
		</Button>
	{/if}
	{#if $buildStatus?.stderr}
		<Button
			outline
			color={'alternative'}
			class="p-2"
			id="stderr"
			on:click={() => (stderrModalOpen = true)}
		>
			<TriangleExclamationSolid color="#c4c400" />
		</Button>
	{/if}
</div>
<Modal title={$t('deploy.stdout')} bind:open={stdoutModalOpen} autoclose outsideclose size="xl">
	<pre class="w-full text-sm font-light z-50 hover:z-50">{$buildStatus?.stdout}</pre>
</Modal>
<Modal title={$t('deploy.stderr')} bind:open={stderrModalOpen} autoclose outsideclose size="xl">
	<div class="grid gap-1">
		<span class="dark:text-white">{$t('deploy.error-lines')}:</span>
		<ul class="flex gap-1">
			{#each errorLinesInStderr as errorLine}
				<li class="text-red-500">{errorLine}</li>
			{/each}
		</ul>
	</div>
	<div class="grid gap-1">
		<div class="dark:text-white">{$t('deploy.raw-output')}:</div>
	</div>
	<pre class="w-full text-sm font-light z-50 hover:z-50">{$buildStatus?.stderr}</pre>
</Modal>
