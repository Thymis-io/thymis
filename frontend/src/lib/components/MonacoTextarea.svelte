<script lang="ts">
	// another approach? github.com/sonyarianto/sveltekit-monaco-editor/blob/main/src/routes/%2Bpage.svelte
	import { onDestroy, onMount } from 'svelte';
	import type * as Monaco from 'monaco-editor/esm/vs/editor/editor.api';
	import { nixLanguage, nixLanguageConfiguration } from './monaconix';

	let editor: Monaco.editor.IStandaloneCodeEditor;
	let monaco: typeof Monaco;
	let editorContainer: HTMLElement;

	let props: {
		placeholder: string | null;
		onChange?: (value: string) => void;
		value: string | null;
		disabled: boolean;
		language?: string;
	} = $props();

	onMount(async () => {
		// Import our 'monaco.ts' file here
		// (onMount() will only be executed in the browser, which is what we want)
		monaco = (await import('./monaco')).default;

		monaco.languages.register({ id: 'nix' });
		monaco.languages.setMonarchTokensProvider('nix', nixLanguage);
		monaco.languages.setLanguageConfiguration('nix', nixLanguageConfiguration);

		// Your monaco instance is ready, let's display some code!
		editor = monaco.editor.create(editorContainer, {
			value: props.value || '',
			language: props.language || 'nix',
			theme: 'vs-dark',
			readOnly: props.disabled
		});
		editor.getModel()?.onDidChangeContent(() => {
			if (props.onChange) {
				props.onChange(editor.getValue());
			}
		});
	});

	onDestroy(() => {
		monaco?.editor.getModels().forEach((model) => model.dispose());
		editor?.dispose();
	});
</script>

<div class="w-full h-140">
	<div class="h-full" bind:this={editorContainer}></div>
</div>
