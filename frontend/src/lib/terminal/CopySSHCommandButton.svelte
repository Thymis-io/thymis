<script lang="ts">
	import { t } from 'svelte-i18n';
	import Copy from 'lucide-svelte/icons/copy';
	import { toast } from '@zerodevx/svelte-toast';
	import type { DeploymentInfo } from '$lib/deploymentInfo';

	interface Props {
		deploymentInfo: DeploymentInfo;
		class?: string;
	}

	let { deploymentInfo, class: clazz = '' }: Props = $props();

	const copySSHCommand = async () => {
		const response = await fetch(`/api/access_client_token/${deploymentInfo.id}`, {
			method: 'POST'
		});
		if (!response.ok) {
			throw new Error('Failed to get token');
		}
		const token = await response.json();
		const command =
			`ssh -o 'ProxyCommand nix shell github:thymis-io/http-network-relay --command access-client ` +
			`--relay-url ${window.location.protocol == 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/agent/relay_for_clients ` +
			`--secret ${token.token} ${token.deployment_info_id} localhost %p tcp' root@${token.deployment_info_id}.thymis.cloud.internal`;
		await navigator.clipboard.writeText(command);
		toast.push($t('terminal.ssh-copied'), { duration: 2000, initial: 1 });
	};
</script>

<button
	class={'ds-btn ds-btn-sm ds-btn-primary flex items-center gap-2 ' + clazz}
	onclick={copySSHCommand}
>
	<Copy size={15} />
	<span class="whitespace-nowrap">{$t('terminal.copy-ssh')}</span>
</button>
