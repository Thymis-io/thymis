<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Button, Helper, Input, Label, Modal, Spinner, Tooltip } from 'flowbite-svelte';
	import type { DeploymentInfo } from '$lib/deploymentInfo';
	import { fetchWithNotify } from '$lib/fetchWithNotify';
	import { invalidate } from '$app/navigation';

	export let open = false;

	export let deploymentInfo: DeploymentInfo | undefined;
	export let configIdentifier: string | undefined;
	let deviceHost: string = '';
	let publicKey: string = '';
	let isScanningPublicKey = false;
	let scanningPublicKeyError = '';

	const hostValidation = (host: string) => {
		if (host.length === 0) {
			return $t('edit-hostkey.host-empty');
		}

		if (
			!/^([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9])(\.([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]))*$/.test(
				host
			)
		) {
			return $t('edit-hostkey.host-invalid');
		}
	};

	const submitData = async () => {
		if (!configIdentifier) return;
		if (deploymentInfo) {
			const response = await fetchWithNotify(`/api/deployment_info/${deploymentInfo.id}`, {
				method: 'PATCH',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					id: deploymentInfo.id,
					reachable_deployed_host: deviceHost,
					ssh_public_key: publicKey,
					deployed_config_id: configIdentifier
				})
			});
		} else {
			const response = await fetchWithNotify(`/api/create_deployment_info`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					deployed_config_id: configIdentifier,
					reachable_deployed_host: deviceHost,
					ssh_public_key: publicKey
				})
			});
			if (response.ok) {
				deploymentInfo = await response.json();
			}
		}
		await invalidate((url: URL) => url.pathname.search('deployment_info') !== -1);
		await invalidate((url: URL) => url.pathname.search('hardware_device') !== -1);
		open = false;
	};

	const scanPublicKey = async () => {
		scanningPublicKeyError = '';
		isScanningPublicKey = true;

		const response = await fetchWithNotify(
			`/api/scan-public-key?host=${deviceHost}`,
			{
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				}
			},
			{},
			fetch,
			[200, 400]
		);

		isScanningPublicKey = false;

		if (response.ok) {
			const data = await response.json();
			publicKey = data;
		} else {
			const data = await response.json();
			if (response.status === 400 && 'detail' in data) {
				scanningPublicKeyError = data.detail;
				return;
			}
			console.error('Unrecognized Error. Failed to scan public key');
		}
	};
</script>

<Modal
	title={$t('edit-hostkey.title')}
	bind:open
	outsideclose
	size="lg"
	on:open={() => {
		deviceHost = deploymentInfo?.reachable_deployed_host ?? '';
		publicKey = deploymentInfo?.ssh_public_key ?? '';
	}}
	on:open={() => {
		setTimeout(() => {
			const deviceHostHtmlInput = document.getElementById('display-name');
			deviceHostHtmlInput?.focus();
		}, 1);
	}}
	bodyClass="p-4 md:p-5 space-y-4 flex-1"
>
	<form>
		<div class="mb-4">
			<Label for="device-host"
				>{$t('edit-hostkey.device-host')}
				<Input id="device-host" bind:value={deviceHost} />
				{#if hostValidation(deviceHost)}
					<Helper color="red">{hostValidation(deviceHost)}</Helper>
				{:else}
					<Helper color="green">{$t('edit-hostkey.host-valid')}</Helper>
				{/if}
			</Label>
		</div>
		<div class="mb-4 flex gap-2">
			<Label for="public-key" class="w-full">
				{$t('edit-hostkey.public-key')}
				<Input id="public-key" bind:value={publicKey} />
			</Label>
			<div>
				<Button
					class="mt-5 whitespace-nowrap gap-2"
					color="alternative"
					on:click={scanPublicKey}
					disabled={isScanningPublicKey || deviceHost.length === 0}
				>
					{#if isScanningPublicKey}
						<Spinner class="w-5 h-5" />
					{/if}
					{$t('edit-hostkey.scan-public-key')}
				</Button>
				<Tooltip class="whitespace-pre">{$t('edit-hostkey.scan-public-key-tooltip')}</Tooltip>
				<Label color="red">{scanningPublicKeyError}</Label>
			</div>
		</div>
		<div class="flex justify-end">
			<Button
				type="button"
				class="btn btn-primary"
				disabled={!!(hostValidation(deviceHost) || publicKey.length === 0)}
				on:click={submitData}
			>
				{deploymentInfo ? $t('edit-hostkey.update') : $t('edit-hostkey.create')}
			</Button>
		</div>
	</form>
</Modal>
