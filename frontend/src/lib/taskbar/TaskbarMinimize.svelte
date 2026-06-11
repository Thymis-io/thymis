<script lang="ts">
	import { t } from 'svelte-i18n';
	import ChevronsDown from 'lucide-svelte/icons/chevrons-down';
	import ChevronsUp from 'lucide-svelte/icons/chevrons-up';

	interface Props {
		class?: string;
		taskbarMinimized?: boolean;
	}

	let { class: className = '', taskbarMinimized = $bindable(false) }: Props = $props();
</script>

<div class={'absolute right-0 z-10 flex items-stretch ' + className}>
	<button
		title={taskbarMinimized ? $t('taskbar.maximize') : $t('taskbar.minimize')}
		class="flex h-full items-center justify-center px-3 text-[var(--ds-text-dim)] transition-colors hover:bg-[var(--ds-surface-2)] hover:text-[var(--ds-text)]"
		onclick={() => (taskbarMinimized = !taskbarMinimized)}
	>
		{#if taskbarMinimized}
			<ChevronsUp size={22} />
		{:else}
			<ChevronsDown size={22} />
		{/if}
	</button>
</div>
