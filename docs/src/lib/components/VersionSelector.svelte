<script lang="ts">
	let isOpen = $state(false);

	// Check if we're in development mode
    // needs to be get from env
	const isDevelopment = false;

    const versions: Record<string, string> = {
        "v0.7": "https://github.com/Thymis-io/thymis/blob/v0.7/docs/src/lib/docs/SUMMARY.md",
        "v0.6": "https://github.com/Thymis-io/thymis/blob/v0.6/docs/src/lib/docs/SUMMARY.md",
        "v0.5": "https://github.com/Thymis-io/thymis/blob/v0.5/docs/src/SUMMARY.md",
        "v0.4": "https://github.com/Thymis-io/thymis/blob/v0.4/docs/src/SUMMARY.md",
        "v0.3": "https://github.com/Thymis-io/thymis/blob/v0.3/docs/src/SUMMARY.md",
	}

    if (isDevelopment) {
		versions["development version"] = "https://github.com/Thymis-io/thymis"
    }

	const currentVersion = isDevelopment ? "development version" : Object.keys(versions)[0];

	function toggleDropdown() {
		isOpen = !isOpen;
	}

	function closeDropdown() {
		isOpen = false;
	}

	function getGitHubUrl(version: string) {
		return versions[version]
	}

	function handleVersionClick(event: MouseEvent, versionItem: typeof versions[0], position: number) {
		closeDropdown();

		// If it's the current version (first item), prevent navigation
		if (position === 0) {
			event.preventDefault();
			return;
		}
	}

	// Close dropdown when clicking outside
	function handleOutsideClick(event: MouseEvent) {
		const target = event.target as Element;
		if (!target.closest('.version-selector')) {
			closeDropdown();
		}
	}
</script>

<svelte:window on:click={handleOutsideClick} />

<div class="version-selector relative">
	<button
		type="button"
		onclick={toggleDropdown}
		class="flex items-center space-x-2 rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
		aria-haspopup="true"
		aria-expanded={isOpen}
	>
		<span>{isDevelopment ? currentVersion : `latest version (${currentVersion})`}</span>
		<i class="fas fa-chevron-down w-3 h-3 transition-transform" class:rotate-180={isOpen}></i>
	</button>

	{#if isOpen}
		<div class="absolute left-0 mt-2 w-48 rounded-md border border-gray-200 bg-white shadow-lg z-50">
			<div class="py-1">
				{#each Object.keys(versions) as versionItem, position}
					<a
						href={getGitHubUrl(versionItem)}
						target="_blank"
						rel="noopener noreferrer"
						onclick={(event) => handleVersionClick(event, versionItem, position)}
						class="flex items-center justify-between px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors {position === 0 ? 'cursor-default' : ''}"
					>
						<span>{versionItem}</span>
						{#if position === 0}
							<span class="text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full">Current</span>
						{/if}
					</a>
				{/each}
				<div class="border-t border-gray-100 mt-1 pt-1">
					<a
						href="https://github.com/Thymis-io/thymis/releases"
						target="_blank"
						rel="noopener noreferrer"
						onclick={closeDropdown}
						class="flex items-center px-4 py-2 text-sm text-gray-500 hover:bg-gray-100 transition-colors"
					>
						<i class="fab fa-github w-4 h-4 mr-2"></i>
						View all releases
					</a>
				</div>
			</div>
		</div>
	{/if}
</div>
