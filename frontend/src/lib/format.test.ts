import { describe, it, expect } from 'vitest';
import { formatBytes } from './format';
import { formatRamSize } from './config/configUtils';

describe('formatBytes', () => {
	it('renders whole bytes without decimals', () => {
		expect(formatBytes(0)).toBe('0 B');
		expect(formatBytes(1)).toBe('1 B');
		expect(formatBytes(1023)).toBe('1023 B');
	});

	it('scales by 1024 and labels IEC units by default', () => {
		expect(formatBytes(1024)).toBe('1.00 KiB');
		expect(formatBytes(1536)).toBe('1.50 KiB');
		expect(formatBytes(1024 * 1024)).toBe('1.00 MiB');
		expect(formatBytes(3 * 1024 ** 3)).toBe('3.00 GiB');
	});

	it('drops decimals as the value grows', () => {
		expect(formatBytes(9.5 * 1024)).toBe('9.50 KiB');
		expect(formatBytes(42.5 * 1024)).toBe('42.5 KiB');
		expect(formatBytes(512.5 * 1024)).toBe('513 KiB');
	});

	it('stays at the largest unit instead of overflowing it', () => {
		expect(formatBytes(2048 * 1024 ** 5)).toBe('2048 PiB');
	});

	it('scales by 1000 and labels SI units on request', () => {
		expect(formatBytes(999, { system: 'si' })).toBe('999 B');
		expect(formatBytes(1000, { system: 'si' })).toBe('1.00 KB');
		expect(formatBytes(1024, { system: 'si' })).toBe('1.02 KB');
		expect(formatBytes(1500, { system: 'si', decimals: 2 })).toBe('1.50 KB');
	});

	it('honours fixed decimals and spacing options', () => {
		expect(formatBytes(1536, { decimals: 0 })).toBe('2 KiB');
		expect(formatBytes(1536, { space: false })).toBe('1.50KiB');
		expect(formatBytes(1e9, { system: 'si', decimals: 0, space: false })).toBe('1GB');
	});
});

describe('formatRamSize', () => {
	it('is empty for absent or zero amounts', () => {
		expect(formatRamSize(null)).toBeNull();
		expect(formatRamSize(undefined)).toBeNull();
		expect(formatRamSize(0)).toBeNull();
	});

	it('renders rounded SI amounts without a space', () => {
		expect(formatRamSize(512 * 1000 ** 2)).toBe('512MB');
		expect(formatRamSize(4 * 1000 ** 3)).toBe('4GB');
		expect(formatRamSize(8.4 * 1000 ** 3)).toBe('8GB');
	});

	it('falls back to smaller SI units below a gigabyte', () => {
		expect(formatRamSize(300 * 1000 ** 2)).toBe('300MB');
		expect(formatRamSize(512 * 1000)).toBe('512KB');
	});
});
