<script setup lang="ts">
import { ChevronDown, ChevronRight, FileText, Folder, Trash2 } from 'lucide-vue-next'
import { computed, inject } from 'vue'
import { __ } from '../translation'

type FolderNode = {
	name: string
	folder_name: string
	children?: FolderNode[]
}

const props = defineProps<{
	node: FolderNode
	depth?: number
}>()

const ctx = inject('uploadsTreeCtx') as {
	tablesByFolder: { value: Record<string, any[]> }
	expandedFolders: { value: Record<string, boolean> }
	countInSubtree: (node: FolderNode) => number
	toggleFolder: (name: string) => void
	goToTable: (tableName: string) => void
	confirmDeleteTable: (table: any) => void
	canDeleteUploads: { value: boolean }
	deletingTable: { value: string | null }
}

const depth = computed(() => props.depth ?? 0)
const tables = computed(() => ctx.tablesByFolder.value[props.node.name] || [])
const count = computed(() => ctx.countInSubtree(props.node))
const open = computed(() => ctx.expandedFolders.value[props.node.name] !== false)
const displayName = computed(() => props.node.folder_name || props.node.name)
const show = computed(
	() => count.value > 0 || (props.node.children && props.node.children.length > 0),
)
</script>

<template>
	<div
		v-if="show"
		class="overflow-hidden rounded border border-gray-200"
		:class="depth ? 'mt-1 border-gray-100' : 'mb-1.5'"
		:style="depth ? { marginLeft: `${depth * 16}px` } : undefined"
	>
		<div
			class="flex cursor-pointer items-center justify-between border-b border-gray-200 bg-gray-50 p-3 transition-colors hover:bg-gray-100"
			@click="ctx.toggleFolder(node.name)"
		>
			<div class="flex items-center gap-3">
				<ChevronDown v-if="open" class="h-4 w-4 text-gray-500" />
				<ChevronRight v-else class="h-4 w-4 text-gray-500" />
				<Folder class="h-4 w-4 fill-blue-100 text-blue-500" />
				<span class="text-sm font-medium text-gray-800">{{ displayName }}</span>
			</div>
			<span class="rounded-full bg-gray-200 px-2 py-0.5 text-xs text-gray-500">
				{{ count }} {{ count === 1 ? __('table') : __('tables') }}
			</span>
		</div>
		<div v-show="open" class="divide-y divide-gray-100 bg-white">
			<div
				v-for="table in tables"
				:key="table.table_name"
				class="group flex items-center gap-2 py-2.5 pl-11 pr-3 transition-colors hover:bg-blue-50/40"
			>
				<div
					class="flex min-w-0 flex-1 cursor-pointer items-center gap-3"
					@click="ctx.goToTable(table.table_name)"
				>
					<FileText class="h-4 w-4 shrink-0 text-gray-400" />
					<span class="truncate font-mono text-sm text-gray-700">{{ table.table_name }}</span>
				</div>
				<Button
					v-if="ctx.canDeleteUploads.value"
					variant="ghost"
					:label="__('Delete')"
					:loading="ctx.deletingTable.value === table.table_name"
					@click.stop="ctx.confirmDeleteTable(table)"
				>
					<template #prefix>
						<Trash2 class="h-4 w-4 text-gray-500 group-hover:text-red-600" />
					</template>
				</Button>
			</div>
			<FolderTreeBranch
				v-for="child in node.children"
				:key="child.name"
				:node="child"
				:depth="depth + 1"
			/>
		</div>
	</div>
</template>
