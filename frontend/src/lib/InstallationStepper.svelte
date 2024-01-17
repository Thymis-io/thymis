<script lang="ts">
	import {
		Stepper,
		Step,
		SlideToggle,
		ProgressBar,
		TabGroup,
		Tab,
		CodeBlock
	} from '@skeletonlabs/skeleton';
	import { Download, Redo, Apple, AppWindow, Wrench } from 'lucide-svelte';

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

<div class="w-full card p-4 text-token">
	{#if !enteredData}
		<Stepper
			stepTerm="Schritt"
			buttonNextLabel="Weiter →"
			buttonBackLabel="← Zurück"
			buttonCompleteLabel="Generieren"
			on:complete={onCompleteHandler}
		>
			<Step>
				<svelte:fragment slot="header">Thymis installieren</svelte:fragment>
				<p>
					Sie können hier einfach ein ISO-Datei oder ein Systemimage für ihr IoT-Gerät erstellen.
				</p>
			</Step>
			<Step>
				<svelte:fragment slot="header">Gerät auswählen</svelte:fragment>
				<p>
					Wir unterstützen momentan x86-basierte und aarch64/ARM64-basierte Geräte. Darunter zählen
					der Raspberry Pi 3, 4 und 5, sowie normale Desktop-Computer.
				</p>
				<select class="select" size="4" bind:value={data.device}>
					<option value="x86">Generisches x86-Gerät (z.B. Desktop-PC)</option>
					<option value="rpi3">Raspberry Pi 3</option>
					<option value="rpi4">Raspberry Pi 4</option>
					<option value="rpi5">Raspbery Pi 5</option>
					<option value="aarch64">Generisches aarch64/ARM64-Gerät</option>
				</select>
			</Step>
			<Step>
				<svelte:fragment slot="header">Verbindungsinformationen</svelte:fragment>
				<p>
					Sobald Thymis installiert ist, können Sie noch viel mehr ganz einfach einrichten. Geben
					Sie erstmal die notwendigen Verbindungsinformationen an, damit Sie das Gerät nach der
					automatischen Installation erreich können.
				</p>
				<div class="space-y-4">
					<label class="label">
						<span>Name</span>
						<input class="input" type="text" placeholder="device01" bind:value={data.displayName} />
					</label>
					<label class="label">
						<span>Hostname</span>
						<input
							class="input"
							type="text"
							placeholder="thymis-device01"
							bind:value={data.hostname}
						/>
					</label>
					<label class="label">
						<span>WLAN SSID - Name der WLAN-Verbindung</span>
						<input class="input" type="text" placeholder="PhoibeWifi" bind:value={data.wifiSSID} />
					</label>
					<label class="label">
						<span>WLAN Passwort</span>
						<input
							class="input"
							type="text"
							placeholder="kept secret"
							bind:value={data.wifiPassword}
						/>
					</label>
					<label class="label">
						<span>Statische IP-Adresse</span>
						<input class="input" type="text" placeholder="192.168.." bind:value={data.staticIP} />
					</label>
					<label class="label">
						<span>SSH Public-Key</span>
						<textarea
							class="textarea"
							rows="4"
							placeholder="ssh-rsa AAA... thymis@mydevice"
							bind:value={data.sshPublicKey}
						/>
					</label>
				</div>
			</Step>
			<Step>
				<svelte:fragment slot="header">Es kann los gehen!</svelte:fragment>
				<p>
					Drücken Sie auf <code>Generieren</code>, um das Systemabbild zu erstellen.
				</p>
			</Step>
		</Stepper>
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
