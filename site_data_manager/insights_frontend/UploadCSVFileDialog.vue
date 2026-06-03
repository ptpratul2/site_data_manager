<script setup lang="ts">
import { FileUploader, createListResource, call } from 'frappe-ui'
import { __ } from '../translation'
import { FileUp } from 'lucide-vue-next'
import { computed, reactive, ref, watch } from 'vue'
import DataTable from '../components/DataTable.vue'
import { QueryResultColumn, QueryResultRow } from '../types/query.types'
import { createToast } from '../helpers/toasts'

const show = defineModel()

const fileUploaded = ref(false)
const csvData = reactive({
	loading: false,
	file: null as File | null,
	tablename: '',
	columns: [] as QueryResultColumn[],
	rows: [] as QueryResultRow[],
	totalRowCount: 0,
})

const selectedFolder = ref('')

// Query Site Folder doctype directly — Frappe's permission layer filters by User Permission automatically.
// is_group=0 means leaf (uploadable) folders only.
const folderResource = createListResource({
	doctype: 'Site Folder',
	filters: { is_group: 0 },
	fields: ['name', 'folder_name', 'parent_site_folder'],
	orderBy: 'folder_name asc',
	pageLength: 500,
	auto: false,
})

const folderOptions = computed(() =>
	(folderResource.data || []).map((f: any) => ({
		label: f.parent_site_folder ? `${f.parent_site_folder} → ${f.folder_name || f.name}` : (f.folder_name || f.name),
		value: f.name,
	}))
)

watch(show, (isOpen) => {
	if (isOpen) {
		folderResource.fetch()
	} else {
		resetFile()
	}
})

function uploadFile(file: File) {
	// Mark as loading (shows spinner in place of upload zone) but NOT yet as uploaded
	csvData.loading = true
	csvData.file = file
	return call('insights.api.get_file_data', { filename: file.name })
		.then((data: any) => {
			csvData.tablename = data.tablename || (file as any).file_name?.split('.')[0] || 'imported_table'
			csvData.columns = data.columns || []
			csvData.rows = data.rows || []
			csvData.totalRowCount = data.total_rows || 0
			// Only switch to preview once we have data
			fileUploaded.value = true
		})
		.catch((error: any) => {
			createToast({
				title: __('Upload Failed'),
				message: error?.message || __('Failed to process uploaded file'),
				variant: 'error',
			})
		})
		.finally(() => {
			csvData.loading = false
		})
}

const importing = ref(false)
const importDisabled = computed(
	() =>
		!selectedFolder.value ||
		!csvData.file ||
		!csvData.tablename ||
		!csvData.columns.length ||
		importing.value,
)

function importCSVData() {
	if (!selectedFolder.value) {
		createToast({
			title: __('Site Folder required'),
			message: __('Select a sub-folder under its parent folder.'),
			variant: 'error',
		})
		return
	}
	if (importDisabled.value || !csvData.file) return

	importing.value = true
	return call('insights.api.import_csv_data', {
		filename: csvData.file.name,
		tablename: csvData.tablename,
		site_folder: selectedFolder.value,
	})
		.then(() => {
			createToast({
				title: __('Table Imported'),
				message: __(`Table '{0}' imported successfully`, csvData.tablename),
				variant: 'success',
			})
			show.value = false
		})
		.catch((error: any) => {
			createToast({
				title: __('Import Failed'),
				message: error?.message || __('Failed to import table'),
				variant: 'error',
			})
		})
		.finally(() => {
			importing.value = false
		})
}

function resetFile() {
	fileUploaded.value = false
	csvData.file = null
	csvData.tablename = ''
	csvData.columns = []
	csvData.rows = []
	csvData.totalRowCount = 0
	selectedFolder.value = ''
}
</script>

<template>
	<Dialog
		v-model="show"
		:options="{
			title: fileUploaded ? __('Import Table') : __('Upload CSV/Excel/JSON File'),
			size: fileUploaded ? '4xl' : 'lg',
			paddingTop: '8vh',
		}"
	>
		<template #body-content>
			<div class="flex flex-col" style="max-height: min(78vh, 720px)">
				<!-- Scrollable content area -->
				<div class="min-h-0 flex-1 overflow-y-auto space-y-4 pb-1">
					<!-- Site Folder picker -->
					<div>
						<label class="mb-1.5 block text-xs text-gray-600">
							{{ __('Site Folder') }} <span class="text-red-500">*</span>
						</label>
						<select
							v-model="selectedFolder"
							:disabled="folderResource.loading"
							class="w-full rounded border border-gray-300 bg-white px-2.5 py-1.5 text-sm text-gray-800 focus:border-gray-500 focus:outline-none disabled:opacity-50"
						>
							<option value="">
								{{ folderResource.loading ? __('Loading…') : __('— Select Folder —') }}
							</option>
							<option v-for="opt in folderOptions" :key="opt.value" :value="opt.value">
								{{ opt.label }}
							</option>
						</select>
						<p v-if="!folderResource.loading && !folderOptions.length" class="mt-1 text-xs text-amber-600">
							{{ __('No upload folders found. Create a sub-folder under Site Folder in Desk.') }}
						</p>
					</div>

					<!-- File upload drop zone (hidden while loading or after data is ready) -->
					<FileUploader
						v-if="!csvData.loading && !fileUploaded"
						:uploadArgs="{ private: true }"
						:file-types="['.csv', '.xlsx', '.json', '.jsonl']"
						@success="uploadFile"
					>
						<template #default="{ progress, uploading, openFileSelector }">
							<div
								class="flex flex-col items-center gap-4 rounded border border-dashed border-gray-400 p-8"
							>
								<div
									class="flex cursor-pointer flex-col items-center justify-center gap-2 text-center"
									@click="openFileSelector"
								>
									<FileUp
										v-if="!uploading"
										class="h-6 w-6 text-gray-600"
										stroke-width="1.2"
									/>
									<p v-if="!uploading" class="text-sm font-medium text-gray-800">
										{{ __('or drag and drop a file here') }}
									</p>
									<div v-else class="flex w-[15rem] flex-col gap-2">
										<div class="h-2 w-full rounded-full bg-gray-200">
											<div
												class="h-2 rounded-full bg-blue-500 transition-all"
												:style="{ width: `${progress}%` }"
											></div>
										</div>
										<p class="text-xs">{{ __('Uploading...') }}</p>
									</div>
								</div>
								<Button
									v-if="!uploading"
									variant="solid"
									:label="__('Upload File')"
									@click="openFileSelector"
								>
									<template #prefix>
										<FileUp class="h-4 w-4" stroke-width="1.5" />
									</template>
								</Button>
							</div>
						</template>
					</FileUploader>

					<!-- Processing spinner shown after file upload while get_file_data is running -->
					<div
						v-else-if="csvData.loading"
						class="flex flex-col items-center gap-3 rounded border border-dashed border-gray-300 p-10 text-gray-500"
					>
						<div class="h-5 w-5 animate-spin rounded-full border-2 border-gray-300 border-t-blue-500"></div>
						<p class="text-sm">{{ __('Reading file…') }}</p>
					</div>

					<!-- Preview after file is processed -->
					<div v-else-if="fileUploaded" class="flex flex-col gap-3">
						<FormControl
							class="w-full max-w-md"
							:label="__('Table Name')"
							v-model="csvData.tablename"
						/>
						<div class="overflow-hidden rounded border bg-white" style="max-height: min(36vh, 20rem)">
							<DataTable
								v-if="csvData.columns.length"
								class="h-full"
								:columns="csvData.columns"
								:rows="csvData.rows"
							/>
						</div>
						<p class="tnum text-sm text-gray-600">
							{{ __('Total Rows:') }} {{ csvData.totalRowCount.toLocaleString() }}
						</p>
					</div>
				</div>

				<!-- Action buttons — always pinned at the bottom -->
				<div
					v-if="fileUploaded"
					class="mt-3 flex flex-shrink-0 items-center justify-end gap-2 border-t pt-3"
				>
					<Button :label="__('Reset File')" @click="resetFile" />
					<Button
						variant="solid"
						:label="__('Import')"
						:loading="importing"
						:disabled="importDisabled"
						@click="importCSVData"
					/>
				</div>
			</div>
		</template>
	</Dialog>
</template>
