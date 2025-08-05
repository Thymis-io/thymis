<script>

</script>

<script context="module">
  import a from './summary/a.svelte';
  import li from './summary/li.svelte';
  import ul from './summary/ul.svelte';

  export { a, li, ul };
</script>

<slot>
  <!-- the mdsvex content will be slotted in here -->
</slot>
