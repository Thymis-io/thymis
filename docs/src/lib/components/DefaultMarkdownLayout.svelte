<script>

</script>

<script context="module">
  import a from './defaultMarkdown/a.svelte';
  import img from './defaultMarkdown/img.svelte';
  import pre from './defaultMarkdown/pre.svelte';
  export { a, img, pre };
</script>

<slot>
  <!-- the mdsvex content will be slotted in here -->
</slot>
