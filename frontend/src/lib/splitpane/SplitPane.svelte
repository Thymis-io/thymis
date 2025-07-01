<script lang="ts">
	import type { Snippet } from 'svelte';
	import { constrain } from './utils.js';
	import type { Length } from './types';

	interface Props {
		id?: string;
		type: 'horizontal' | 'vertical';
		reverse?: boolean;
		pos?: Length;
		min?: Length;
		max?: Length;
		disabled?: boolean;
		priority?: 'min' | 'max';
		class?: string;
		leftPaneClass?: string;
		rightPaneClass?: string;
		dividerClass?: string;
		onchange?: (position: Length) => void;
		a?: Snippet;
		b?: Snippet;
	}

	let {
		id = undefined,
		type,
		reverse = false,
		pos = '50%',
		min = '0%',
		max = '100%',
		disabled = false,
		priority = 'min',
		class: clazz = '',
		leftPaneClass = '',
		rightPaneClass = '',
		dividerClass = '',
		onchange,
		a,
		b
	}: Props = $props();

	let splitpane_container: HTMLElement;

	let dragging = $state(false);
	let w = $state(0);
	let h = $state(0);

	let position = $state(pos);

	// constrain position
	$effect(() => {
		if (splitpane_container) {
			const size = type === 'horizontal' ? w : h;
			position = constrain(splitpane_container, size, min, max, position, priority);
		}
	});

	function update(x: number, y: number) {
		if (disabled) return;

		const { top, left } = splitpane_container.getBoundingClientRect();
		const size = type === 'horizontal' ? w : h;
		const offset = type === 'horizontal' ? x - left : y - top;
		const pos_px = reverse ? size - offset : offset;

		position = pos.endsWith('%') ? `${(100 * pos_px) / size}%` : `${pos_px}px`;

		onchange?.(position);
	}

	function drag(node: HTMLElement, callback: (event: PointerEvent) => void) {
		const pointerdown = (event: PointerEvent) => {
			if (
				(event.pointerType === 'mouse' && event.button === 2) ||
				(event.pointerType !== 'mouse' && !event.isPrimary)
			)
				return;

			node.setPointerCapture(event.pointerId);

			event.preventDefault();

			dragging = true;

			const onpointerup = () => {
				dragging = false;

				node.setPointerCapture(event.pointerId);

				window.removeEventListener('pointermove', callback, false);
				window.removeEventListener('pointerup', onpointerup, false);
			};

			window.addEventListener('pointermove', callback, false);
			window.addEventListener('pointerup', onpointerup, false);
		};

		node.addEventListener('pointerdown', pointerdown, { capture: true, passive: false });

		return {
			destroy() {
				node.removeEventListener('pointerdown', pointerdown);
			}
		};
	}
</script>

<div
	data-pane={id}
	class="splitpane_container {type} {reverse ? 'reverse' : ''} {clazz || ''}"
	bind:this={splitpane_container}
	bind:clientWidth={w}
	bind:clientHeight={h}
	style="--pos: {position}"
>
	<div class="pane {leftPaneClass || ''}">
		{@render a?.()}
	</div>

	<div class="pane {rightPaneClass || ''}">
		{@render b?.()}
	</div>

	{#if pos !== '0%' && pos !== '100%'}
		<div
			class="{type} divider {dividerClass || ''}"
			class:disabled
			use:drag={(e) => update(e.clientX, e.clientY)}
		></div>
	{/if}
</div>

{#if dragging}
	<div class="mousecatcher"></div>
{/if}

<style>
	.splitpane_container {
		--sp-thickness: var(--thickness, 8px);
		--sp-color: var(--color, transparent);
		display: grid;
		position: relative;
		width: 100%;
		height: 100%;
	}

	.splitpane_container.vertical {
		grid-template-rows: var(--pos) 1fr;
	}

	.splitpane_container.horizontal {
		grid-template-columns: var(--pos) 1fr;
	}

	.splitpane_container.horizontal.reverse {
		grid-template-columns: 1fr var(--pos);
	}

	.splitpane_container.vertical.reverse {
		grid-template-rows: 1fr var(--pos);
	}

	.pane {
		width: 100%;
		height: 100%;
		overflow: auto;
	}

	.pane > :global(*) {
		width: 100%;
		height: 100%;
		overflow: hidden;
	}

	.mousecatcher {
		position: absolute;
		left: 0;
		top: 0;
		width: 100%;
		height: 100%;
		background: rgba(255, 255, 255, 0.0001);
	}

	.divider {
		position: absolute;
		touch-action: none !important;
	}

	.divider::after {
		content: '';
		position: absolute;
		background-color: var(--sp-color);
	}

	.horizontal > .divider {
		padding: 0 calc(0.5 * var(--sp-thickness));
		width: 0;
		height: 100%;
		cursor: ew-resize;
		left: var(--pos);
		transform: translate(calc(-0.5 * var(--sp-thickness)), 0);
	}

	.horizontal.reverse > .divider {
		left: auto;
		right: var(--pos);
		transform: translate(calc(0.5 * var(--sp-thickness)), 0);
	}

	.horizontal > .divider.disabled {
		cursor: default;
	}

	.horizontal > .divider::after {
		left: 50%;
		top: 0;
		width: 1px;
		height: 100%;
	}

	.vertical > .divider {
		padding: calc(0.5 * var(--sp-thickness)) 0;
		width: 100%;
		height: 0;
		cursor: ns-resize;
		top: var(--pos);
		transform: translate(0, calc(-0.5 * var(--sp-thickness)));
	}

	.vertical.reverse > .divider {
		top: auto;
		bottom: var(--pos);
		transform: translate(0, calc(0.5 * var(--sp-thickness)));
	}

	.vertical > .divider.disabled {
		cursor: default;
	}

	.vertical > .divider::after {
		top: 50%;
		left: 0;
		width: 100%;
		height: 1px;
	}
</style>
