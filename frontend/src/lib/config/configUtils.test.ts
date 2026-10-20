import { describe, it, expect } from 'vitest';
import { effectiveSettingPriority, inheritedSettingPriority } from './configUtils';
import { HOST_PRIORITY, type ModuleSettingsWithOrigin } from '$lib/state';

const definition = (
	overrides: Partial<ModuleSettingsWithOrigin> = {}
): ModuleSettingsWithOrigin => ({
	type: 'thymis_controller.modules.thymis.ThymisDevice',
	settings: {},
	originId: 'tag',
	originContext: 'tag',
	originName: 'Tag',
	priority: 90,
	...overrides
});

describe('effectiveSettingPriority', () => {
	it('falls back to the priority of the defining tag', () => {
		expect(effectiveSettingPriority(definition(), 'timezone')).toBe(90);
	});

	it('prefers the per-setting override', () => {
		expect(effectiveSettingPriority(definition({ priorities: { timezone: 70 } }), 'timezone')).toBe(
			70
		);
	});

	it('does not let an override of another setting leak', () => {
		expect(
			effectiveSettingPriority(definition({ priorities: { timezone: 70 } }), 'nameservers')
		).toBe(90);
	});

	it('honours an override of 0', () => {
		expect(effectiveSettingPriority(definition({ priorities: { timezone: 0 } }), 'timezone')).toBe(
			0
		);
	});

	it('uses the host priority for definitions without an origin priority', () => {
		expect(effectiveSettingPriority(definition({ priority: undefined }), 'timezone')).toBe(
			HOST_PRIORITY
		);
	});

	it('returns undefined for a missing definition', () => {
		expect(effectiveSettingPriority(undefined, 'timezone')).toBeUndefined();
	});
});

describe('inheritedSettingPriority', () => {
	it('ignores per-setting overrides', () => {
		expect(inheritedSettingPriority(definition({ priorities: { timezone: 70 } }))).toBe(90);
	});

	it('falls back to the host priority and handles missing definitions', () => {
		expect(inheritedSettingPriority(definition({ priority: undefined }))).toBe(HOST_PRIORITY);
		expect(inheritedSettingPriority(undefined)).toBeUndefined();
	});
});
