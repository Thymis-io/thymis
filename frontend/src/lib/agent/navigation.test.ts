import { describe, expect, it } from 'vitest';
import { frontendActionPath } from './navigation';

describe('frontendActionPath', () => {
	it.each([
		['overview', '/overview'],
		['configuration_list', '/configuration/list'],
		['devices', '/devices'],
		['devices_active', '/devices/active'],
		['devices_archived', '/devices/archived'],
		['devices_without_deployment', '/devices/without-deployment'],
		['tasks', '/tasks'],
		['history', '/history'],
		['external_repositories', '/external-repositories'],
		['tags', '/tags'],
		['vnc', '/vnc'],
		['secrets', '/secrets'],
		['artifacts', '/artifacts'],
		['auto_update', '/auto-update']
	])('maps %s to %s', (destination, expectedPath) => {
		expect(frontendActionPath({ destination })).toBe(expectedPath);
	});

	it.each([
		['configuration_edit', '/configuration/edit'],
		['configuration_details', '/configuration/configuration-details'],
		['configuration_logs', '/configuration/logs'],
		['configuration_terminal', '/configuration/terminal'],
		['configuration_vnc', '/configuration/vnc']
	])('maps %s to a selected configuration page', (destination, expectedPath) => {
		expect(frontendActionPath({ destination, identifier: 'camera' })).toBe(
			`${expectedPath}?global-nav-target-type=config&global-nav-target=camera&config-selected-module-context-type=config&config-selected-module-context-identifier=camera`
		);
	});

	it.each([
		['device_details', '/devices/device%20one/details'],
		['device_logs', '/devices/device%20one/logs'],
		['device_terminal', '/devices/device%20one/terminal'],
		['device_vnc', '/devices/device%20one/vnc'],
		['deployment_logs', '/deployment_info/device%20one/logs'],
		['task', '/tasks/device%20one']
	])('maps %s to its entity page', (destination, expectedPath) => {
		expect(frontendActionPath({ destination, identifier: 'device one' })).toBe(expectedPath);
	});

	it('rejects unknown destinations and missing entity identifiers', () => {
		expect(frontendActionPath({ destination: 'not-a-route' })).toBeUndefined();
		expect(frontendActionPath({ destination: 'device_details' })).toBeUndefined();
		expect(frontendActionPath(null)).toBeUndefined();
	});
});
