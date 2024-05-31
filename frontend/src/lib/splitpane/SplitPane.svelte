<script>
	import { createEventDispatcher } from 'svelte';
	import { constrain } from './utils.js';

	/** @type {ReturnType<typeof createEventDispatcher<{ change: undefined }>>} */
	const dispatch = createEventDispatcher();

	/** @type {string | undefined} */
	export let id = undefined;

	/** @type {'horizontal' | 'vertical'} */
	export let type;

	/** @type {import('./types').Length} */
	export let pos = '50%';

	/** @type {import('./types').Length} */
	export let min = '0%';

	/** @type {import('./types').Length} */
	export let max = '100%';

	export let disabled = false;

	/** @type {'min' | 'max'}*/
	export let priority = 'min';

	/** @type {HTMLElement} */
	let splitpane_container;

	let dragging = false;
	let w = 0;
	let h = 0;

	$: position = pos;

	// constrain position
	$: if (splitpane_container) {
		const size = type === 'horizontal' ? w : h;
		position = constrain(splitpane_container, size, min, max, position, priority);
	}

	/**
	 * @param {number} x
	 * @param {number} y
	 */
	function update(x, y) {
		if (disabled) return;

		const { top, left } = splitpane_container.getBoundingClientRect();

		const pos_px = type === 'horizontal' ? x - left : y - top;
		const size = type === 'horizontal' ? w : h;

		position = pos.endsWith('%') ? `${(100 * pos_px) / size}%` : `${pos_px}px`;

		dispatch('change');
	}

	/**
	 * @param {HTMLElement} node
	 * @param {(event: PointerEvent) => void} callback
	 */
	function drag(node, callback) {
		/** @param {PointerEvent} event */
		const pointerdown = (event) => {
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
	class="splitpane_container {type}"
	bind:this={splitpane_container}
	bind:clientWidth={w}
	bind:clientHeight={h}
	style="--pos: {position}"
>
	<div class="pane">
		<slot name="a" />
	</div>

	<div class="pane">
		<slot name="b" />
	</div>

	{#if pos !== '0%' && pos !== '100%'}
		<div class="{type} divider" class:disabled use:drag={(e) => update(e.clientX, e.clientY)} />
	{/if}
</div>

{#if dragging}
	<div class="mousecatcher" />
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
