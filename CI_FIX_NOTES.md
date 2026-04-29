# CI Fix Notes — nav:visible strict mode violations

## Problem

Playwright strict mode violations in `screencaps.spec.ts` and `utils.ts`:

```
locator('nav:visible').locator('a').filter({ hasText: 'Configs' }) resolved to 2 elements
```

Tests fail consistently (3 retries each) on 1920×1080 viewport.

## Root Cause

The layout has **two** `<Sidebar>` instances:

1. **Mobile drawer** (`+layout.svelte`): wrapped in a div, hidden at lg+ via `lg:hidden`
2. **Desktop sidebar** (`MainWindow.svelte`): always present, always visible at lg+

Both render `<nav>` elements. The visibility gating relied on Tailwind CSS classes
(`hidden`, `lg:hidden`, `lg:block`) to hide/show each sidebar at the appropriate breakpoint.

The issue: `Sidebar.svelte` passes `class={drawerHidden ? 'hidden' : ''}` to the flowbite
`<Sidebar>` component, whose `asideClass` includes `lg:block`. `twMerge` keeps **both**
`hidden` and `lg:block` (they're in different breakpoint conflict groups). In Tailwind v4
via `@tailwindcss/vite`, responsive variants are generated inside `@media` blocks which
appear **after** base utilities in the stylesheet — so `lg:block` wins over `hidden` at
1920px (>= 1024px).

This causes the mobile drawer aside to have `display: block` at 1920px despite the parent
div also having `hidden` / `lg:hidden`. While the parent div should enforce `display: none`,
Playwright ends up seeing both `<nav>` elements as `:visible`, triggering the strict-mode
violation.

Prior fix attempts:
- `1d5def3b`: replaced flowbite `<Sidebar>` with plain `<aside>` — WORKED, but was reverted
- `bde0104a`: pinned flowbite-svelte to 0.48.6, reverted Sidebar — did NOT fix
- `1f5a9f7f` / `013b28d0`: pinned tailwindcss/flowbite versions — did NOT fix
- `23524b39`: removed `block` class from mobile drawer wrapper — did NOT fix

## Fix

Remove the mobile drawer sidebar from the DOM entirely when it is closed, using Svelte's
`{#if !drawerHidden}` conditional rendering:

```svelte
<!-- Before -->
<div class="h-screen z-50 {drawerHidden ? 'hidden' : ''} lg:hidden">
    <Sidebar ... bind:drawerHidden />
</div>

<!-- After -->
{#if !drawerHidden}
    <div class="h-screen z-50 lg:hidden">
        <Sidebar ... bind:drawerHidden />
    </div>
{/if}
```

**Why this works:**
- At 1920px (test viewport), `drawerHidden` is always `true` (hamburger is `lg:hidden`,
  so the drawer is never opened). The mobile sidebar never enters the DOM.
- At small viewports, the mobile sidebar is only rendered when the drawer is open
  (`drawerHidden=false`), which is the only time it should be visible anyway.
- The desktop sidebar in `MainWindow.svelte` is unaffected.

**File changed:** `frontend/src/routes/(authenticated)/+layout.svelte`
