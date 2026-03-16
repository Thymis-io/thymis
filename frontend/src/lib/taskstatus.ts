import { browser } from '$app/environment';
import { get, writable } from 'svelte/store';
import { fetchWithNotify } from './fetchWithNotify';

export type TaskState = 'pending' | 'running' | 'completed' | 'failed';

export type TaskProcess = {
	task_id: string;
	process_index: number;

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

export type Task = {
	id: string;
	start_time: string;
	end_time?: string;
	state: TaskState;
	exception?: string;
	task_type: string;
	task_submission_data: Record<string, unknown> | null;
	task_submission_data_raw: Record<string, unknown> | null;
	processes: TaskProcess[];

	parent_task_id?: string;
	children?: string[];
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

let resolvePromise: () => void;
let socketPromise = new Promise<void>((resolve) => {
	resolvePromise = resolve;
});

const isSameProcess = (a: TaskProcess, b: TaskProcess) => {
	return a.task_id === b.task_id && a.process_index === b.process_index;
};

const mergeProcesses = (existingProcesses: TaskProcess[], incomingProcesses: TaskProcess[]) => {
	const results: TaskProcess[] = incomingProcesses.map((incoming) => {
		const existing = existingProcesses.find((p) => isSameProcess(p, incoming));
		return {
			...existing,
			...incoming,
			process_stdout: (existing?.process_stdout ?? '') + (incoming.process_stdout ?? ''),
			process_stderr: (existing?.process_stderr ?? '') + (incoming.process_stderr ?? ''),
			nix_errors: (existing?.nix_errors ?? []).concat(incoming.nix_errors ?? []),
			nix_error_logs: (existing?.nix_error_logs ?? []).concat(incoming.nix_error_logs ?? []),
			nix_warning_logs: (existing?.nix_warning_logs ?? []).concat(incoming.nix_warning_logs ?? []),
			nix_notice_logs: (existing?.nix_notice_logs ?? []).concat(incoming.nix_notice_logs ?? []),
			nix_info_logs: (existing?.nix_info_logs ?? []).concat(incoming.nix_info_logs ?? [])
		};
	});

	for (const existing of existingProcesses) {
		if (!incomingProcesses.some((incoming) => isSameProcess(incoming, existing))) {
			results.push(existing);
		}
	}

	return results;
};

const startSocket = () => {
	console.log('starting task_status socket');
	// get schemed from current location
	const scheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
	socket = new WebSocket(`${scheme}://${window.location.host}/api/task_status`);
	socket.onopen = () => {
		console.log('task_status socket opened');
		resolvePromise();
	};
	socket.onmessage = async (event) => {
		const data = JSON.parse(event.data) as
			| ShortTaskMessage
			| SubscripedTaskMessage
			| SubscripedTaskOutputMessage;
		if (data.type === 'new_short_task' || data.type === 'short_task_update') {
			taskStatus.update((ts) => {
				const taskPage = new URL(window.location.href).searchParams.get('task-page') ?? '1';
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
						processes: mergeProcesses(task.processes ?? [], data.task.processes ?? [])
					};
				}
				return task;
			});
		}
	};
	socket.onclose = () => {
		console.log('task_status socket closed');
		socketPromise = new Promise<void>((resolve) => {
			resolvePromise = resolve;
		});
		setTimeout(startSocket, 1000);
	};
};

export const subscribeTask = async (taskId: string) => {
	await socketPromise;
	if (!socket || taskId === get(subscribedTask)?.id) return;
	subscribedTask.set(null);
	socket.send(JSON.stringify({ type: 'subscribe_task', task_id: taskId }));
};

if (browser) {
	startSocket();
}
