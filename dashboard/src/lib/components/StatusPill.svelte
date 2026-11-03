<script lang="ts">
	import type { Status } from '../types';

	let { status }: { status: Status } = $props();
</script>

<span data-status={status}></span>
