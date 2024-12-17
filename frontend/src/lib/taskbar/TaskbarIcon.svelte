<script lang="ts">
	import { type TaskShort } from '$lib/taskstatus';
	import { Tooltip } from 'flowbite-svelte';

	export let tasks: TaskShort[];
	export let title: string;
</script>

<div class="flex items-center gap-[2px] sm:gap-1 lg:gap-2">
	<div class="w-[12px] sm:w-[20px]">
		<slot name="icon" />
	</div>
	<span class="text-xs md:text-sm hidden lg:block">
		{title}: {tasks.length}
	</span>
	<span class="text-sm block lg:hidden">
		{tasks.length}
	</span>
</div>
<Tooltip>{title}</Tooltip>
