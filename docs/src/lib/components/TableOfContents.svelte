<script lang="ts">
    import { onMount } from 'svelte';

    let tocItems = $state<Array<{ text: string; id: string; level: number }>>([]);

    onMount(() => {
        // Find all headings in the main content area
        const headings = document.querySelectorAll('main h1, main h2, main h3, main h4, main h5, main h6');

        const items: Array<{ text: string; id: string; level: number }> = [];

        headings.forEach((heading, index) => {
            const text = heading.textContent || '';
            let id = heading.id;

            // If heading doesn't have an ID, create one
            if (!id) {
                id = text.toLowerCase()
                    .replace(/[^\w\s-]/g, '')
                    .replace(/\s+/g, '-')
                    .trim();

                // Ensure uniqueness
                if (document.getElementById(id)) {
                    id = `${id}-${index}`;
                }

                heading.id = id;
            }

            const level = parseInt(heading.tagName.charAt(1));
            items.push({ text, id, level });
        });

        tocItems = items;
    });

    function scrollToHeading(id: string) {
        const element = document.getElementById(id);
        if (element) {
            element.scrollIntoView({ behavior: 'smooth' });
        }
    }
</script>

{#if tocItems.length > 0}
    <div class="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-6">
        <h3 class="text-sm font-semibold text-gray-900 mb-3">Table of Contents</h3>
        <ul class="space-y-1 text-sm">
            {#each tocItems as item}
                <li style="margin-left: {(item.level - 1) * 0.75}rem">
                    <button
                        type="button"
                        onclick={() => scrollToHeading(item.id)}
                        class="text-gray-600 hover:text-gray-900 transition-colors text-left block w-full"
                    >
                        {item.text}
                    </button>
                </li>
            {/each}
        </ul>
    </div>
{/if}
