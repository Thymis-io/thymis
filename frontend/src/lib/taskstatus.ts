import { browser } from '$app/environment';
import { get, writable } from 'svelte/store';
import { invalidate } from '$app/navigation';
import { fetchWithNotify } from './fetchWithNotify';
import { page } from '$app/stores';
import { currentState, getConfigByIdentifier } from './state';
import { getConfigImageFormat } from './config/configUtils';

export type TaskState = 'pending' | 'running' | 'completed' | 'failed';

export type Task = {
	id: string;
	start_time: string;
	end_time?: string;
	state: TaskState;
	exception?: string;
	task_type: string;
	task_submission_data: Record<string, unknown> | null;
	task_submission_data_raw: Record<string, unknown> | null;

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

type ShortTaskMessage = {
	type: 'new_short_task' | 'short_task_update';
	task_id: string;
	task: TaskShort;
};

type SubscripedTaskMessage = {
	type: 'subscribed_task';
	task_id: string;
	task: Task;
};

type SubscripedTaskOutputMessage = {
	type: 'subscribed_task_output';
	task_id: string;
	stdout?: string;
	stderr?: string;
	nix_errors?: {
		msg: string;
		raw_msg: string;
		line?: number;
		column?: number;
		file?: string;
	}[];
	nix_error_logs?: string[];
	nix_warning_logs?: string[];
	nix_notice_logs?: string[];
	nix_info_logs?: string[];
};

let socket: WebSocket | undefined;

export const taskStatus = writable<Record<string, TaskShort>>({});
export const subscribedTask = writable<Task | null>(null);

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
		const data = JSON.parse(event.data) as
			| ShortTaskMessage
			| SubscripedTaskMessage
			| SubscripedTaskOutputMessage;
		if (data.type === 'new_short_task' || data.type === 'short_task_update') {
			taskStatus.update((ts) => {
				const taskPage = get(page).url.searchParams.get('task-page') ?? '1';
				if (data.task.id in ts || (data.type === 'new_short_task' && taskPage === '1')) {
					ts[data.task.id] = data.task;
				}
				return ts;
			});
		} else if (data.type === 'subscribed_task') {
			subscribedTask.set(data.task);
		} else if (data.type === 'subscribed_task_output') {
			subscribedTask.update((task) => {
				if (task && task.id === data.task_id) {
					if (task.process_stdout) {
						task.process_stdout += data.stdout;
					} else {
						task.process_stdout = data.stdout;
					}
					if (task.process_stderr) {
						task.process_stderr += data.stderr;
					} else {
						task.process_stderr = data.stderr;
					}
					if (task.nix_errors) {
						task.nix_errors.push(...(data.nix_errors ?? []));
					} else {
						task.nix_errors = data.nix_errors;
					}
					if (task.nix_error_logs) {
						task.nix_error_logs.push(...(data.nix_error_logs ?? []));
					} else {
						task.nix_error_logs = data.nix_error_logs;
					}
					if (task.nix_warning_logs) {
						task.nix_warning_logs.push(...(data.nix_warning_logs ?? []));
					} else {
						task.nix_warning_logs = data.nix_warning_logs;
					}
					if (task.nix_notice_logs) {
						task.nix_notice_logs.push(...(data.nix_notice_logs ?? []));
					} else {
						task.nix_notice_logs = data.nix_notice_logs;
					}
					if (task.nix_info_logs) {
						task.nix_info_logs.push(...(data.nix_info_logs ?? []));
					} else {
						task.nix_info_logs = data.nix_info_logs;
					}
				}
				return task;
			});
		}
	};
	socket.onclose = () => {
		console.log('task_status socket closed');
		setTimeout(startSocket, 1000);
	};
};

export const subscribeTask = (taskId: string) => {
	if (!socket || taskId === get(subscribedTask)?.id) return;
	subscribedTask.set(null);
	socket.send(JSON.stringify({ type: 'subscribe_task', task_id: taskId }));
};

let lastTaskStatus: TasksShort = {};
taskStatus.subscribe((tasks) => {
	// if a task.type is commandtask, and the task just finished, download the image
	// tasks have a uuid now at .id
	// tasks.forEach((task) => {
	Object.values(tasks).forEach(async (task) => {
		if (task.task_type !== 'build_device_image_task') return;
		if (task.state !== 'completed') return;
		if (!task.task_submission_data) return;
		if (!('configuration_id' in task.task_submission_data)) return;
		// check: this task was previously in the list, but not completed
		const otherTask = lastTaskStatus[task.id];
		if (!otherTask) return;
		if (otherTask.state === 'completed') return;
		// download the image
		// only if: config deviceModule image format is sd card
		const config_id = task.task_submission_data.configuration_id as string;
		const config = getConfigByIdentifier(currentState, config_id);
		const image_format = getConfigImageFormat(config);
		if (browser && image_format === 'sd-card-image') {
			const downloadUrl = `/api/download-image?identifier=${task.task_submission_data.configuration_id}`;
			const response = await fetchWithNotify(downloadUrl, { method: 'HEAD' });
			if (response.ok) {
				const a = document.createElement('a');
				a.href = downloadUrl;
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
