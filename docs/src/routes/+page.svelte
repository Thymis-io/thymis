<script lang="ts">
    import { goto } from '$app/navigation';
    import { onMount } from 'svelte';

    onMount(() => {
        goto('/index');
    });
</script>

<div class="min-h-screen bg-gray-50 flex items-center justify-center">
    <div class="text-center">
        <h1 class="text-2xl font-bold text-gray-900 mb-4">Thymis Documentation</h1>
        <p class="text-gray-600">Redirecting to documentation...</p>
    </div>
</div>
