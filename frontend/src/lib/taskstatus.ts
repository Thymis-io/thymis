import { browser } from '$app/environment';
import { writable } from 'svelte/store';
import { controllerHost } from './api';

type TaskState = 'pending' | 'running' | 'completed' | 'failed';
type Task = {
	type: 'task';
	display_name: string;
	state: TaskState;
	exception?: string;
};
type CommandTask = Omit<Task, 'type'> & {
	type: 'commandtask';
	stdout: string;
	stderr: string;
};
type CompositeTask = Omit<Task, 'type'> & {
	type: 'compositetask';
	tasks: TaskList;
};

type TaskList = (Task | CommandTask | CompositeTask)[];

let socket: WebSocket | undefined;

export let taskStatus = writable<TaskList | undefined>();

const startSocket = () => {
	console.log('starting task_status socket');
	socket = new WebSocket(`ws://${controllerHost}/task_status`);
	socket.onmessage = (event) => {
		taskStatus.set(JSON.parse(event.data));
		console.log('task_status', JSON.parse(event.data));
	};
	socket.onclose = () => {
		console.log('task_status socket closed');
		setTimeout(startSocket, 1000);
	};
};

if (browser) {
	startSocket();
}
