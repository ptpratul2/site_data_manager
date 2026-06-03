<script setup lang="tsx">
import { watchDebounced } from '@vueuse/core'
import { Breadcrumbs } from 'frappe-ui'
import {
	MoreHorizontal,
	RefreshCcw,
	SearchIcon,
	FileText,
	Upload,
	Trash2,
} from 'lucide-vue-next'
import { call } from 'frappe-ui'
import { computed, h, onMounted, provide, ref, watch, watchEffect } from 'vue'
import { useRouter } from 'vue-router'
import useDataSourceStore from './data_source'
import useTableStore, { DataSourceTable } from './tables'
import UploadCSVFileDialog from './UploadCSVFileDialog.vue'
import FolderTreeBranch from './FolderTreeBranch.vue'
import { confirmDialog } from '../helpers/confirm_dialog'
import { attachRealtimeListener } from '../helpers/index.ts'
import { createToast } from '../helpers/toasts'
import session from '../session'
import { __ } from '../translation'

type FolderNode = {
	name: string
	folder_name: string
	is_group?: number
	children?: FolderNode[]
}

const props = defineProps<{ name: string }>()
const router = useRouter()

const dataSource = useDataSourceStore().getSource(props.name)
const tableStore = useTableStore()
const isUploadsDataSource = computed(() => props.name === 'uploads')
const showUploadDialog = ref(false)

const searchQuery = ref('')
const filteredTables = ref<DataSourceTable[]>([])
const folderTree = ref<FolderNode[]>([])
const expandedFolders = ref<Record<string, boolean>>({})
const deletingTable = ref<string | null>(null)
const loading = ref(false)

const canDeleteUploads = computed(
	() => isUploadsDataSource.value && Boolean(session.user.can_delete_uploads),
)

const tablesByFolderDoc = computed(() => {
	const map: Record<string, DataSourceTable[]> = {}
	for (const table of filteredTables.value) {
		const key = table.custom_site_folder_doc || table.custom_site_folder
		if (!key) continue
		if (!map[key]) map[key] = []
		map[key].push(table)
	}
	return map
})

const unassignedTables = computed(() =>
	filteredTables.value.filter((t) => !(t.custom_site_folder_doc || t.custom_site_folder)),
)

watchDebounced(searchQuery, () => updateTablesList(), { debounce: 300, immediate: true })

async function refreshUploads() {
	if (!isUploadsDataSource.value) return updateTablesList()

	loading.value = true
	try {
		await session.fetchSessionInfo()
		const [treeRes] = await Promise.all([
			call('insights.api.get_site_folder_tree'),
			updateTablesList(),
		])
		folderTree.value = treeRes || []
		for (const node of folderTree.value) {
			initExpanded(node)
		}
	} catch (error: any) {
		createToast({
			title: __('Could not load folders'),
			message: error?.message || __('Try Refresh from the menu.'),
			variant: 'error',
		})
	} finally {
		loading.value = false
	}
}

function initExpanded(node: FolderNode) {
	if (expandedFolders.value[node.name] === undefined) {
		expandedFolders.value[node.name] = true
	}
	for (const child of node.children || []) {
		initExpanded(child)
	}
}

function updateTablesList() {
	return tableStore.getTables(props.name, searchQuery.value).then((tables) => {
		filteredTables.value = tables || []
	})
}

onMounted(() => {
	if (isUploadsDataSource.value) refreshUploads()
	else updateTablesList()
})

watch(
	() => props.name,
	() => (isUploadsDataSource.value ? refreshUploads() : updateTablesList()),
)

function onPermissionsUpdated(data?: { user?: string }) {
	if (data?.user && data.user !== session.user.email) return
	refreshUploads()
}

attachRealtimeListener('update_user_permissions', onPermissionsUpdated)
attachRealtimeListener('insights_upload_permissions_updated', onPermissionsUpdated)

watch(showUploadDialog, (open, wasOpen) => {
	if (wasOpen && !open && isUploadsDataSource.value) refreshUploads()
})

function toggleFolder(name: string) {
	expandedFolders.value[name] = !expandedFolders.value[name]
}

function countInSubtree(node: FolderNode): number {
	let n = (tablesByFolderDoc.value[node.name] || []).length
	for (const child of node.children || []) {
		n += countInSubtree(child)
	}
	return n
}

function goToTable(tableName: string) {
	router.push(`/data-source/${props.name}/${encodeURIComponent(tableName)}`)
}

function confirmDeleteTable(table: DataSourceTable) {
	confirmDialog({
		title: __('Delete uploaded file'),
		message: __(
			'Permanently delete table "{0}"? This removes the data from Insights and cannot be undone.',
			table.table_name,
		),
		primaryActionLabel: __('Delete'),
		theme: 'red',
		onSuccess: () => {
			deletingTable.value = table.table_name
			return call('insights.api.delete_uploaded_table', { table_name: table.table_name })
				.then(() => {
					createToast({
						title: __('Deleted'),
						message: __(`Table '{0}' was deleted.`, table.table_name),
						variant: 'success',
					})
					return refreshUploads()
				})
				.catch((error: Error) => {
					createToast({
						title: __('Delete failed'),
						message: error?.message || __('Could not delete this table.'),
						variant: 'error',
					})
				})
				.finally(() => {
					deletingTable.value = null
				})
		},
	})
}

provide('uploadsTreeCtx', {
	tablesByFolder: tablesByFolderDoc,
	expandedFolders,
	countInSubtree,
	toggleFolder,
	goToTable,
	confirmDeleteTable,
	canDeleteUploads,
	deletingTable,
})

const dataSourceStore = useDataSourceStore()
watchEffect(() => {
	document.title = `Tables | ${props.name || dataSourceStore.getSource(props.name)?.title}`
})
</script>

<template>
	<header class="flex h-12 items-center justify-between border-b py-2.5 pl-5 pr-2">
		<Breadcrumbs
			:items="[
				{ label: __('Data Sources'), route: '/data-source' },
				{ label: dataSource?.title || props.name, route: `/data-source/${props.name}` },
			]"
		/>
		<Button
			v-if="isUploadsDataSource"
			variant="solid"
			:label="__('Upload File')"
			@click="showUploadDialog = true"
		>
			<template #prefix>
				<Upload class="h-4 w-4" stroke-width="1.5" />
			</template>
		</Button>
	</header>

	<div class="mb-4 flex min-h-0 flex-1 flex-col gap-3 overflow-auto px-5 py-3">
		<div class="flex gap-2 py-1">
			<FormControl placeholder="Search by Title" v-model="searchQuery" :debounce="300">
				<template #prefix>
					<SearchIcon class="h-4 w-4 text-gray-500" />
				</template>
			</FormControl>
			<Dropdown
				:options="[
					{
						label: __('Update Tables'),
						onClick: () =>
							tableStore
								.updateDataSourceTables(props.name)
								.then(() =>
									isUploadsDataSource ? refreshUploads() : updateTablesList(),
								),
						icon: () =>
							h(RefreshCcw, { class: 'h-4 w-4 text-gray-700', 'stroke-width': '1.5' }),
					},
				]"
			>
				<Button>
					<template #icon>
						<MoreHorizontal class="h-4 w-4 text-gray-700" stroke-width="1.5" />
					</template>
				</Button>
			</Dropdown>
		</div>

		<template v-if="isUploadsDataSource">
			<div v-if="loading" class="py-8 text-center text-sm text-gray-500">
				{{ __('Loading…') }}
			</div>
			<div
				v-else-if="filteredTables.length === 0"
				class="flex flex-col items-center justify-center rounded border border-dashed py-16 text-center"
			>
				<p class="text-sm font-medium text-gray-800">{{ __('No Tables Found') }}</p>
				<Button
					class="mt-3"
					variant="solid"
					:label="__('Upload File')"
					@click="showUploadDialog = true"
				/>
			</div>
			<div v-else class="flex flex-col gap-1.5 pb-4">
				<FolderTreeBranch
					v-for="root in folderTree"
					:key="root.name"
					:node="root"
					:depth="0"
				/>

				<template v-if="unassignedTables.length">
					<div class="my-3 text-xs font-semibold uppercase tracking-wider text-gray-400">
						{{ __('Other Files') }}
					</div>
					<div class="divide-y rounded border border-gray-200 bg-white">
						<div
							v-for="table in unassignedTables"
							:key="table.table_name"
							class="group flex items-center gap-2 px-3 py-2.5 hover:bg-gray-50"
						>
							<div
								class="flex min-w-0 flex-1 cursor-pointer items-center gap-3"
								@click="goToTable(table.table_name)"
							>
								<FileText class="h-4 w-4 text-gray-400" />
								<span class="truncate font-mono text-sm">{{ table.table_name }}</span>
							</div>
							<Button
								v-if="canDeleteUploads"
								variant="ghost"
								:label="__('Delete')"
								:loading="deletingTable === table.table_name"
								@click.stop="confirmDeleteTable(table)"
							>
								<template #prefix>
									<Trash2 class="h-4 w-4 text-gray-500 group-hover:text-red-600" />
								</template>
							</Button>
						</div>
					</div>
				</template>
			</div>
		</template>

		<ListView
			v-else
			class="h-full"
			:columns="[{ label: __('Table Name'), key: 'table_name' }]"
			:rows="filteredTables"
			row-key="table_name"
			:options="{
				showTooltip: false,
				getRowRoute: (table: DataSourceTable) => ({
					path: `/data-source/${props.name}/${table.table_name}`,
				}),
			}"
		/>
	</div>

	<UploadCSVFileDialog v-model="showUploadDialog" />
</template>
