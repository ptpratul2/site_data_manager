<script setup lang="ts">
import { computed } from 'vue'
import { __ } from '../translation'
import FolderSelectBranch from './FolderSelectBranch.vue'

export type FolderSelectNode = {
	name: string
	folder_name: string
	is_group?: number
	children?: FolderSelectNode[]
}

const props = defineProps<{
	tree: FolderSelectNode[]
	modelValue: string
}>()

const emit = defineEmits<{
	'update:modelValue': [value: string]
}>()

const selected = computed({
	get: () => props.modelValue,
	set: (v: string) => emit('update:modelValue', v),
})

function selectNode(node: FolderSelectNode) {
	const isGroup = Boolean(node.is_group) || Boolean(node.children?.length)
	if (isGroup) return
	selected.value = node.name
}
</script>

<template>
	<div class="max-h-48 overflow-y-auto rounded border border-gray-200 bg-gray-50/50 py-1">
		<FolderSelectBranch
			v-for="node in tree"
			:key="node.name"
			:node="node"
			:depth="0"
			:selected="selected"
			@select="selectNode"
		/>
		<p v-if="!tree.length" class="px-3 py-2 text-xs text-gray-500">
			{{ __('No folders found.') }}
		</p>
	</div>
</template>
