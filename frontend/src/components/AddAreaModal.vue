<template>
  <n-modal
    v-model:show="showModal"
    preset="card"
    :bordered="false"
    :closable="true"
    class="add-area-modal"
    :title="isEdit ? '编辑区域' : '添加区域'"
    :header-style="headerStyle"
  >
    <template #header>
      <div class="add-area-modal__header">
        <span class="add-area-modal__indicator"></span>
        <span class="add-area-modal__title">{{ isEdit ? '编辑区域' : '添加区域' }}</span>
      </div>
    </template>

    <n-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-placement="top"
      require-mark-placement="right-hanging"
    >
      <n-form-item label="区域名称" path="name">
        <n-input
          v-model:value="formData.name"
          placeholder="请输入区域名称"
        />
      </n-form-item>

      <n-form-item label="上级区域" path="parentKey">
        <n-tree-select
          v-model:value="formData.parentKey"
          :options="treeOptions"
          placeholder="请选择上级区域"
          clearable
          :default-expand-all="true"
        />
      </n-form-item>

      <n-form-item label="区域描述" path="description">
        <n-input
          v-model:value="formData.description"
          type="textarea"
          placeholder="请输入描述，例如：该区域包含3个摄像头，主要负责外围安防监控..."
          :rows="3"
        />
      </n-form-item>

      <n-form-item>
        <n-checkbox v-model:checked="formData.enableMonitoring">
          立即激活区域监控权限
        </n-checkbox>
      </n-form-item>
    </n-form>

    <template #footer>
      <div class="add-area-modal__footer">
        <n-button @click="handleClose">取消</n-button>
        <n-button type="primary" @click="handleSubmit">确定</n-button>
      </div>
    </template>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import {
  NModal, NForm, NFormItem, NInput, NButton,
  NTreeSelect, NCheckbox
} from 'naive-ui'
import type { TreeOption, FormRules, FormInst } from 'naive-ui'

interface AreaNode {
  key: string
  label: string
  parentKey?: string
}

const props = defineProps<{
  show: boolean
  treeData: TreeOption[]
  editData?: AreaNode | null
}>()

const emit = defineEmits<{
  (e: 'update:show', value: boolean): void
  (e: 'save', data: { name: string; parentKey: string; description: string }): void
}>()

const showModal = computed({
  get: () => props.show,
  set: (val) => emit('update:show', val)
})

const isEdit = computed(() => !!props.editData)

const formRef = ref<FormInst | null>(null)
const formData = ref({
  name: '',
  parentKey: null as string | null,
  description: '',
  enableMonitoring: true
})

const formRules: FormRules = {
  name: [
    { required: true, message: '请输入区域名称', trigger: 'blur' }
  ]
}

// Convert tree data to tree select options
const treeOptions = computed(() => {
  const convert = (nodes: TreeOption[]): TreeOption[] => {
    return nodes.map(node => ({
      key: node.key,
      label: node.label,
      children: node.children ? convert(node.children) : undefined
    }))
  }
  return convert(props.treeData)
})

const headerStyle = {
  padding: 'var(--spacing-lg) var(--spacing-xl)',
  borderBottom: '1px solid var(--border-color)'
}

function handleClose() {
  emit('update:show', false)
  resetForm()
}

function handleSubmit() {
  formRef.value?.validate((errors) => {
    if (!errors) {
      emit('save', {
        name: formData.value.name,
        parentKey: formData.value.parentKey || '',
        description: formData.value.description
      })
      handleClose()
    }
  })
}

function resetForm() {
  formData.value = {
    name: '',
    parentKey: null,
    description: '',
    enableMonitoring: true
  }
}

// Watch for edit data changes
watch(() => props.show, (val) => {
  if (val && props.editData) {
    formData.value = {
      name: props.editData.label,
      parentKey: props.editData.parentKey || null,
      description: '',
      enableMonitoring: true
    }
  } else if (!val) {
    resetForm()
  }
})
</script>

<style scoped>
.add-area-modal {
  width: 480px;
  max-width: 90vw;
}

.add-area-modal__header {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.add-area-modal__indicator {
  width: 4px;
  height: 18px;
  background: var(--primary-color);
  border-radius: var(--radius-xs);
}

.add-area-modal__title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
}

.add-area-modal__footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-md);
}

:deep(.n-form-item-label) {
  font-weight: var(--font-weight-medium);
}
</style>
