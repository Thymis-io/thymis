import { describe, it, expect } from 'vitest';
import { aggregateTransfers, type NixTransferSummary, type TaskProcess } from './taskstatus';

const processWith = (index: number, transfer: NixTransferSummary): TaskProcess =>
	({
		task_id: 'task',
		process_index: index,
		nix_status: { done: 0, expected: 0, running: 0, failed: 0, transfer }
	}) as TaskProcess;

describe('aggregateTransfers', () => {
	it('sums the transfers of all processes per direction', () => {
		const transfers = aggregateTransfers([
			processWith(0, { download: { done: 100, expected: 200, running: 2, failed: 0 } }),
			processWith(1, { upload: { done: 300, expected: 400, running: 1, failed: 1 } }),
			processWith(2, { upload: { done: 50, expected: 50, running: 0, failed: 0 } })
		]);

		expect(transfers).toEqual([
			{ direction: 'download', done: 100, expected: 200, running: 2, failed: 0 },
			{ direction: 'upload', done: 350, expected: 450, running: 1, failed: 1 }
		]);
	});

	it('reports a direction that only some processes are transferring', () => {
		const transfers = aggregateTransfers([
			processWith(0, { other: { done: 4096, expected: 8192, running: 1, failed: 0 } })
		]);

		expect(transfers).toEqual([
			{ direction: 'other', done: 4096, expected: 8192, running: 1, failed: 0 }
		]);
	});

	it('ignores processes without transfer status', () => {
		const withoutTransfer = { task_id: 'task', process_index: 0 } as TaskProcess;

		expect(aggregateTransfers([withoutTransfer])).toEqual([]);
		expect(aggregateTransfers(undefined)).toEqual([]);
	});
});
