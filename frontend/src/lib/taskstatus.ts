import { browser } from '$app/environment';
import { get, writable } from 'svelte/store';
import { invalidate } from '$app/navigation';
import { fetchWithNotify } from './fetchWithNotify';
import { page } from '$app/stores';

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
	};

	nix_errors?: {
		msg: string;
		raw_msg: string;
		line?: number;
		column?: number;
		file?: string;
	}[];

	nix_files_linked?: number;
	nix_bytes_linked?: number;
	nix_corrupted_paths?: number;
	nix_untrusted_paths?: number;

	nix_error_logs?: string[];
	nix_warning_logs?: string[];
	nix_notice_logs?: string[];
	nix_info_logs?: string[];
};

export type TaskShort = {
	id: string;
	task_type: string;
	state: TaskState;
	start_time: string;
	end_time?: string;
	exception?: string;
	task_submission_data: Record<string, unknown>;

	nix_status?: {
		done: number;
		expected: number;
		running: number;
		failed: number;
	};
};

export type TasksShort = Record<string, TaskShort>;

type TaskStatus = {
	type: 'new_task' | 'task_update';
	task: TaskShort;
};

let socket: WebSocket | undefined;

export const taskStatus = writable<Record<string, TaskShort>>({});
export const tasksById: Record<string, Task> = {};

export const getAllTasks = async (
	limit: number,
	offset: number,
	fetch: typeof window.fetch = window.fetch
) => {
	const url = `/api/tasks?limit=${limit}&offset=${offset}`;
	const response = await fetchWithNotify(url, undefined, {}, fetch);
	const totalCount = response.headers.get('total-count');
	return {
		tasks: (await response.json()) as TaskShort[],
		totalCount: totalCount
	};
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

const startSocket = () => {
	console.log('starting task_status socket');
	// get schemed from current location
	const scheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
	socket = new WebSocket(`${scheme}://${window.location.host}/api/task_status`);
	socket.onmessage = async (event) => {
		const data = JSON.parse(event.data) as TaskStatus;
		taskStatus.update((ts) => {
			const taskPage = get(page).url.searchParams.get('task-page') ?? '1';
			if (data.task.id in ts || (data.type === 'new_task' && taskPage === '1')) {
				ts[data.task.id] = data.task;
			}
			return ts;
		});
		await invalidate((url) => url.pathname.startsWith(`/api/tasks/${data.task.id}`));
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
	Object.values(tasks).forEach(async (task) => {
		if (task.task_type !== 'build_device_image_task') return;
		if (task.state !== 'completed') return;
		if (!('device_identifier' in task.task_submission_data)) return;
		// check: this task was previously in the list, but not completed
		const otherTask = lastTaskStatus[task.id];
		if (!otherTask) return;
		if (otherTask.state === 'completed') return;
		// download the image
		if (browser) {
			const downloadUrl = `/api/download-image?identifier=${task.task_submission_data.device_identifier}`;
			const response = await fetchWithNotify(downloadUrl, { method: 'HEAD' });
			if (response.ok) {
				const a = document.createElement('a');
				a.href = downloadUrl;
				a.download = `thymis-image-${task.task_submission_data.device_identifier}.img`;
				document.body.appendChild(a);
				a.click();
				document.body.removeChild(a);
			}
		}
	});

	lastTaskStatus = structuredClone(tasks);
});

if (browser) {
	startSocket();
}
