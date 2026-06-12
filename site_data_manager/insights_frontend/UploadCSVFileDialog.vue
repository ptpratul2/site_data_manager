<script setup lang="ts">
import { FileUploader, createListResource, call } from 'frappe-ui'
import { __ } from '../translation'
import { FileUp, Sheet } from 'lucide-vue-next'
import { computed, reactive, ref, watch } from 'vue'
import DataTable from '../components/DataTable.vue'
import { QueryResultColumn, QueryResultRow } from '../types/query.types'
import { createToast } from '../helpers/toasts'

const props = withDefaults(
	defineProps<{
		initialMode?: 'file' | 'sheet'
	}>(),
	{ initialMode: 'file' },
)

const show = defineModel()

const uploadMode = ref<'file' | 'sheet'>('file')
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
const sheetUrl = ref('')
const syncInterval = ref('30')
const sheetPreviewReady = ref(false)

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
	})),
)

const syncIntervalOptions = [
	{ label: __('Every 15 minutes'), value: '15' },
	{ label: __('Every 30 minutes'), value: '30' },
	{ label: __('Every 60 minutes'), value: '60' },
	{ label: __('Every 2 hours'), value: '120' },
]

watch(show, (isOpen) => {
	if (isOpen) {
		uploadMode.value = props.initialMode
		folderResource.fetch()
	} else {
		resetAll()
	}
})

function uploadFile(file: File) {
	csvData.loading = true
	csvData.file = file
	return call('insights.api.get_file_data', { filename: file.name })
		.then((data: any) => {
			csvData.tablename = data.tablename || (file as any).file_name?.split('.')[0] || 'imported_table'
			csvData.columns = data.columns || []
			csvData.rows = data.rows || []
			csvData.totalRowCount = data.total_rows || 0
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

function previewGoogleSheet() {
	const url = sheetUrl.value.trim()
	if (!url) {
		createToast({
			title: __('URL required'),
			message: __('Paste a Google Sheets link.'),
			variant: 'error',
		})
		return
	}

	csvData.loading = true
	sheetPreviewReady.value = false
	return call('site_data_manager.api.google_sheets.preview_google_sheet', { url })
		.then((data: any) => {
			csvData.tablename = data.tablename || 'google_sheet_import'
			csvData.columns = data.columns || []
			csvData.rows = data.rows || []
			csvData.totalRowCount = data.total_rows || 0
			sheetPreviewReady.value = true
		})
		.catch((error: any) => {
			createToast({
				title: __('Preview Failed'),
				message: error?.message || __('Could not read Google Sheet. Ensure it is shared as "Anyone with the link can view".'),
				variant: 'error',
			})
		})
		.finally(() => {
			csvData.loading = false
		})
}

const importing = ref(false)
const fileImportDisabled = computed(
	() =>
		!selectedFolder.value ||
		!csvData.file ||
		!csvData.tablename ||
		!csvData.columns.length ||
		importing.value,
)
const sheetImportDisabled = computed(
	() =>
		!selectedFolder.value ||
		!sheetUrl.value.trim() ||
		!csvData.tablename ||
		!csvData.columns.length ||
		!sheetPreviewReady.value ||
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
	if (fileImportDisabled.value || !csvData.file) return

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

function linkGoogleSheet() {
	if (!selectedFolder.value) {
		createToast({
			title: __('Site Folder required'),
			message: __('Select a sub-folder under its parent folder.'),
			variant: 'error',
		})
		return
	}
	if (sheetImportDisabled.value) return

	importing.value = true
	return call('site_data_manager.api.google_sheets.link_google_sheet', {
		url: sheetUrl.value.trim(),
		tablename: csvData.tablename,
		site_folder: selectedFolder.value,
		sync_interval_minutes: Number(syncInterval.value) || 30,
	})
		.then(() => {
			createToast({
				title: __('Google Sheet Linked'),
				message: __(`Table '{0}' linked and synced. Data will refresh automatically.`, csvData.tablename),
				variant: 'success',
			})
			show.value = false
		})
		.catch((error: any) => {
			createToast({
				title: __('Link Failed'),
				message: error?.message || __('Failed to link Google Sheet'),
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
}

function resetSheet() {
	sheetUrl.value = ''
	sheetPreviewReady.value = false
	csvData.tablename = ''
	csvData.columns = []
	csvData.rows = []
	csvData.totalRowCount = 0
}

function resetAll() {
	resetFile()
	resetSheet()
	selectedFolder.value = ''
	syncInterval.value = '30'
	csvData.loading = false
}

const showPreview = computed(
	() => uploadMode.value === 'file' ? fileUploaded.value : sheetPreviewReady.value,
)
const dialogTitle = computed(() => {
	if (showPreview.value) return __('Import Table')
	return uploadMode.value === 'sheet' ? __('Link Google Sheet') : __('Upload CSV/Excel/JSON File')
})
</script>

<template>
	<Dialog
		v-model="show"
		:options="{
			title: dialogTitle,
			size: showPreview ? '4xl' : 'lg',
			paddingTop: '8vh',
		}"
	>
		<template #body-content>
			<div class="flex flex-col" style="max-height: min(78vh, 720px)">
				<div class="min-h-0 flex-1 overflow-y-auto space-y-4 pb-1">
					<!-- Site Folder picker (shared) -->
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

					<!-- Mode tabs -->
					<div class="flex gap-1 rounded-lg border border-gray-200 bg-gray-50 p-1">
						<button
							type="button"
							class="flex flex-1 items-center justify-center gap-1.5 rounded-md px-3 py-1.5 text-sm transition-colors"
							:class="uploadMode === 'file' ? 'bg-white font-medium text-gray-900 shadow-sm' : 'text-gray-600 hover:text-gray-800'"
							@click="uploadMode = 'file'"
						>
							<FileUp class="h-4 w-4" stroke-width="1.5" />
							{{ __('Upload File') }}
						</button>
						<button
							type="button"
							class="flex flex-1 items-center justify-center gap-1.5 rounded-md px-3 py-1.5 text-sm transition-colors"
							:class="uploadMode === 'sheet' ? 'bg-white font-medium text-gray-900 shadow-sm' : 'text-gray-600 hover:text-gray-800'"
							@click="uploadMode = 'sheet'"
						>
							<Sheet class="h-4 w-4" stroke-width="1.5" />
							{{ __('Link Google Sheet') }}
						</button>
					</div>

					<!-- File upload mode -->
					<template v-if="uploadMode === 'file'">
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
					</template>

					<!-- Google Sheet mode -->
					<template v-else>
						<div>
							<label class="mb-1.5 block text-xs text-gray-600">
								{{ __('Google Sheet URL') }} <span class="text-red-500">*</span>
							</label>
							<input
								v-model="sheetUrl"
								type="url"
								class="w-full rounded border border-gray-300 bg-white px-2.5 py-1.5 text-sm text-gray-800 focus:border-gray-500 focus:outline-none"
								:placeholder="__('https://docs.google.com/spreadsheets/d/...')"
							/>
							<p class="mt-1 text-xs text-gray-500">
								{{ __('Share the sheet as "Anyone with the link can view", then paste the browser URL here.') }}
							</p>
						</div>

						<div>
							<label class="mb-1.5 block text-xs text-gray-600">{{ __('Auto Sync Interval') }}</label>
							<select
								v-model="syncInterval"
								class="w-full rounded border border-gray-300 bg-white px-2.5 py-1.5 text-sm text-gray-800 focus:border-gray-500 focus:outline-none"
							>
								<option v-for="opt in syncIntervalOptions" :key="opt.value" :value="opt.value">
									{{ opt.label }}
								</option>
							</select>
						</div>

						<div v-if="!sheetPreviewReady && !csvData.loading" class="flex justify-end">
							<Button
								variant="solid"
								:label="__('Preview Sheet')"
								:disabled="!sheetUrl.trim()"
								@click="previewGoogleSheet"
							/>
						</div>
					</template>

					<!-- Processing spinner -->
					<div
						v-if="csvData.loading"
						class="flex flex-col items-center gap-3 rounded border border-dashed border-gray-300 p-10 text-gray-500"
					>
						<div class="h-5 w-5 animate-spin rounded-full border-2 border-gray-300 border-t-blue-500"></div>
						<p class="text-sm">
							{{ uploadMode === 'sheet' ? __('Reading Google Sheet…') : __('Reading file…') }}
						</p>
					</div>

					<!-- Preview -->
					<div v-else-if="showPreview" class="flex flex-col gap-3">
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

				<!-- Action buttons -->
				<div
					v-if="showPreview"
					class="mt-3 flex flex-shrink-0 items-center justify-end gap-2 border-t pt-3"
				>
					<Button
						:label="uploadMode === 'sheet' ? __('Reset') : __('Reset File')"
						@click="uploadMode === 'sheet' ? resetSheet() : resetFile()"
					/>
					<Button
						variant="solid"
						:label="uploadMode === 'sheet' ? __('Link & Sync') : __('Import')"
						:loading="importing"
						:disabled="uploadMode === 'sheet' ? sheetImportDisabled : fileImportDisabled"
						@click="uploadMode === 'sheet' ? linkGoogleSheet() : importCSVData()"
					/>
				</div>
			</div>
		</template>
	</Dialog>
</template>
