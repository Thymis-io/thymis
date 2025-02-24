<script lang="ts">
	import { t } from 'svelte-i18n';
	import { ToolbarButton, Popover } from 'flowbite-svelte';
	import Logout from 'lucide-svelte/icons/log-out';
	import User from 'lucide-svelte/icons/user-round';
	import LanguageSelect from './LanguageSelect.svelte';
</script>

<ToolbarButton size="lg"><User size={18} /></ToolbarButton>
<Popover arrow={false} trigger="click" placement="bottom">
	<div class="flex flex-col gap-2 p-2">
		<div class="flex items-center justify-center w-max">
			<LanguageSelect />
		</div>
		<a
			href="/auth/logout"
			class="flex p-2 gap-2 items-center rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600"
		>
			<Logout size={18} />
			{$t('common.logout')}
		</a>
	</div>
</Popover>
