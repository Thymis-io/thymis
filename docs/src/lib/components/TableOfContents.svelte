<script lang="ts">
	// TOC will be populated with data in a future step
	let tocItems: Array<{id: string, text: string, level: number}> = $state([]);
</script>

<div class="sticky top-8">
	<h3 class="mb-4 text-sm font-semibold text-gray-900 uppercase tracking-wide">On this page</h3>

	{#if tocItems.length > 0}
		<nav>
			<ul class="space-y-2 text-sm">
				{#each tocItems as item}
					<li>
						<a
							href="#{item.id}"
							class="block text-gray-600 hover:text-gray-900 transition-colors duration-200 py-1"
							class:font-medium={item.level === 1}
							class:pl-0={item.level === 1}
							class:pl-3={item.level === 2}
							class:pl-6={item.level === 3}
						>
							{item.text}
						</a>
					</li>
				{/each}
			</ul>
		</nav>
	{:else}
		<div class="text-sm text-gray-500">
			Table of contents will be populated automatically
		</div>
	{/if}
</div>
