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
	task: Task;
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
			subscribedTask.update((task) => {
				if (task && task.id === data.task_id) {
					return { ...task, ...data.task };
				}
				return task;
			});
		} else if (data.type === 'subscribed_task') {
			subscribedTask.set(data.task);
		} else if (data.type === 'subscribed_task_output') {
			subscribedTask.update((task) => {
				if (task && task.id === data.task_id) {
					return {
						...data.task,
						process_stdout: task.process_stdout
							? task.process_stdout + data.task.process_stdout
							: data.task.process_stdout,
						process_stderr: task.process_stderr
							? task.process_stderr + data.task.process_stderr
							: data.task.process_stderr,
						nix_errors: task.nix_errors
							? task.nix_errors.concat(data.task.nix_errors ?? [])
							: data.task.nix_errors,
						nix_error_logs: task.nix_error_logs
							? task.nix_error_logs.concat(data.task.nix_error_logs ?? [])
							: data.task.nix_error_logs,
						nix_warning_logs: task.nix_warning_logs
							? task.nix_warning_logs.concat(data.task.nix_warning_logs ?? [])
							: data.task.nix_warning_logs,
						nix_notice_logs: task.nix_notice_logs
							? task.nix_notice_logs.concat(data.task.nix_notice_logs ?? [])
							: data.task.nix_notice_logs,
						nix_info_logs: task.nix_info_logs
							? task.nix_info_logs.concat(data.task.nix_info_logs ?? [])
							: data.task.nix_info_logs
					};
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

if (browser) {
	startSocket();
}
