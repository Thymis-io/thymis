<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Spinner } from 'flowbite-svelte';
	import Check from 'lucide-svelte/icons/check';
	import Hourglass from 'lucide-svelte/icons/hourglass';
	import X from 'lucide-svelte/icons/x';

	interface Props {
		inputUrl?: string;
		apiSecret?: string | null;
	}

	let { inputUrl, apiSecret }: Props = $props();

	$effect(() => {
		if (inputUrl) {
			checkRepoStatus(inputUrl, apiSecret);
		}
	});

	type AccessStatus =
		| { status: 'pending' }
		| { status: 'success'; commit_hash?: string }
		| { status: 'error'; detail: string }
		| { status: 'unknown' }
		| { status: 'rate_limited' };

	let repoAccessStatus = $state<{
		prefetch: AccessStatus;
		api: AccessStatus;
	} | null>(null);

	const checkRepoStatus = async (inputUrl: string, apiSecret?: string | null) => {
		repoAccessStatus = { prefetch: { status: 'pending' }, api: { status: 'pending' } };
		const searchParams = new URLSearchParams();
		if (apiSecret) {
			searchParams.set('api_key_secret', apiSecret);
		}

		fetch(
			`/api/external-repositories/test-flake-ref/prefetch/${encodeURIComponent(inputUrl)}?${searchParams.toString()}`
		).then(async (res) => {
			const result = (await res.json()) as AccessStatus;
			if (repoAccessStatus) repoAccessStatus.prefetch = result;
		});

		fetch(
			`/api/external-repositories/test-flake-ref/api-access/${encodeURIComponent(inputUrl)}?${searchParams.toString()}`
		).then(async (res) => {
			const result = (await res.json()) as AccessStatus;
			if (repoAccessStatus) repoAccessStatus.api = result;
		});
	};
</script>

{#if inputUrl}
	<p class="md-4">
		{$t('settings.repo.checking-access', { values: { url: inputUrl } })}
	</p>
{/if}
{#if repoAccessStatus}
	<div class="flex gap-2 text-base">
		{#if repoAccessStatus.prefetch.status === 'pending'}
			<Spinner size="4" />
			{$t('settings.repo.check-prefetch')}
		{:else if repoAccessStatus.prefetch.status === 'success'}
			<Check class="flex-shrink-0 text-green-500" size="20" />
			{$t('settings.repo.check-prefetch-success')}
		{:else if repoAccessStatus.prefetch.status === 'rate_limited'}
			<Hourglass class="flex-shrink-0 text-yellow-500" size="20" />
			{$t('settings.repo.check-rate-limited')}
		{:else if repoAccessStatus.prefetch.status === 'error'}
			<X class="flex-shrink-0 text-red-500" size="20" />
			<span class="flex-shrink-0">{$t('settings.repo.check-prefetch-error')}:</span>
			<span class="whitespace-pre">{repoAccessStatus.prefetch.detail}</span>
		{/if}
	</div>
	<div class="flex items-center gap-2 text-base">
		{#if repoAccessStatus.api.status === 'pending'}
			<Spinner size="4" />
			{$t('settings.repo.check-api')}
		{:else if repoAccessStatus.api.status === 'success'}
			<Check class="flex-shrink-0 text-green-500" size="20" />
			{$t('settings.repo.check-api-success', {
				values: { commit_hash: repoAccessStatus.api.commit_hash }
			})}
		{:else if repoAccessStatus.api.status === 'rate_limited'}
			<Hourglass class="flex-shrink-0 text-yellow-500" size="20" />
			{$t('settings.repo.check-rate-limited')}
		{:else if repoAccessStatus.api.status === 'error'}
			<X class="flex-shrink-0 text-red-500" size="20" />
			<span class="flex-shrink-0">{$t('settings.repo.check-api-error')}:</span>
			<span class="whitespace-pre">{repoAccessStatus.api.detail}</span>
		{/if}
	</div>
{/if}
