const staticDashboardPaths: Record<string, string> = {
	overview: '/overview',
	configuration_list: '/configuration/list',
	devices: '/devices',
	devices_active: '/devices/active',
	devices_archived: '/devices/archived',
	devices_without_deployment: '/devices/without-deployment',
	tasks: '/tasks',
	history: '/history',
	external_repositories: '/external-repositories',
	tags: '/tags',
	vnc: '/vnc',
	secrets: '/secrets',
	artifacts: '/artifacts',
	auto_update: '/auto-update'
};

const configurationDestinationPaths: Record<string, string> = {
	configuration_edit: '/configuration/edit',
	configuration_details: '/configuration/configuration-details',
	configuration_logs: '/configuration/logs',
	configuration_terminal: '/configuration/terminal',
	configuration_vnc: '/configuration/vnc'
};

const deviceDestinationPaths: Record<string, string> = {
	device_details: 'details',
	device_logs: 'logs',
	device_terminal: 'terminal',
	device_vnc: 'vnc'
};

export const frontendActionPath = (input: unknown): string | undefined => {
	if (typeof input !== 'object' || input === null) return undefined;
	const { destination, identifier } = input as Record<string, unknown>;
	if (typeof destination !== 'string') return undefined;
	if (configurationDestinationPaths[destination] && typeof identifier === 'string') {
		const params = new URLSearchParams({
			'global-nav-target-type': 'config',
			'global-nav-target': identifier,
			'config-selected-module-context-type': 'config',
			'config-selected-module-context-identifier': identifier
		});
		return `${configurationDestinationPaths[destination]}?${params}`;
	}
	if (deviceDestinationPaths[destination] && typeof identifier === 'string') {
		return `/devices/${encodeURIComponent(identifier)}/${deviceDestinationPaths[destination]}`;
	}
	if (destination === 'deployment_logs' && typeof identifier === 'string') {
		return `/deployment_info/${encodeURIComponent(identifier)}/logs`;
	}
	if (destination === 'task' && typeof identifier === 'string') {
		return `/tasks/${encodeURIComponent(identifier)}`;
	}
	return staticDashboardPaths[destination];
};
