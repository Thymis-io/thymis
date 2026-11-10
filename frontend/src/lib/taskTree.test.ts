import { describe, it, expect } from 'vitest';
import type { TaskShort, TaskState } from './taskstatus';
import {
	buildTaskTree,
	flattenSubtaskTree,
	flattenTaskTree,
	withLiveDescendants,
	type TaskTreeRow
} from './taskTree';

const task = (
	id: string,
	parent: string | null = null,
	{ state = 'completed', second = 0 }: { state?: TaskState; second?: number } = {}
): TaskShort => ({
	id,
	parent_task_id: parent ?? undefined,
	state,
	task_type: 'build_project_task',
	submitted_time: `2026-01-01T00:00:${String(second).padStart(2, '0')}Z`,
	task_submission_data: {}
});

const describeRows = (rows: TaskTreeRow[]) =>
	rows.map((row) =>
		row.kind === 'task' ? `${row.depth}:${row.task.id}` : `${row.depth}:more(${row.hidden})`
	);

const children = (parent: string, count: number) =>
	Array.from({ length: count }, (_, i) => task(`${parent}${i}`, parent, { second: i + 1 }));

describe('flattenTaskTree', () => {
	it('shows 3 children without a more row', () => {
		const rows = flattenTaskTree(buildTaskTree([task('p'), ...children('p', 3)]), new Set());

		expect(describeRows(rows)).toEqual(['0:p', '1:p0', '1:p1', '1:p2']);
	});

	it('hides the 4th child behind a more row', () => {
		const rows = flattenTaskTree(buildTaskTree([task('p'), ...children('p', 4)]), new Set());

		expect(describeRows(rows)).toEqual(['0:p', '1:p0', '1:p1', '1:p2', '1:more(1)']);
	});

	it('shows all children of an expanded parent and offers to show fewer', () => {
		const rows = flattenTaskTree(buildTaskTree([task('p'), ...children('p', 4)]), new Set(['p']));

		expect(describeRows(rows)).toEqual(['0:p', '1:p0', '1:p1', '1:p2', '1:p3', '1:more(1)']);
		expect(rows.at(-1)).toMatchObject({ kind: 'more', parentId: 'p', expanded: true });
	});

	it('applies the limit at each level', () => {
		const tasks = [task('p'), ...children('p', 4), ...children('p0', 5)];

		const collapsed = describeRows(flattenTaskTree(buildTaskTree(tasks), new Set(['p'])));
		const expanded = describeRows(flattenTaskTree(buildTaskTree(tasks), new Set(['p', 'p0'])));

		expect(collapsed).toEqual([
			'0:p',
			'1:p0',
			'2:p00',
			'2:p01',
			'2:p02',
			'2:more(2)',
			'1:p1',
			'1:p2',
			'1:p3',
			'1:more(1)'
		]);
		expect(expanded.filter((row) => row.startsWith('2:p0'))).toHaveLength(5);
	});

	it('keeps children in submission order whatever their state', () => {
		const tasks = [
			task('p'),
			task('running', 'p', { state: 'running', second: 4 }),
			task('completed', 'p', { state: 'completed', second: 1 }),
			task('failed', 'p', { state: 'failed', second: 3 }),
			task('pending', 'p', { state: 'pending', second: 2 })
		];

		const rows = flattenTaskTree(buildTaskTree(tasks), new Set(['p']));

		expect(describeRows(rows)).toEqual([
			'0:p',
			'1:completed',
			'1:pending',
			'1:failed',
			'1:running',
			'1:more(1)'
		]);
	});
});

describe('buildTaskTree', () => {
	it('makes a task whose parent is not loaded a top-level task, newest first', () => {
		const roots = buildTaskTree([
			task('old', null, { second: 1 }),
			task('orphan', 'missing', { second: 2 })
		]);

		expect(roots.map((root) => root.task.id)).toEqual(['orphan', 'old']);
	});
});

describe('flattenSubtaskTree', () => {
	it("draws a task's children at depth 0, in submission order and limited, with its more row", () => {
		const subtasks = [
			task('fourth', 'p', { state: 'running', second: 4 }),
			task('second', 'p', { state: 'pending', second: 2 }),
			task('first', 'p', { state: 'completed', second: 1 }),
			task('third', 'p', { state: 'failed', second: 3 }),
			task('below', 'first', { second: 5 })
		];

		const rows = flattenSubtaskTree(task('p', 'grandparent'), subtasks, new Set());

		expect(describeRows(rows)).toEqual(['0:first', '1:below', '0:second', '0:third', '0:more(1)']);
		expect(rows.at(-1)).toMatchObject({ parentId: 'p' });
	});

	it('keeps `parent` as the root when a cycle leads back to it', () => {
		const rows = flattenSubtaskTree(task('p', 'c'), [task('c', 'p')], new Set());

		expect(describeRows(rows)).toEqual(['0:c']);
	});
});

describe('withLiveDescendants', () => {
	it('overlays live versions and adds live tasks below loaded or anchor tasks', () => {
		const loaded = [task('root'), task('child', 'root')];
		const live = {
			child: task('child', 'root', { state: 'running' }),
			grandchild: task('grandchild', 'child'),
			underAnchor: task('underAnchor', 'anchor'),
			unrelated: task('unrelated')
		};

		const tasks = withLiveDescendants(loaded, live, ['anchor']);

		expect(tasks.map((t) => t.id).sort()).toEqual(['child', 'grandchild', 'root', 'underAnchor']);
		expect(tasks.find((t) => t.id === 'child')?.state).toBe('running');
	});

	it('terminates on a cycle that never reaches an anchor', () => {
		const live = { a: task('a', 'b'), b: task('b', 'a') };

		expect(withLiveDescendants([task('root')], live).map((t) => t.id)).toEqual(['root']);
	});
});
