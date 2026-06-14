<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Button, Modal } from 'flowbite-svelte';
	import TriangleAlert from 'lucide-svelte/icons/triangle-alert';
	import { createEventDispatcher } from 'svelte';

	interface Props {
		target: string | undefined;
		description?: string;
	}

	let { target, description }: Props = $props();

	const dispatch = createEventDispatcher();
</script>

<Modal
	open={!!target}
	title={$t('deleteConfirm.title', { values: { target } })}
	autoclose
	outsideclose
	on:close={() => dispatch('cancel')}
>
	<div class="delete-callout">
		<TriangleAlert size={22} class="shrink-0" style="color: var(--ds-danger)" />
		<div class="min-w-0">
			<p class="text-base whitespace-pre-line" style="color: var(--ds-text)">
				{description || $t('deleteConfirm.text', { values: { target } })}
			</p>
			<p class="mt-1 text-sm font-medium" style="color: var(--ds-danger)">
				{$t('deleteConfirm.warning')}
			</p>
		</div>
	</div>
	<div class="mt-4 flex justify-end gap-2">
		<Button on:click={() => dispatch('cancel')} color="alternative">
			{$t('deleteConfirm.cancel')}
		</Button>
		<Button on:click={() => dispatch('confirm')} color="red">
			<TriangleAlert size={16} class="mr-2" />
			{$t('deleteConfirm.confirm')}
		</Button>
	</div>
</Modal>

<style lang="postcss">
	.delete-callout {
		display: flex;
		align-items: flex-start;
		gap: 12px;
		padding: 14px 16px;
		border-radius: var(--ds-radius);
		border: 1px solid var(--ds-danger);
		background: var(--ds-danger-dim);
	}
</style>
