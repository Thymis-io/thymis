<script lang="ts">
	import { t } from 'svelte-i18n';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { invalidate } from '$app/navigation';
	import { Button, Input, Label, Alert, Spinner, Toggle, Select } from 'flowbite-svelte';
	import Search from 'lucide-svelte/icons/search';
	import RefreshCcw from 'lucide-svelte/icons/refresh-ccw';
	import Download from 'lucide-svelte/icons/download';
	import Calendar from 'lucide-svelte/icons/calendar';
	import Clock from 'lucide-svelte/icons/clock';
	import MonospaceText from '$lib/components/MonospaceText.svelte';
	import Paginator from '$lib/components/Paginator.svelte';
	import PageHead from '$lib/components/layout/PageHead.svelte';
	import RenderTimeAgo from '$lib/components/RenderTimeAgo.svelte';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	// Helper functions for datetime format conversion
	const toLocalDateTimeString = (isoString: string): string => {
		// Convert ISO string to datetime-local format (YYYY-MM-DDTHH:MM)
		return isoString.slice(0, 16);
	};

	const toISOString = (localDateTime: string): string => {
		// Convert datetime-local format to full ISO string
		return new Date(localDateTime).toISOString();
	};

	// URL parameters and state
	let deploymentId = $derived($page.params.id);

	// URL-derived values for reading current state
	let urlFromDateTime = $derived.by(() => {
		const param = $page.url.searchParams.get('fromDateTime');
		if (param) {
			// If parameter exists, convert to local datetime format for form inputs
			return toLocalDateTimeString(
				param.includes('T') && param.includes(':') ? param : new Date(param).toISOString()
			);
		}
		return toLocalDateTimeString(new Date(new Date().getTime() - 60 * 60 * 1000).toISOString());
	});
	let urlToDateTime = $derived.by(() => {
		const param = $page.url.searchParams.get('toDateTime');
		if (param) {
			// If parameter exists, convert to local datetime format for form inputs
			return toLocalDateTimeString(
				param.includes('T') && param.includes(':') ? param : new Date(param).toISOString()
			);
		}
		return toLocalDateTimeString(new Date().toISOString());
	});
	let urlLimit = $derived(parseInt($page.url.searchParams.get('limit') || '100'));
	let urlOffset = $derived(parseInt($page.url.searchParams.get('offset') || '0'));
	let urlSearchQuery = $derived($page.url.searchParams.get('search') || '');
	// Form input state - initialized with defaults, synced with URL via effect
	let fromDateTime = $state('');
	let toDateTime = $state('');
	let limit = $state('100'); // Changed to string to match Select component
	let searchQuery = $state('');

	// UI state that doesn't come from URL
	let autoRefresh = $state(false);
	let refreshInterval = $state(5); // seconds
	let reverseOrder = $state(false); // Toggle for reversing log order

	// Loading state
	let isLoading = $state(false);
	let refreshTimer: NodeJS.Timeout | null = null;

	// Log display options
	let showTimestamps = $state(true);
	let wrapLines = $state(false);

	// Only sync form values with URL on initial load and when URL changes from external navigation
	// Track if we're currently applying filters to avoid syncing during user input
	let isApplyingFilters = $state(false);

	$effect(() => {
		if (!isApplyingFilters) {
			fromDateTime = urlFromDateTime;
			toDateTime = urlToDateTime;
			limit = urlLimit.toString(); // Convert to string for Select component
			searchQuery = urlSearchQuery;
		}
	});

	// Pagination settings
	const limitOptions = [
		{ value: '50', name: '50' },
		{ value: '100', name: '100' },
		{ value: '200', name: '200' },
		{ value: '500', name: '500' },
		{ value: '1000', name: '1000' }
	];

	// Quick time range presets
	const timePresets = [
		{ label: 'Last 15 minutes', minutes: 15 },
		{ label: 'Last hour', minutes: 60 },
		{ label: 'Last 4 hours', minutes: 240 },
		{ label: 'Last 24 hours', minutes: 1440 },
		{ label: 'Last 7 days', minutes: 10080 }
	];

	// Apply filters and navigate
	const applyFilters = () => {
		isLoading = true;
		isApplyingFilters = true;
		const url = new URL($page.url);

		// Check if parameters have changed
		const currentFromDateTime = urlFromDateTime;
		const currentToDateTime = urlToDateTime;
		const currentLimit = urlLimit.toString();
		const currentOffset = urlOffset.toString();
		const currentSearch = urlSearchQuery;

		const hasParamChanges =
			currentFromDateTime !== fromDateTime ||
			currentToDateTime !== toDateTime ||
			currentLimit !== limit ||
			currentOffset !== '0' || // Always reset offset when applying filters
			currentSearch !== searchQuery;

		if (hasParamChanges) {
			// Parameters changed, use goto to update URL
			url.searchParams.set('fromDateTime', toISOString(fromDateTime));
			url.searchParams.set('toDateTime', toISOString(toDateTime));
			url.searchParams.set('limit', limit);
			url.searchParams.set('offset', '0'); // Reset offset when applying filters
			if (searchQuery) url.searchParams.set('search', searchQuery);
			else url.searchParams.delete('search');

			goto(url.toString(), { replaceState: false, noScroll: true }).then(() => {
				isApplyingFilters = false;
			});
		} else {
			// No parameter changes, just refresh data
			invalidate((url) => url.pathname.startsWith('/api/logs/')).then(() => {
				isLoading = false;
				isApplyingFilters = false;
			});
		}
	};

	// Quick time range selection
	const setTimePreset = (minutes: number) => {
		isApplyingFilters = true;
		const now = new Date();
		const from = new Date(now.getTime() - minutes * 60 * 1000);
		const url = new URL($page.url);
		url.searchParams.set('toDateTime', now.toISOString());
		url.searchParams.set('fromDateTime', from.toISOString());
		goto(url.toString(), { replaceState: false, noScroll: true }).then(() => {
			isApplyingFilters = false;
		});
	};

	// Pagination handlers
	const handlePageChange = (newPage: number) => {
		isApplyingFilters = true;
		const url = new URL($page.url);
		url.searchParams.set('offset', ((newPage - 1) * urlLimit).toString());
		goto(url.toString(), { replaceState: false, noScroll: true }).then(() => {
			isApplyingFilters = false;
		});
	};

	const handleLimitChange = () => {
		// Don't proceed if we're already applying filters to avoid race conditions
		if (isApplyingFilters) return;

		isApplyingFilters = true;
		const url = new URL($page.url);
		url.searchParams.set('limit', limit);
		url.searchParams.set('offset', '0'); // Reset to first page when changing limit
		goto(url.toString(), { replaceState: false, noScroll: true }).then(() => {
			isApplyingFilters = false;
		});
	};

	// Auto-refresh functionality
	const toggleAutoRefresh = () => {
		if (autoRefresh) {
			refreshTimer = setInterval(() => {
				// Update toDateTime to current time for live logs
				isApplyingFilters = true;
				const url = new URL($page.url);
				url.searchParams.set('toDateTime', new Date().toISOString());
				goto(url.toString(), { replaceState: true, noScroll: true }).then(() => {
					isApplyingFilters = false;
				});
			}, refreshInterval * 1000);
		} else {
			if (refreshTimer) {
				clearInterval(refreshTimer);
				refreshTimer = null;
			}
		}
	};

	// Download logs functionality
	const downloadLogs = () => {
		// Create download link for current log data
		if (data.logs && data.logs.length > 0) {
			// Always use chronological order for downloads (oldest first)
			// Since data.logs arrives newest first, reverse it for chronological order
			const logText = [...data.logs]
				.reverse()
				.map((log: any) => {
					const timestamp = new Date(log.timestamp).toISOString();
					return `[${timestamp}] ${log.level || 'INFO'}: ${log.message || JSON.stringify(log)}`;
				})
				.join('\n');

			const blob = new Blob([logText], { type: 'text/plain' });
			const url = URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = url;
			a.download = `logs_${deploymentId}_${new Date().toISOString().slice(0, 10)}.txt`;
			document.body.appendChild(a);
			a.click();
			document.body.removeChild(a);
			URL.revokeObjectURL(url);
		}
	};

	// Watch auto-refresh toggle
	$effect(() => {
		toggleAutoRefresh();
		return () => {
			if (refreshTimer) {
				clearInterval(refreshTimer);
			}
		};
	});

	// Update loading state when data changes
	$effect(() => {
		if (data) {
			isLoading = false;
			isApplyingFilters = false;
		}
	});

	// Handle limit changes reactively
	$effect(() => {
		// Only trigger limit change if the limit differs from URL and we're not currently applying filters
		if (!isApplyingFilters && limit !== urlLimit.toString()) {
			handleLimitChange();
		}
	});

	// Process logs for display (server already handles filtering)
	const processedLogs = $derived(reverseOrder ? [...(data.logs || [])].reverse() : data.logs || []);

	// Format logs for display
	const formatLogsForDisplay = (logs: any[]) => {
		return logs
			.map((log: any) => {
				let line = '';

				if (showTimestamps && log.timestamp) {
					const timestamp = new Date(log.timestamp).toISOString();
					line += `[${timestamp}] `;
				}

				if (log.level) {
					line += `${log.level.toUpperCase()}: `;
				}

				line += log.message || JSON.stringify(log, null, 2);

				return line;
			})
			.join('\n');
	};

	// Current page calculation
	const currentPage = $derived(Math.floor(urlOffset / urlLimit) + 1);
	// Note: We don't have total count from server, so pagination is based on current results
	// This means we can only show pagination controls when we have a full page of results
	const hasMorePages = $derived(data.logs && data.logs.length === urlLimit);
	const showPagination = $derived(urlOffset > 0 || hasMorePages);
</script>

<PageHead
	nav={data.nav}
	globalState={data.globalState}
	repoStatus={data.repoStatus}
	title="Deployment Logs"
/>

<div class="flex flex-col gap-4 px-0 py-4 w-full">
	<!-- Header with actions -->
	<div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 px-4">
		<div>
			<p class="text-sm text-gray-600 dark:text-gray-400">
				Viewing logs for deployment: {deploymentId}
			</p>
		</div>

		<div class="flex flex-wrap gap-2">
			<Button size="sm" color="blue" on:click={applyFilters} disabled={isLoading}>
				{#if isLoading}
					<Spinner class="mr-2" size="4" />
				{:else}
					<RefreshCcw class="mr-2 h-4 w-4" />
				{/if}
				Refresh
			</Button>

			<Button
				size="sm"
				color="green"
				on:click={downloadLogs}
				disabled={!data.logs || data.logs.length === 0}
			>
				<Download class="mr-2 h-4 w-4" />
				Download
			</Button>
		</div>
	</div>

	<!-- Filters and Controls -->
	<div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
			<!-- Time Range -->
			<div class="space-y-2">
				<Label class="text-sm font-medium">Time Range</Label>
				<div class="flex flex-col gap-2">
					<div class="flex items-center gap-2">
						<Calendar class="h-4 w-4 text-gray-500" />
						<Input
							type="datetime-local"
							bind:value={fromDateTime}
							class="text-sm"
							placeholder="From"
						/>
					</div>
					<div class="flex items-center gap-2">
						<Clock class="h-4 w-4 text-gray-500" />
						<Input type="datetime-local" bind:value={toDateTime} class="text-sm" placeholder="To" />
					</div>
				</div>
			</div>

			<!-- Quick Time Presets -->
			<div class="space-y-2">
				<Label class="text-sm font-medium">Quick Select</Label>
				<div class="grid grid-cols-1 gap-1">
					{#each timePresets as preset}
						<Button size="xs" color="light" on:click={() => setTimePreset(preset.minutes)}>
							{preset.label}
						</Button>
					{/each}
				</div>
			</div>

			<!-- Search -->
			<div class="space-y-2">
				<Label class="text-sm font-medium">Search</Label>
				<div class="relative">
					<Search
						class="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-500"
					/>
					<Input bind:value={searchQuery} placeholder="Search logs..." class="pl-10 text-sm" />
				</div>
			</div>
		</div>

		<!-- Display Options and Auto-refresh -->
		<div
			class="flex flex-wrap items-center justify-between gap-4 mt-4 pt-4 border-t border-gray-200 dark:border-gray-600"
		>
			<div class="flex flex-wrap items-center gap-4">
				<div class="flex items-center gap-2">
					<Toggle bind:checked={showTimestamps} size="small" />
					<Label class="text-sm">Show timestamps</Label>
				</div>
				<div class="flex items-center gap-2">
					<Toggle bind:checked={wrapLines} size="small" />
					<Label class="text-sm">Wrap lines</Label>
				</div>
				<div class="flex items-center gap-2">
					<Toggle bind:checked={reverseOrder} size="small" />
					<Label class="text-sm">Reverse order</Label>
				</div>
				<div class="flex items-center gap-2">
					<Toggle bind:checked={autoRefresh} size="small" />
					<Label class="text-sm">Auto-refresh ({refreshInterval}s)</Label>
				</div>
			</div>

			<div class="flex items-center gap-2">
				<Label class="text-sm">Per page:</Label>
				<Select bind:value={limit} items={limitOptions} size="sm" class="w-20" />
			</div>
		</div>

		<!-- Apply Filters Button -->
		<div class="flex justify-center mt-4">
			<Button color="primary" on:click={applyFilters} disabled={isLoading}>
				{#if isLoading}
					<Spinner class="mr-2" size="4" />
				{/if}
				Apply Filters
			</Button>
		</div>
	</div>

	<!-- Log Content -->
	<div
		class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 flex-1 min-h-0"
	>
		{#if isLoading}
			<div class="flex items-center justify-center p-8">
				<Spinner size="8" />
				<span class="ml-3 text-gray-600 dark:text-gray-400">Loading logs...</span>
			</div>
		{:else if !data.logs || data.logs.length === 0}
			<div class="flex flex-col items-center justify-center p-8 text-center">
				<div class="text-gray-400 dark:text-gray-500 mb-4">
					<Search class="h-12 w-12 mx-auto" />
				</div>
				<h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">No logs found</h3>
				<p class="text-gray-600 dark:text-gray-400 mb-4">
					No logs were found for the selected time range and filters.
				</p>
				<Button color="light" on:click={applyFilters}>
					<RefreshCcw class="mr-2 h-4 w-4" />
					Refresh
				</Button>
			</div>
		{:else}
			<div class="space-y-4">
				<!-- Log Stats -->
				<div
					class="flex flex-wrap items-center justify-between gap-2 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg"
				>
					<div class="text-sm text-gray-600 dark:text-gray-400">
						Showing {processedLogs.length} logs
					</div>
					<div class="text-sm text-gray-600 dark:text-gray-400">
						{#if processedLogs.length > 0}
							<RenderTimeAgo timestamp={processedLogs[0]?.timestamp} class="inline" />
							to
							<RenderTimeAgo
								timestamp={processedLogs[processedLogs.length - 1]?.timestamp}
								class="inline"
							/>
						{/if}
					</div>
				</div>

				<!-- Log Display -->
				<div class="relative">
					{#if processedLogs.length > 0}
						<MonospaceText code={formatLogsForDisplay(processedLogs)} language={undefined} />
					{:else}
						<Alert color="yellow">
							<span class="font-medium">No logs match your filters.</span>
							Try adjusting your search query or time range.
						</Alert>
					{/if}
				</div>

				<!-- Pagination -->
				{#if showPagination}
					<div class="flex justify-center items-center gap-4 mt-6">
						<div class="flex items-center gap-2">
							{#if urlOffset > 0}
								<Button size="sm" color="light" on:click={() => handlePageChange(currentPage - 1)}>
									Previous
								</Button>
							{/if}
							<span class="text-sm text-gray-600 dark:text-gray-400">
								Page {currentPage}
							</span>
							{#if hasMorePages}
								<Button size="sm" color="light" on:click={() => handlePageChange(currentPage + 1)}>
									Next
								</Button>
							{/if}
						</div>
					</div>
				{/if}
			</div>
		{/if}
	</div>
</div>
