/**
 * Unit systems used to render byte counts.
 *
 * `iec` scales by 1024 and labels the units KiB/MiB/…, which matches how nix
 * and most system tooling report sizes. `si` scales by 1000 and labels them
 * KB/MB/…, which is how storage vendors and user-supplied file sizes are
 * usually quoted.
 */
const UNIT_SYSTEMS = {
	iec: { base: 1024, units: ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB'] },
	si: { base: 1000, units: ['B', 'KB', 'MB', 'GB', 'TB', 'PB'] }
} as const;

export type ByteUnitSystem = keyof typeof UNIT_SYSTEMS;

export interface FormatBytesOptions {
	/** Unit system to scale and label with. Defaults to `iec`. */
	system?: ByteUnitSystem;
	/**
	 * Fixed number of decimals for scaled units. When omitted, the precision
	 * shrinks as the value grows so that roughly three significant digits are
	 * shown (0 decimals at >= 100, 1 at >= 10, 2 below that).
	 */
	decimals?: number;
	/** Separate value and unit with a space. Defaults to `true`. */
	space?: boolean;
}

/**
 * Render a byte count with a matching unit, e.g. `formatBytes(1536)` is
 * `"1.50 KiB"`.
 */
export const formatBytes = (bytes: number, options: FormatBytesOptions = {}): string => {
	const { system = 'iec', decimals, space = true } = options;
	const { base, units } = UNIT_SYSTEMS[system];

	let value = bytes;
	let unit = 0;
	while (value >= base && unit < units.length - 1) {
		value /= base;
		unit += 1;
	}

	// Bytes are whole numbers, so the unscaled unit never gets decimals.
	const precision = unit === 0 ? 0 : (decimals ?? (value >= 100 ? 0 : value >= 10 ? 1 : 2));
	return `${value.toFixed(precision)}${space ? ' ' : ''}${units[unit]}`;
};
