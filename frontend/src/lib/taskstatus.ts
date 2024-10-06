import { browser } from '$app/environment';
import { derived, writable, type Readable } from 'svelte/store';
import { invalidate } from '$app/navigation';

export type TaskState = 'pending' | 'running' | 'completed' | 'failed';
export type TaskVanilla = {
	id: string;
	type: 'task';
	display_name: string;
	state: TaskState;
	exception?: string;
	start_time: number;
	end_time?: number;
	data: Record<string, unknown>;
};
export type CommandTask = Omit<TaskVanilla, 'type'> & {
	type: 'commandtask';
	stdout: string;
	stderr: string;
};
export type NixCommandTask = Omit<CommandTask, 'type'> & {
	type: 'nixcommandtask';
	status: {
		done: number;
		expected: number;
		running: number;
		failed: number;
		errors: unknown[];
		logs_by_level: Record<number, string[]>;
	};
};

export type CompositeTask = Omit<TaskVanilla, 'type'> & {
	type: 'compositetask';
	tasks: TaskList;
};

export type Task = TaskVanilla | CommandTask | CompositeTask | NixCommandTask;

export type TaskList = Task[];

let socket: WebSocket | undefined;

export const taskStatus = writable<TaskList>([]);
export const tasksById: Record<string, Task> = {};
export const tasksByIdStore: Readable<Record<string, Task>> = derived<
	typeof taskStatus,
	Record<string, Task>
>(
	taskStatus,
	($taskStatus, set) => {
		const tasksById: Record<string, Task> = {};
		for (const task of $taskStatus) {
			tasksById[task.id] = task;
		}
		set(tasksById);
	},
	{}
);
taskStatus.subscribe((value) => {
	for (const task of value) {
		tasksById[task.id] = task;
	}
});

export const getAllTasks = async (fetch: typeof window.fetch = window.fetch) => {
	const response = await fetch(`/api/tasks`);
	return (await response.json()) as TaskList;
};

export const getTask = async (taskId: string, fetch: typeof window.fetch = window.fetch) => {
	const response = await fetch(`/api/tasks/${taskId}`);
	return (await response.json()) as Task;
};

export const cancelTask = async (taskId: string, fetch: typeof window.fetch = window.fetch) => {
	const response = await fetch(`/api/tasks/${taskId}/cancel`, {
		method: 'POST'
	});
	return response;
};

export const retryTask = async (taskId: string, fetch: typeof window.fetch = window.fetch) => {
	const response = await fetch(`/api/tasks/${taskId}/retry`, {
		method: 'POST'
	});
	return response;
};

export const runImmediately = async (taskId: string, fetch: typeof window.fetch = window.fetch) => {
	const response = await fetch(`/api/tasks/${taskId}/run_immediately`, {
		method: 'POST'
	});
	return response;
};

const startSocket = () => {
	console.log('starting task_status socket');
	// get schemed from current location
	const scheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
	socket = new WebSocket(`${scheme}://${window.location.host}/api/task_status`);
	socket.onmessage = async (event) => {
		const data = JSON.parse(event.data) as TaskList;
		console.log('task_status socket message', data);
		taskStatus.set(data);
		await invalidate((url) => url.pathname.startsWith('/tasks'));
	};
	socket.onclose = () => {
		console.log('task_status socket closed');
		setTimeout(startSocket, 1000);
	};
};

let lastTaskStatus: TaskList = [];
taskStatus.subscribe((tasks) => {
	// if a task.type is commandtask, and the task just finished, download the image
	// tasks have a uuid now at .id
	tasks.forEach((task) => {
		if (task.type !== 'nixcommandtask') return;
		if (task.state !== 'completed') return;
		console.log('nixcommandtask completed1', task);
		if (!('program' in task.data)) return;
		if (task.data.program !== 'nix') return;
		if (!('args' in task.data)) return;
		console.log('nixcommandtask completed2', task);
		if (!(task.data.args instanceof Array)) return;
		// if (task.data.args[0] !== 'build') return;
		if (task.data.args.indexOf('build') === -1) return;
		if (!('identifier' in task.data)) return;
		console.log('nixcommandtask completed3', task);
		// check: this task was previously in the list, but not completed
		const otherTask = lastTaskStatus.find((t) => t.id === task.id);
		console.log('nixcommandtask completed4', task, otherTask);
		if (!otherTask) return;
		console.log('nixcommandtask completed5', task, otherTask);
		if (otherTask.state === 'completed') return;
		console.log('nixcommandtask completed6', task, otherTask);
		// download the image
		const a = document.createElement('a');
		a.href = `/api/download-image?identifier=${task.data.identifier}`;
		a.download = `thymis-image-${task.data.identifier}.img`;
		document.body.appendChild(a);
		a.click();
		document.body.removeChild(a);
	});

	lastTaskStatus = tasks;
});

if (browser) {
	startSocket();
}
