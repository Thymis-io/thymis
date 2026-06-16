import { describe, it, expect } from 'vitest';
import { RANGE_OPTIONS, rangeToParams } from './fleet';

describe('rangeToParams', () => {
	it('maps named ranges to hours + granularity', () => {
		expect(rangeToParams('24h')).toEqual({ hours: 24, granularity: '15min', buckets: 48 });
		expect(rangeToParams('7d')).toEqual({ hours: 168, granularity: '1h', buckets: 48 });
		expect(rangeToParams('30d')).toEqual({ hours: 720, granularity: '6h', buckets: 60 });
		expect(rangeToParams('90d')).toEqual({ hours: 2160, granularity: '1d', buckets: 90 });
	});

	it('exposes the selectable ranges', () => {
		expect(RANGE_OPTIONS).toContain('24h');
		expect(RANGE_OPTIONS).toContain('90d');
	});
});
