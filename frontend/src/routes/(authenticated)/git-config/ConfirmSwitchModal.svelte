<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Button, Modal, Label, P, Input, Helper } from 'flowbite-svelte';
	import { createEventDispatcher } from 'svelte';

	export let currentBranch: string | undefined;
	export let remoteBranch: string | undefined;

	const dispatch = createEventDispatcher();

	$: title = currentBranch
		? $t('git-config.confirm-switch-modal-title-from-to', {
				values: { fromBranch: currentBranch, toBranch: remoteBranch }
			})
		: $t('git-config.confirm-switch-modal-title-new', { values: { branch: remoteBranch } });
</script>

<Modal {title} open={!!remoteBranch} autoclose outsideclose on:close={() => dispatch('cancel')}>
	<div class="text-lg">
		{$t('git-config.confirm-switch-modal-text')}
	</div>
	<div class="flex justify-end mt-4">
		<Button on:click={() => dispatch('cancel')} color="alternative">
			{$t('git-config.confirm-switch-modal-cancel')}
		</Button>
		<Button on:click={() => dispatch('confirm')} color="red" class="ml-2">
			{$t('git-config.confirm-switch-modal-confirm', { values: { branch: remoteBranch } })}
		</Button>
	</div>
</Modal>
