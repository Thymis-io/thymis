<script lang="ts">
    import { page } from '$app/stores';

    const currentYear = new Date().getFullYear();
</script>

<footer class="border-t border-gray-200 mt-16 pt-8 pb-8">
    <div class="max-w-4xl">
        <div class="flex flex-col md:flex-row justify-between items-center text-sm text-gray-600">
            <div class="flex items-center space-x-4 mb-4 md:mb-0">
                <span>&copy; {currentYear} Thymis Documentation</span>
                <a href="https://thymis.io" class="hover:text-gray-900 transition-colors">
                    Visit thymis.io
                </a>
            </div>

            <div class="flex items-center space-x-4">
                <span class="text-xs">
                    Built with SvelteKit & Tailwind CSS
                </span>
            </div>
        </div>
    </div>
</footer>
