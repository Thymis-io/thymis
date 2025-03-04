<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Button, Modal } from 'flowbite-svelte';
	import { createEventDispatcher } from 'svelte';

	interface Props {
		target: string | undefined;
	}

	let { target }: Props = $props();

	const dispatch = createEventDispatcher();
</script>

<Modal
	open={!!target}
	title={$t('deleteConfirm.title', { values: { target } })}
	autoclose
	outsideclose
	on:close={() => dispatch('cancel')}
>
	<div class="text-lg">
		{$t('deleteConfirm.text', { values: { target } })}
	</div>
	<div class="flex justify-end mt-4">
		<Button on:click={() => dispatch('cancel')} color="alternative">
			{$t('deleteConfirm.cancel')}
		</Button>
		<Button on:click={() => dispatch('confirm')} color="red" class="ml-2">
			{$t('deleteConfirm.confirm')}
		</Button>
	</div>
</Modal>
