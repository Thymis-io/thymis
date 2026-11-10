import type { TaskShort } from './taskstatus';

/** Children shown before a "more" row. */
export const VISIBLE_CHILDREN = 3;

export type TaskNode = { task: TaskShort; children: TaskNode[] };

/** A task, or the "more" row toggling a parent's `hidden` children. */
export type TaskTreeRow =
	| { kind: 'task'; task: TaskShort; depth: number }
	| { kind: 'more'; parentId: string; hidden: number; expanded: boolean; depth: number };

/** Tasks whose parent isn't in `tasks` become roots, newest first; tasks on a cycle are left out. */
export const buildTaskTree = (tasks: TaskShort[]): TaskNode[] => {
	const nodes = new Map<string, TaskNode>(tasks.map((task) => [task.id, { task, children: [] }]));
	const roots: TaskNode[] = [];
	for (const node of nodes.values()) {
		const parent = node.task.parent_task_id && nodes.get(node.task.parent_task_id);
		(parent ? parent.children : roots).push(node);
	}

	// Children oldest first so rows stay put as states change.
	for (const node of nodes.values()) {
		node.children.sort(
			(a, b) =>
				a.task.submitted_time.localeCompare(b.task.submitted_time) ||
				a.task.id.localeCompare(b.task.id)
		);
	}
	return roots.sort((a, b) => b.task.submitted_time.localeCompare(a.task.submitted_time));
};

/** Depth-first rows; each task shows VISIBLE_CHILDREN children unless it is in `expanded`. */
export const flattenTaskTree = (
	roots: TaskNode[],
	expanded: ReadonlySet<string>,
	rootDepth = 0
): TaskTreeRow[] => {
	const rows: TaskTreeRow[] = [];
	const visit = (node: TaskNode, depth: number) => {
		rows.push({ kind: 'task', task: node.task, depth });
		const isExpanded = expanded.has(node.task.id);
		const shown = isExpanded ? node.children : node.children.slice(0, VISIBLE_CHILDREN);
		for (const child of shown) visit(child, depth + 1);
		if (node.children.length > VISIBLE_CHILDREN) {
			rows.push({
				kind: 'more',
				parentId: node.task.id,
				hidden: node.children.length - VISIBLE_CHILDREN,
				expanded: isExpanded,
				depth: depth + 1
			});
		}
	};
	for (const root of roots) visit(root, rootDepth);
	return rows;
};

/** Rows for `parent`'s descendants, its children at depth 0, without `parent`. */
export const flattenSubtaskTree = (
	parent: TaskShort,
	subtasks: TaskShort[],
	expanded: ReadonlySet<string>
): TaskTreeRow[] => {
	// Unlinked so `parent` stays a root even if a cycle leads back to it.
	const root = { ...parent, parent_task_id: undefined };
	const node = buildTaskTree([root, ...subtasks]).find((node) => node.task === root)!;
	return flattenTaskTree([node], expanded, -1).slice(1);
};

/** Loaded tasks with live updates, plus live tasks below them or `anchorIds`. */
export const withLiveDescendants = (
	loaded: TaskShort[],
	live: Record<string, TaskShort>,
	anchorIds: string[] = []
): TaskShort[] => {
	const tasks = loaded.map((task) => live[task.id] ?? task);
	const anchors = new Set([...tasks.map((task) => task.id), ...anchorIds]);
	const isBelowAnchor = (task: TaskShort) => {
		const visited = new Set<string>();
		for (let id = task.parent_task_id; id && !visited.has(id); id = live[id]?.parent_task_id) {
			if (anchors.has(id)) return true;
			visited.add(id);
		}
		return false;
	};
	for (const task of Object.values(live)) {
		if (!anchors.has(task.id) && isBelowAnchor(task)) tasks.push(task);
	}
	return tasks;
};
