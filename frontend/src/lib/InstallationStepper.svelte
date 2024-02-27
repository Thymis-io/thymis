<script lang="ts">
	import { ProgressBar, TabGroup, Tab, CodeBlock } from '@skeletonlabs/skeleton';
	import { Button, StepIndicator, Label, Input, Select, Textarea } from 'flowbite-svelte';
	import Download from 'lucide-svelte/icons/download';
	import Redo from 'lucide-svelte/icons/redo';
	import Apple from 'lucide-svelte/icons/apple';
	import AppWindow from 'lucide-svelte/icons/app-window';
	import Wrench from 'lucide-svelte/icons/wrench';

	export let onSubmit: null | ((data: any) => void) = null;

	let data = {
		device: '',
		displayName: '',
		hostname: '',
		wifiSSID: '',
		wifiPassword: '',
		staticIP: '',
		sshPublicKey: ''
	};
	let enteredData = false;
	let imageGenerated = true;
	let tabSetDistroImaging: number = 0;

	let currentStep = 1;
	let steps = [
		'Thymis installieren',
		'Gerät auswählen',
		'Verbindungsinformationen',
		'Es kann los gehen!'
	];

	function onCompleteHandler(e: CustomEvent): void {
		enteredData = true;

		if (data && onSubmit) {
			onSubmit(data);
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
							{ value: 'x86', name: 'Generisches x86-Gerät (z.B. Desktop-PC)' },
							{ value: 'rpi3', name: 'Raspberry Pi 3' },
							{ value: 'rpi4', name: 'Raspberry Pi 4' },
							{ value: 'rpi5', name: 'Raspbery Pi 5' },
							{ value: 'aarch64', name: 'Generisches aarch64/ARM64-Gerät' }
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
						<Label class="mb-2">Hostname</Label>
						<Input placeholder="thymis-device01" bind:value={data.hostname} />
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
					on:click={() => (currentStep += 1)}
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
						<ProgressBar value={undefined} />
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
					<TabGroup>
						<Tab bind:group={tabSetDistroImaging} name="Windows" value={0}>
							<svelte:fragment slot="lead"><AppWindow /></svelte:fragment>
							<span>Windows</span>
						</Tab>
						<Tab bind:group={tabSetDistroImaging} name="macOS" value={1}>
							<svelte:fragment slot="lead"><Apple /></svelte:fragment>
							<span>macOS</span>
						</Tab>
						<Tab bind:group={tabSetDistroImaging} name="Linux" value={2}>
							<svelte:fragment slot="lead"><Wrench /></svelte:fragment>
							<span>Linux</span>
						</Tab>
						<!-- Tab Panels --->
						<svelte:fragment slot="panel">
							<div class="space-y-4">
								{#if tabSetDistroImaging === 0}
									<p>
										Installieren Sie <a
											class="anchor"
											href="https://etcher.balena.io/"
											target="_blank">balena Etcher</a
										>. Nach der Installation können Sie die Image-Datei und einen Datenträger zum
										beschreiben auswählen.
									</p>
								{:else if tabSetDistroImaging === 1}
									<p>
										1. Lassen Sie sich Ihre angeschlossenen Geräte anzeigen und identifizieren Sie
										das Gerät mit <code>/dev/diskX</code>, das für Ihren gewünschten Datenträgen
										steht.
									</p>
									<CodeBlock language="bash" code={`sudo diskutil listDisk`} />
									<p>
										2. Entfernen Sie den Datenträger aus Ihrem Dateisystem (unmount), falls Sie es
										noch nicht gemacht haben.
									</p>
									<CodeBlock language="bash" code={`sudo diskutil unmountDisk /dev/diskX`} />
									<p>
										3. Überschreiben Sie den Datenträger mit dem Systemabbild mit Thymis. Dabei wird
										der Datenträger komplett überschrieben.
									</p>
									<CodeBlock
										language="bash"
										code={`sudo dd if=~/Downloads/thymis-XY.img of=/dev/diskX`}
									/>
								{:else if tabSetDistroImaging === 2}
									<p>
										1. Lassen Sie sich Ihre angeschlossenen Geräte anzeigen und identifizieren Sie
										das Gerät mit <code>/dev/sdX</code>, das für Ihren gewünschten Datenträgen
										steht.
									</p>
									<CodeBlock language="bash" code={`sudo lsblk`} />
									<p>
										2. Entfernen Sie den Datenträger aus Ihrem Dateisystem (unmount), falls Sie es
										noch nicht gemacht haben.
									</p>
									<p>
										3. Überschreiben Sie den Datenträger mit dem Systemabbild mit Thymis. Dabei wird
										der Datenträger komplett überschrieben.
									</p>
									<CodeBlock
										language="bash"
										code={`sudo dd if=~/Downloads/thymis-XY.img of=/dev/sdX`}
									/>
								{/if}
							</div>
						</svelte:fragment>
					</TabGroup>
				</section>
			</div>
		</section>
	{/if}
</div>
