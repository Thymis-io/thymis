import { browser } from '$app/environment';
import { writable } from 'svelte/store';
import { controllerHost } from './api';

export type TaskState = 'pending' | 'running' | 'completed' | 'failed';
export type TaskVanilla = {
	type: 'task';
	display_name: string;
	state: TaskState;
	exception?: string;
	start_time: number;
	data: Record<string, any>;
};
export type CommandTask = Omit<TaskVanilla, 'type'> & {
	type: 'commandtask';
	stdout: string;
	stderr: string;
};
export type CompositeTask = Omit<TaskVanilla, 'type'> & {
	type: 'compositetask';
	tasks: TaskList;
};

export type Task = TaskVanilla | CommandTask | CompositeTask;

export type TaskList = Task[];

let socket: WebSocket | undefined;

export const taskStatus = writable<TaskList>([]);
export let taskStatusValue: TaskList = [];

const startSocket = () => {
	console.log('starting task_status socket');
	socket = new WebSocket(`ws://${controllerHost}/task_status`);
	socket.onmessage = (event) => {
		const data = JSON.parse(event.data) as TaskList;
		const lastTaskStatus = taskStatusValue;

		// if a task.type is commandtask, and the task just finished, download the image
		// for each task in the task list
		data.forEach((task) => {
			if (task.type !== 'commandtask') return;
			if (task.state !== 'completed') return;
			if (!('program' in task.data)) return;
			if (task.data.program !== 'nix') return;
			if (!('args' in task.data)) return;
			if (task.data.args[0] !== 'build') return;
			if (!('identifier' in task.data)) return;
			// check: this task was previously in the list, but not completed
			const otherTask = lastTaskStatus?.find(
				(t) =>
					t.type === 'commandtask' &&
					t.data.identifier === task.data.identifier &&
					t.start_time === task.start_time
			);
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

		taskStatus.set(data);
		taskStatusValue = data;
	};
	socket.onclose = () => {
		console.log('task_status socket closed');
		setTimeout(startSocket, 1000);
	};
};

if (browser) {
	startSocket();
}
