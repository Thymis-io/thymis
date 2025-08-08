<script>

</script>

<script context="module">
  import a from './defaultMarkdown/a.svelte';
  export { a };
  import img from './defaultMarkdown/img.svelte';
  export { img };
</script>

<slot>
  <!-- the mdsvex content will be slotted in here -->
</slot>
