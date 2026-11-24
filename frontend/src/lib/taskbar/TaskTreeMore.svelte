<script lang="ts">
	import { t } from 'svelte-i18n';
	import TaskTreeIndent from './TaskTreeIndent.svelte';

	interface Props {
		depth: number;
		/** Children hidden while collapsed. */
		hidden: number;
		expanded: boolean;
		ontoggle: () => void;
	}

	let { depth, hidden, expanded, ontoggle }: Props = $props();
</script>

<TaskTreeIndent {depth}>
	<button class="ds-btn ds-btn-sm ds-btn-ghost whitespace-nowrap" onclick={ontoggle}>
		{expanded
			? $t('taskbar.show-less')
			: `… ${$t('taskbar.show-more', { values: { count: hidden } })}`}
	</button>
</TaskTreeIndent>
