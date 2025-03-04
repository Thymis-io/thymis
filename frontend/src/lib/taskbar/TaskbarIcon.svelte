<script lang="ts">
	import { type TaskShort } from '$lib/taskstatus';

	interface Props {
		tasks: TaskShort[];
		title: string;
		class?: string;
		icon?: import('svelte').Snippet;
	}

	let { tasks, title, class: clazz = '', icon }: Props = $props();
</script>

<div class="flex items-center gap-[2px] sm:gap-1 lg:gap-2 {clazz}">
	<div class="w-[12px] sm:w-[20px]">
		{@render icon?.()}
	</div>
	<span class="text-xs md:text-sm hidden lg:block">
		{title}: {tasks.length}
	</span>
	<span class="text-sm block lg:hidden">
		{tasks.length}
	</span>
</div>
