import { browser } from '$app/environment';
import { derived, writable, type Readable } from 'svelte/store';
import { invalidate } from '$app/navigation';
import { fetchWithNotify } from './fetchWithNotify';

export type TaskState = 'pending' | 'running' | 'completed' | 'failed';

export type Task = {
	id: string;
	start_time: string;
	end_time?: string;
	state: TaskState;
	exception?: string;
	task_type: string;
	task_submission_data: Record<string, unknown>;

	parent_task_id?: string;
	children?: string[];

	process_program?: string;
	process_args?: string[];
	process_env?: Record<string, string>;
	process_stdout?: string;
	process_stderr?: string;

	nix_status?: {
		done: number;
		expected: number;
		running: number;
		failed: number;
		errors: unknown[];
		logs_by_level: Record<number, string[]>;
	};
	nix_files_linked?: number;
	nix_bytes_linked?: number;
	nix_corrupted_paths?: number;
	nix_untrusted_paths?: number;
	nix_errors?: Record<string, unknown>;
	nix_warnings?: Record<string, unknown>;
	nix_notices?: Record<string, unknown>;
	nix_infos?: Record<string, unknown>;
};

export type TaskShort = {
	id: string;
	task_type: string;
	state: TaskState;
	start_time: string;
	end_time?: string;
	exception?: string;
	data: Record<string, unknown>;
};

export type TasksShort = Record<string, TaskShort>;

let socket: WebSocket | undefined;

export const taskStatus = writable<Record<string, TaskShort>>({});
export const tasksById: Record<string, Task> = {};

export const getAllTasks = async (fetch: typeof window.fetch = window.fetch) => {
	const response = await fetchWithNotify(`/api/tasks`, undefined, {}, fetch);
	return (await response.json()) as TaskShort[];
};

export const getTask = async (taskId: string, fetch: typeof window.fetch = window.fetch) => {
	const response = await fetchWithNotify(`/api/tasks/${taskId}`, undefined, {}, fetch);
	return (await response.json()) as Task;
};

export const cancelTask = async (taskId: string, fetch: typeof window.fetch = window.fetch) => {
	const response = await fetchWithNotify(
		`/api/tasks/${taskId}/cancel`,
		{ method: 'POST' },
		{},
		fetch
	);
	return response;
};

export const retryTask = async (taskId: string, fetch: typeof window.fetch = window.fetch) => {
	const response = await fetchWithNotify(
		`/api/tasks/${taskId}/retry`,
		{
			method: 'POST'
		},
		{},
		fetch
	);
	return response;
};

export const runImmediately = async (taskId: string, fetch: typeof window.fetch = window.fetch) => {
	const response = await fetchWithNotify(
		`/api/tasks/${taskId}/run_immediately`,
		{
			method: 'POST'
		},
		{},
		fetch
	);
	return response;
};

const startSocket = () => {
	console.log('starting task_status socket');
	// get schemed from current location
	const scheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
	socket = new WebSocket(`${scheme}://${window.location.host}/api/task_status`);
	socket.onmessage = async (event) => {
		console.log('task_status message', event.data);
		const data = JSON.parse(event.data) as TaskShort;
		taskStatus.update((ts) => {
			ts[data.id] = data;
			console.log('task_status update', ts);
			return ts;
		});
		await invalidate((url) => url.pathname.startsWith(`/api/tasks/${data.id}`));
	};
	socket.onclose = () => {
		console.log('task_status socket closed');
		setTimeout(startSocket, 1000);
	};
};

let lastTaskStatus: TasksShort = {};
taskStatus.subscribe((tasks) => {
	// if a task.type is commandtask, and the task just finished, download the image
	// tasks have a uuid now at .id
	// tasks.forEach((task) => {
	Object.values(tasks).forEach((task) => {
		if (task.task_type !== 'nixcommandtask') return;
		if (task.state !== 'completed') return;
		if (!('program' in task.data)) return;
		if (task.data.program !== 'nix') return;
		if (!('args' in task.data)) return;
		if (!(task.data.args instanceof Array)) return;
		// if (task.data.args[0] !== 'build') return;
		if (task.data.args.indexOf('build') === -1) return;
		if (!('identifier' in task.data)) return;
		// check: this task was previously in the list, but not completed
		const otherTask = lastTaskStatus[task.id];
		if (!otherTask) return;
		if (otherTask.state === 'completed') return;
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
