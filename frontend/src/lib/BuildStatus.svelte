<script lang="ts">
	// TODO: Completely rework this file, see DEV-60
	import { t } from 'svelte-i18n';
	import { Button, Modal } from 'flowbite-svelte';
	import { CircleExclamationSolid, TriangleExclamationSolid } from 'svelte-awesome-icons';
	import { taskStatus } from './taskstatus';

	let stdoutModalOpen = false;
	let stderrModalOpen = false;
	let currentTask: Task | null = null;

	// $: latestTask = $taskStatus?.at(-1);

	// let errorLinesInStderr: string[] = [];
	// $: if (latestTask && 'stderr' in latestTask) {
	// 	const lines = latestTask?.stderr?.split('\n') ?? [];
	// 	const trimmedLines = lines.map((line) => line.trim());
	// 	const errorLines = trimmedLines.filter((line) => line.startsWith('error:'));
	// 	const strippedErrorLines = errorLines.map((line) => line.replace('error:', ''));
	// 	const trimmedStrippedErrorLines = strippedErrorLines.map((line) => line.trim());
	// 	const nonEmptyErrorLines = trimmedStrippedErrorLines.filter((line) => line.length > 0);
	// 	errorLinesInStderr = nonEmptyErrorLines;
	// }
	const getErrorsFromStderr = (stderr: string) => {
		const lines = stderr.split('\n');
		const trimmedLines = lines.map((line) => line.trim());
		const errorLines = trimmedLines.filter((line) => line.startsWith('error:'));
		const strippedErrorLines = errorLines.map((line) => line.replace('error:', ''));
		const trimmedStrippedErrorLines = strippedErrorLines.map((line) => line.trim());
		const nonEmptyErrorLines = trimmedStrippedErrorLines.filter((line) => line.length > 0);
		return nonEmptyErrorLines;
	};

	const hasStderr = (task) => 'stderr' in task && task.stderr;
	const hasStdout = (task) => 'stdout' in task && task.stdout;

	$: last5Tasks = $taskStatus?.slice(-5) ?? [];
</script>

<div class="dark:text-white">
	{$t('deploy.last-5-tasks')}
</div>
{#each last5Tasks as task}
	<div class="flex justify-between items-center gap-1">
		<span class="dark:text-white">
			{task.display_name}: {task.state}
		</span>
		{#if hasStdout(task)}
			<Button
				outline
				color={'alternative'}
				class="p-2"
				id="stderr"
				on:click={() => ((stdoutModalOpen = true), (currentTask = task))}
			>
				<CircleExclamationSolid color="#0080c0" id="stdout" />
			</Button>
		{/if}
		{#if hasStderr(task)}
			<Button
				outline
				color={'alternative'}
				class="p-2"
				id="stderr"
				on:click={() => ((stderrModalOpen = true), (currentTask = task))}
			>
				<TriangleExclamationSolid color="#c4c400" />
			</Button>
		{/if}
	</div>
{/each}
<Modal title={$t('deploy.stdout')} bind:open={stdoutModalOpen} autoclose outsideclose size="xl">
	<pre class="w-full text-sm font-light z-50 hover:z-50">{currentTask?.stdout}</pre>
</Modal>

<Modal title={$t('deploy.stderr')} bind:open={stderrModalOpen} autoclose outsideclose size="xl">
	<div class="grid gap-1">
		<span class="dark:text-white">{$t('deploy.error-lines')}:</span>
		<ul class="flex gap-1">
			{#each getErrorsFromStderr(currentTask?.stderr) as errorLine}
				<li class="text-red-500">{errorLine}</li>
			{/each}
		</ul>
	</div>
	<div class="grid gap-1">
		<div class="dark:text-white">{$t('deploy.raw-output')}:</div>
	</div>
	<pre class="w-full text-sm font-light z-50 hover:z-50">{currentTask?.stderr}</pre>
</Modal>
