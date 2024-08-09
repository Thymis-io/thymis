<script lang="ts">
	import { t } from 'svelte-i18n';
	import {
		Alert,
		Button,
		StepIndicator,
		Label,
		Input,
		Select,
		Textarea,
		Progressbar,
		Tabs,
		TabItem,
		Heading,
		P
	} from 'flowbite-svelte';
	import Download from 'lucide-svelte/icons/download';
	import Redo from 'lucide-svelte/icons/redo';
	import Apple from 'lucide-svelte/icons/apple';
	import AppWindow from 'lucide-svelte/icons/app-window';
	import Wrench from 'lucide-svelte/icons/wrench';
	import type { Device, Module } from '../../lib/state';
	import ConfigSelectOne from '../../lib/config/ConfigSelectOne.svelte';

	export let onSubmit: null | ((data: Device) => void) = null;
	export let thymisDevice: Module | undefined = undefined;

	let data = {
		device: '',
		displayName: '',
		targetHost: '',
		wifiSSID: '',
		wifiPassword: '',
		staticIP: '',
		sshPublicKey: ''
	};
	let enteredData = false;
	let imageGenerated = true;

	let currentStep = 1;
	let steps = [
		$t('create-device.step-1.title'),
		$t('create-device.step-2.title'),
		$t('create-device.step-3.title'),
		$t('create-device.step-4.title')
	];

	function onCompleteHandler(): void {
		enteredData = true;

		if (data && onSubmit) {
			onSubmit({
				displayName: data.displayName,
				identifier: data.displayName.toLowerCase().replaceAll(' ', '-'),
				targetHost: data.targetHost,
				modules: [
					{
						type: 'thymis_controller.modules.thymis.ThymisDevice',
						settings: {
							device_type: data.device
						}
					}
				],
				tags: []
			});
		}
	}
	function reset(): void {
		enteredData = false;
		imageGenerated = false;
	}
</script>

<div class="w-full p-2">
	{#if !enteredData}
		<div class="flex flex-col gap-4">
			<StepIndicator {currentStep} {steps} />
			<div class="h-96 overflow-y-auto space-y-4">
				{#if currentStep === 1}
					<p>{$t('create-device.step-1.info')}</p>
				{:else if currentStep === 2}
					<p>{$t('create-device.step-2.info')}</p>
					{#if thymisDevice}
						<ConfigSelectOne
							value={data.device}
							change={(value) => (data.device = value)}
							setting={thymisDevice.settings.device_type}
							options={thymisDevice.settings.device_type.options}
						/>
					{/if}
				{:else if currentStep === 3}
					<p>{$t('create-device.step-3.info')}</p>
					<div>
						<Label class="mb-2">{$t('create-device.step-3.device-name')}</Label>
						<Input placeholder="device01" bind:value={data.displayName} />
					</div>
					<div>
						<Label class="mb-2">{$t('create-device.step-3.hostname')}</Label>
						<Input placeholder="thymis-device01" bind:value={data.targetHost} />
					</div>
					<div>
						<Label class="mb-2">{$t('create-device.step-3.wlan-ssid')}</Label>
						<Input placeholder="PhoibeWifi" bind:value={data.wifiSSID} />
					</div>
					<div>
						<Label class="mb-2">{$t('create-device.step-3.wlan-password')}</Label>
						<Input placeholder="kept secret" bind:value={data.wifiPassword} />
					</div>
					<div>
						<Label class="mb-2">{$t('create-device.step-3.static-network-ip')}</Label>
						<Input placeholder="192.168.." bind:value={data.staticIP} />
					</div>
					<div>
						<Label class="mb-2">{$t('create-device.step-3.ssh-pubkey')}</Label>
						<Textarea placeholder="192.168.." rows="4" bind:value={data.sshPublicKey} />
					</div>
				{:else if currentStep === 4}
					<p>{$t('create-device.step-4.info')}</p>
					<Button color={'alternative'} on:click={() => (enteredData = true)}>
						{$t('create-device.step-4.complete')}
					</Button>
				{/if}
			</div>
			<div class="flex justify-between">
				<Button
					color={'alternative'}
					disabled={currentStep === 1}
					on:click={() => (currentStep -= 1)}
				>
					{$t('create-device.back')}
				</Button>
				<Button
					color={'alternative'}
					disabled={currentStep === steps.length}
					on:click={() => {
						currentStep += 1;

						if (currentStep === steps.length && !enteredData) {
							onCompleteHandler();
						}
					}}
				>
					{$t('create-device.next')}
				</Button>
			</div>
		</div>
	{:else}
		<Heading tag="h2" class="pb-2">
			{#if !imageGenerated}
				{$t('create-device.finish.title.generating')}
			{:else}
				{$t('create-device.finish.title.generated')}
			{/if}
		</Heading>
		<section class="p-4">
			<div class="pb-4 space-y-4">
				{#if !imageGenerated}
					<div>
						<Progressbar progress={undefined} />
					</div>
				{/if}
				<div class="space-x-4">
					<button
						class="btn bg-gradient-to-br variant-gradient-primary-secondary"
						disabled={!imageGenerated}
					>
						<P><Download /></P>
						<P>{$t('create-device.finish.download')}</P>
					</button>
					<button
						class="btn bg-gradient-to-br variant-filled"
						disabled={!imageGenerated}
						on:click={reset}
					>
						<P><Redo /></P>
						<P>{$t('create-device.finish.new')}</P>
					</button>
				</div>
			</div>
			<hr class="!border-t-4 py-2" />
			<Heading tag="h3" class="py-4">
				{!imageGenerated
					? $t('create-device.finish.next-steps.generating')
					: $t('create-device.finish.next-steps.generated')}
			</Heading>
			<div class="space-y-8">
				<section class="space-y-4">
					<Heading tag="h4">{$t('create-device.finish.sd-title')}</Heading>
					<P>{$t('create-device.finish.sd-info')}</P>
					<Alert color="yellow">
						<P color="yellow">{$t('create-device.finish.sd-size-warning')}</P>
					</Alert>
				</section>
				<section class="space-y-4">
					<Heading tag="h4">
						{!imageGenerated
							? $t('create-device.finish.software-title.generating')
							: $t('create-device.finish.software-title.generated')}
					</Heading>
					<P>{$t('create-device.finish.software-info')}</P>
					<Alert color="red">
						<P color="red">{$t('create-device.finish.software-warning')}</P>
					</Alert>
					<P>{$t('create-device.finish.software-permissions')}</P>
					<Tabs>
						<TabItem name="Windows" open={true}>
							<svelte:fragment slot="title"><AppWindow />Windows</svelte:fragment>
							<P>
								{@html $t('create-device.finish.software-windows.install', {
									values: {
										balena:
											'<a class="text-blue-600" href="https://etcher.balena.io/" target="_blank">balena Etcher</a>'
									}
								})}
							</P>
						</TabItem>
						<TabItem name="macOS">
							<svelte:fragment slot="title"><Apple />macOS</svelte:fragment>
							<P>{$t('create-device.finish.software-macos.step-1')}</P>
							<!-- <CodeBlock language="bash" code={`sudo diskutil listDisk`} /> -->
							<code class="text-gray-500">sudo diskutil listDisk</code>
							<P>{$t('create-device.finish.software-macos.step-2')}</P>
							<!-- <CodeBlock language="bash" code={`sudo diskutil unmountDisk /dev/diskX`} /> -->
							<code class="text-gray-500">sudo diskutil unmountDisk /dev/diskX</code>
							<P>{$t('create-device.finish.software-macos.step-3')}</P>
							<!-- <CodeBlock
								language="bash"
								code={`sudo dd if=~/Downloads/thymis-XY.img of=/dev/diskX`}
							/> -->
							<code class="text-gray-500">sudo dd if=~/Downloads/thymis-XY.img of=/dev/diskX</code>
						</TabItem>
						<TabItem name="Linux">
							<svelte:fragment slot="title"><Wrench />Linux</svelte:fragment>
							<P>{$t('create-device.finish.software-linux.step-1')}</P>
							<!-- <CodeBlock language="bash" code={`sudo lsblk`} /> -->
							<code class="text-gray-500">sudo lsblk</code>
							<P>{$t('create-device.finish.software-linux.step-3')}</P>
							<P>{$t('create-device.finish.software-linux.step-3')}</P>
							<!-- <CodeBlock
								language="bash"
								code={`sudo dd if=~/Downloads/thymis-XY.img of=/dev/sdX`}
							/> -->
							<code class="text-gray-500">sudo dd if=~/Downloads/thymis-XY.img of=/dev/sdX</code>
						</TabItem>
					</Tabs>
				</section>
			</div>
		</section>
	{/if}
</div>
