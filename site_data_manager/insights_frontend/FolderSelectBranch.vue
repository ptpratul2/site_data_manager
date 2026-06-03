<script setup lang="ts">
import { ChevronRight, Folder } from 'lucide-vue-next'
import type { FolderSelectNode } from './FolderSelectTree.vue'
import FolderSelectBranch from './FolderSelectBranch.vue'

const props = defineProps<{
	node: FolderSelectNode
	depth: number
	selected: string
}>()

const emit = defineEmits<{
	select: [node: FolderSelectNode]
}>()

function isGroup(node: FolderSelectNode) {
	return Boolean(node.is_group) || Boolean(node.children?.length)
}

const group = isGroup(props.node)
const label = props.node.folder_name || props.node.name
</script>

<template>
	<div
		class="flex cursor-pointer items-center gap-2 py-2 pr-3 text-sm"
		:class="[
			group ? 'font-medium text-gray-700' : 'text-gray-800 hover:bg-blue-50',
			!group && selected === node.name ? 'bg-blue-100 font-medium text-blue-900' : '',
		]"
		:style="{ paddingLeft: `${12 + depth * 16}px` }"
		@click="emit('select', node)"
	>
		<Folder v-if="group" class="h-4 w-4 shrink-0 fill-amber-100 text-amber-600" />
		<ChevronRight v-else class="h-3 w-3 shrink-0 text-gray-400" />
		<span class="truncate">{{ label }}</span>
	</div>
	<FolderSelectBranch
		v-for="child in node.children || []"
		:key="child.name"
		:node="child"
		:depth="depth + 1"
		:selected="selected"
		@select="emit('select', $event)"
	/>
</template>
