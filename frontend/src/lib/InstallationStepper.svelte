<script lang="ts">
	import {
		Button,
		StepIndicator,
		Label,
		Input,
		Select,
		Textarea,
		Progressbar,
		Tabs,
		TabItem
	} from 'flowbite-svelte';
	import Download from 'lucide-svelte/icons/download';
	import Redo from 'lucide-svelte/icons/redo';
	import Apple from 'lucide-svelte/icons/apple';
	import AppWindow from 'lucide-svelte/icons/app-window';
	import Wrench from 'lucide-svelte/icons/wrench';
	import type { Device } from './state';

	export let onSubmit: null | ((data: Device) => void) = null;

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
		'Thymis installieren',
		'Gerät auswählen',
		'Verbindungsinformationen',
		'Es kann los gehen!'
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
						type: 'thymis_controller.models.modules.thymis.ThymisDevice',
						settings: {
							device_type: { value: data.device }
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
					<p>
						Sie können hier einfach ein ISO-Datei oder ein Systemimage für ihr IoT-Gerät erstellen.
					</p>
				{:else if currentStep === 2}
					<p>
						Wir unterstützen momentan x86-basierte und aarch64/ARM64-basierte Geräte. Darunter
						zählen der Raspberry Pi 3, 4 und 5, sowie normale Desktop-Computer.
					</p>
					<Select
						bind:value={data.device}
						items={[
							{ value: 'generic-x86_64', name: 'Generisches x86-Gerät (z.B. Desktop-PC)' },
							{ value: 'raspberry-pi-4', name: 'Raspberry Pi 4' },
							{ value: 'generic-aarch64', name: 'Generisches aarch64/ARM64-Gerät' }
						]}
					/>
				{:else if currentStep === 3}
					<p>
						Sobald Thymis installiert ist, können Sie noch viel mehr ganz einfach einrichten. Geben
						Sie erstmal die notwendigen Verbindungsinformationen an, damit Sie das Gerät nach der
						automatischen Installation erreich können.
					</p>
					<div>
						<Label class="mb-2">Name</Label>
						<Input placeholder="device01" bind:value={data.displayName} />
					</div>
					<div>
						<Label class="mb-2">Deployment-Ziel - Hostname oder IP-Adresse</Label>
						<Input placeholder="thymis-device01" bind:value={data.targetHost} />
					</div>
					<div>
						<Label class="mb-2">WLAN SSID - Name der WLAN-Verbindung</Label>
						<Input placeholder="PhoibeWifi" bind:value={data.wifiSSID} />
					</div>
					<div>
						<Label class="mb-2">WLAN Passwort</Label>
						<Input placeholder="kept secret" bind:value={data.wifiPassword} />
					</div>
					<div>
						<Label class="mb-2">Statische IP-Adresse</Label>
						<Input placeholder="192.168.." bind:value={data.staticIP} />
					</div>
					<div>
						<Label class="mb-2">SSH Public-Key</Label>
						<Textarea placeholder="192.168.." rows="4" bind:value={data.sshPublicKey} />
					</div>
				{:else if currentStep === 4}
					<p>
						Drücken Sie auf <code>Generieren</code>, um das Systemabbild zu erstellen.
					</p>
					<Button color={'alternative'} on:click={() => (enteredData = true)}>Generieren</Button>
				{/if}
			</div>
			<div class="flex justify-between">
				<Button
					color={'alternative'}
					disabled={currentStep === 1}
					on:click={() => (currentStep -= 1)}
				>
					Zurück
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
					Weiter
				</Button>
			</div>
		</div>
	{:else}
		<header class="card-header text-2xl font-bold">
			{#if !imageGenerated}
				Wir erstellen Ihr persönliches Systemabbild von Thymis.
			{:else}
				Ihr Systemabbild ist bereit!
			{/if}
		</header>
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
						<span><Download /></span>
						<span>Image herunterladen</span>
					</button>
					<button
						class="btn bg-gradient-to-br variant-filled"
						disabled={!imageGenerated}
						on:click={reset}
					>
						<span><Redo /></span>
						<span>weiteres Image erstellen</span>
					</button>
				</div>
			</div>
			<hr class="!border-t-4" />
			<h3 class="h3 pb-2 pt-4">
				{!imageGenerated ? 'Das können Sie währenddessen machen' : 'Das sind die nächsten Schritte'}
			</h3>
			<div class="space-y-8">
				<section class="space-y-4">
					<h4 class="h4">Einen Datenträgen vorbereiten</h4>
					<p>
						Legen Sie sich einen passenden Datenträger zu Ihrem Gerät bereit. Überlicherweise werden
						bei ISOs USB-Sticks oder CDs/DVDs verwendet. Bei Systemabbildern als .img wird ein
						Datenträger, wie bspw. eine microSD-Karte mit dem System bespielt.
					</p>
					<aside class="alert variant-ghost-warning">
						<div class="alert-message">
							<p>Der Datenträger muss mindestens 4 GB umfassen können.</p>
						</div>
					</aside>
				</section>
				<section class="space-y-4">
					<h4 class="h4">
						{!imageGenerated
							? 'Software zum Imagen installieren'
							: 'Systemabbild auf Datenträgen kopieren'}
					</h4>
					<p>
						Das Systemabbild muss auf den Datenträger installiert werden. Wir geben Ihnen mehrere
						Empfehlungen, wie Sie das machen können.
					</p>
					<aside class="alert variant-ghost-error">
						<div class="alert-message">
							<p>Der Datenträger wird beim Beschreiben formatiert. Alle Daten werden gelöscht!</p>
						</div>
					</aside>
					<p>Sie brauchen Superuser/Root/Administrator-Rechte für den diesen Schritt.</p>
					<Tabs>
						<TabItem name="Windows">
							<svelte:fragment slot="title"><AppWindow />Windows</svelte:fragment>
							<p>
								Installieren Sie <a class="anchor" href="https://etcher.balena.io/" target="_blank"
									>balena Etcher</a
								>. Nach der Installation können Sie die Image-Datei und einen Datenträger zum
								beschreiben auswählen.
							</p>
						</TabItem>
						<TabItem name="macOS">
							<svelte:fragment slot="title"><Apple />macOS</svelte:fragment>
							<p>
								1. Lassen Sie sich Ihre angeschlossenen Geräte anzeigen und identifizieren Sie das
								Gerät mit <code>/dev/diskX</code>, das für Ihren gewünschten Datenträgen steht.
							</p>
							<!-- <CodeBlock language="bash" code={`sudo diskutil listDisk`} /> -->
							<code>sudo diskutil listDisk</code>
							<p>
								2. Entfernen Sie den Datenträger aus Ihrem Dateisystem (unmount), falls Sie es noch
								nicht gemacht haben.
							</p>
							<!-- <CodeBlock language="bash" code={`sudo diskutil unmountDisk /dev/diskX`} /> -->
							<code>sudo diskutil unmountDisk /dev/diskX</code>
							<p>
								3. Überschreiben Sie den Datenträger mit dem Systemabbild mit Thymis. Dabei wird der
								Datenträger komplett überschrieben.
							</p>
							<!-- <CodeBlock
								language="bash"
								code={`sudo dd if=~/Downloads/thymis-XY.img of=/dev/diskX`}
							/> -->
							<code>sudo dd if=~/Downloads/thymis-XY.img of=/dev/diskX</code>
						</TabItem>
						<TabItem name="Linux">
							<svelte:fragment slot="title"><Wrench />Linux</svelte:fragment>
							<p>
								1. Lassen Sie sich Ihre angeschlossenen Geräte anzeigen und identifizieren Sie das
								Gerät mit <code>/dev/sdX</code>, das für Ihren gewünschten Datenträgen steht.
							</p>
							<!-- <CodeBlock language="bash" code={`sudo lsblk`} /> -->
							<code>sudo lsblk</code>
							<p>
								2. Entfernen Sie den Datenträger aus Ihrem Dateisystem (unmount), falls Sie es noch
								nicht gemacht haben.
							</p>
							<p>
								3. Überschreiben Sie den Datenträger mit dem Systemabbild mit Thymis. Dabei wird der
								Datenträger komplett überschrieben.
							</p>
							<!-- <CodeBlock
								language="bash"
								code={`sudo dd if=~/Downloads/thymis-XY.img of=/dev/sdX`}
							/> -->
							<code>sudo dd if=~/Downloads/thymis-XY.img of=/dev/sdX</code>
						</TabItem>
					</Tabs>
				</section>
			</div>
		</section>
	{/if}
</div>
