<script lang="ts">
    let { children } = $props();
</script>
<ul class="space-y-1 list-none pl-0 [&_ul]:ml-4 [&_ul]:mt-2">
    {@render children()}
</ul>
