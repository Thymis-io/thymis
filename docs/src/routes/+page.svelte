<script lang="ts">
    const modules = import.meta.glob('$lib/docs/**/*.md', { eager: true });
    console.log(JSON.stringify(Object.keys(modules)));
    // 16:04:09.735 ["/src/lib/docs/SIDEBAR.md","/src/lib/docs/api.md","/src/lib/docs/architecture.md","/src/lib/docs/development.md","/src/lib/docs/extensions.md","/src/lib/docs/getting_started/index.md","/src/lib/docs/getting_started/nixos.md","/src/lib/docs/index.md","/src/lib/docs/usage/existing_device.md","/src/lib/docs/usage/index.md","/src/lib/docs/usage/provisioning.md","/src/lib/docs/usage/system_configuration.md","/src/lib/docs/usage/terminal.md","/src/lib/docs/usage/vnc.md"] +page.svelte:3:13

    // we want to show SIDEBAR.md in the sidebar
    const Sidebar = modules['/src/lib/docs/SIDEBAR.md'].default;

    // and let's show the index.md here

    const Index = modules['/src/lib/docs/index.md'].default;

    console.log(Sidebar);
</script>

<!-- Tailwind CSS -->

<div class="container mx-auto px-4">
    <div class="sidebar w-1/4">
        <Sidebar />
    </div>
    <div class="content w-3/4">
        <Index />
    </div>
</div>
