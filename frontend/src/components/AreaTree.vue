<template>
  <div class="area-tree card-border-xl">
    <div class="area-tree__header">
      <span class="area-tree__title">区域架构</span>
      <n-button
        type="primary"
        size="small"
        @click="showAddAreaModal = true"
      >
        <template #icon>
          <n-icon><AddOutline /></n-icon>
        </template>
        新增
      </n-button>
    </div>
    <div class="area-tree__body">
      <n-tree
        block-line
        show-line
        :data="treeData"
        :expanded-keys="expandedKeys"
        :selected-keys="selectedKeys"
        :render-label="renderLabel"
        :render-suffix="renderSuffix"
        :node-props="nodeProps"
        :theme-overrides="treeThemeOverrides"
        @update:expanded-keys="handleExpandedKeysUpdate"
      />
    </div>

    <!-- Add Area Modal -->
    <AddAreaModal
      v-model:show="showAddAreaModal"
      :tree-data="treeData"
      @save="handleAddArea"
    />

    <!-- Edit Area Modal -->
    <AddAreaModal
      v-model:show="showEditAreaModal"
      :tree-data="treeData"
      :edit-data="editingArea"
      @save="handleEditArea"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, h, onMounted } from 'vue'
import { NTree, NIcon, NButton, NPopconfirm, useMessage } from 'naive-ui'
import type { TreeOption } from 'naive-ui'
import { AddOutline, CreateOutline, TrashOutline } from '@vicons/ionicons5'
import { useAppStore } from '@/stores/app'
import AddAreaModal from './AddAreaModal.vue'
import { getAreaTree, createArea, updateArea, deleteArea, type AreaTreeNode } from '@/api/area'

export interface AreaNode {
  key: string
  label: string
  parentKey?: string
  children?: AreaNode[]
}

const appStore = useAppStore()
const message = useMessage()

const emit = defineEmits<{
  (e: 'select', key: string, label: string): void
  (e: 'update', treeData: TreeOption[]): void
}>()

const props = defineProps<{
  selectedKey: string
}>()

const selectedKeys = computed(() => [props.selectedKey])
const expandedKeys = ref<string[]>([])
const hoveredKey = ref<string | null>(null)
const loading = ref(false)

// Modal states
const showAddAreaModal = ref(false)
const showEditAreaModal = ref(false)
const editingArea = ref<AreaNode | null>(null)

// Tree data - reactive
const treeData = ref<TreeOption[]>([])

// 将后端区域数据转换为树形结构
function convertToTreeOption(node: AreaTreeNode): TreeOption {
  const option: TreeOption = {
    key: node.id,
    label: node.name
  }
  if (node.children && node.children.length > 0) {
    option.children = node.children.map(convertToTreeOption)
  }
  return option
}

// 加载区域树数据
async function loadAreaTree() {
  loading.value = true
  try {
    const response = await getAreaTree()
    if (response.data.data) {
      treeData.value = response.data.data.map(convertToTreeOption)
      // 默认展开第一层
      expandedKeys.value = treeData.value.map(n => n.key as string)
      emit('update', treeData.value)
    }
  } catch (error: any) {
    console.error('加载区域树失败:', error)
    // 如果 API 失败，使用默认数据
    treeData.value = [
      {
        label: '默认园区',
        key: 'default-area',
        children: []
      }
    ]
  } finally {
    loading.value = false
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadAreaTree()
})

function handleExpandedKeysUpdate(keys: string[]) {
  expandedKeys.value = keys
}

// Render label with hover effect
function renderLabel({ option }: { option: TreeOption }) {
  return h('span', {
    class: 'area-tree__node-label'
  }, option.label as string)
}

// Render suffix with edit/delete buttons
function renderSuffix({ option }: { option: TreeOption }) {
  if (hoveredKey.value !== option.key) return null
  
  return h('div', {
    class: 'area-tree__node-actions',
    onClick: (e: Event) => e.stopPropagation()
  }, [
    h(NButton, {
      text: true,
      size: 'tiny',
      class: 'area-tree__action-btn',
      onClick: (e: Event) => {
        e.stopPropagation()
        handleEditClick(option)
      }
    }, {
      icon: () => h(NIcon, { size: 14 }, { default: () => h(CreateOutline) })
    }),
    h(NPopconfirm, {
      onPositiveClick: () => handleDeleteArea(option.key as string)
    }, {
      trigger: () => h(NButton, {
        text: true,
        size: 'tiny',
        class: 'area-tree__action-btn area-tree__action-btn--danger',
        onClick: (e: Event) => e.stopPropagation()
      }, {
        icon: () => h(NIcon, { size: 14 }, { default: () => h(TrashOutline) })
      }),
      default: () => '确定删除此区域吗？'
    })
  ])
}

function nodeProps({ option }: { option: TreeOption }) {
  return {
    onClick() {
      emit('select', option.key as string, option.label as string)
    },
    onMouseenter() {
      hoveredKey.value = option.key as string
    },
    onMouseleave() {
      hoveredKey.value = null
    }
  }
}

function handleEditClick(option: TreeOption) {
  editingArea.value = {
    key: option.key as string,
    label: option.label as string,
    parentKey: findParentKey(option.key as string)
  }
  showEditAreaModal.value = true
}

function findParentKey(key: string, nodes: TreeOption[] = treeData.value, parent?: string): string | undefined {
  for (const node of nodes) {
    if (node.key === key) return parent
    if (node.children) {
      const found = findParentKey(key, node.children, node.key as string)
      if (found !== undefined) return found
    }
  }
  return undefined
}

async function handleAddArea(data: { name: string; parentKey: string; description: string }) {
  try {
    const response = await createArea({
      name: data.name,
      parent_id: data.parentKey || undefined,
      description: data.description || undefined
    })
    
    if (response.data.data) {
      message.success('区域创建成功')
      // 重新加载区域树
      await loadAreaTree()
      // 展开父节点
      if (data.parentKey && !expandedKeys.value.includes(data.parentKey)) {
        expandedKeys.value.push(data.parentKey)
      }
    }
  } catch (error: any) {
    message.error(error.message || '创建区域失败')
  }
}

function addToParent(nodes: TreeOption[], parentKey: string, newNode: TreeOption) {
  for (const node of nodes) {
    if (node.key === parentKey) {
      if (!node.children) node.children = []
      node.children.push(newNode)
      return true
    }
    if (node.children && addToParent(node.children, parentKey, newNode)) {
      return true
    }
  }
  return false
}

async function handleEditArea(data: { name: string; parentKey: string; description: string }) {
  if (!editingArea.value) return
  
  try {
    await updateArea(editingArea.value.key, {
      name: data.name,
      description: data.description || undefined
    })
    
    message.success('区域更新成功')
    editingArea.value = null
    // 重新加载区域树
    await loadAreaTree()
  } catch (error: any) {
    message.error(error.message || '更新区域失败')
  }
}

async function handleDeleteArea(key: string) {
  try {
    await deleteArea(key)
    message.success('区域删除成功')
    // 重新加载区域树
    await loadAreaTree()
  } catch (error: any) {
    message.error(error.message || '删除区域失败')
  }
}

const treeThemeOverrides = computed(() => {
  const dark = appStore.isDarkMode
  return {
    nodeTextColor: dark ? '#c0c0c8' : '#555',
    nodeColorHover: dark ? 'rgba(255,255,255,0.08)' : 'rgba(67, 24, 255, 0.06)',
    nodeColorActive: dark ? 'rgba(67, 24, 255, 0.2)' : 'rgba(67, 24, 255, 0.1)',
    lineColor: dark ? '#3a3a40' : '#e5e7eb'
  }
})

// Expose tree data for parent components
defineExpose({
  treeData
})
</script>

<style scoped>
.area-tree {
  width: 260px;
  min-width: 260px;
  background: var(--bg-card);
  display: flex;
  flex-direction: column;
  height: fit-content;
  min-height: 300px;
  max-height: calc(100vh - 130px);
  position: sticky;
  top: 0;
  align-self: flex-start;
  transition: box-shadow var(--transition-normal);
}

.area-tree:hover {
  box-shadow: var(--shadow-md);
}

.area-tree__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--border-color);
}

.area-tree__title {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
}

.area-tree__body {
  padding: var(--spacing-sm);
  overflow-y: auto;
  flex: 1;
}

/* Node styles */
:deep(.n-tree-node) {
  border-radius: var(--radius-md);
  transition: all var(--transition-normal);
}

:deep(.n-tree-node:hover) {
  background: var(--bg-hover);
}

:deep(.n-tree-node-content) {
  padding: var(--spacing-xs) var(--spacing-sm);
}

:deep(.n-tree-node--selected) {
  background: rgba(67, 24, 255, 0.1) !important;
}

:deep(.n-tree-node--selected .n-tree-node-content__text) {
  color: var(--primary-color);
  font-weight: var(--font-weight-medium);
}

.area-tree__node-label {
  font-size: var(--font-size-base);
}

.area-tree__node-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  margin-left: var(--spacing-sm);
}

.area-tree__action-btn {
  opacity: 0.6;
  transition: opacity var(--transition-fast), color var(--transition-fast);
}

.area-tree__action-btn:hover {
  opacity: 1;
}

.area-tree__action-btn--danger:hover {
  color: var(--error-color) !important;
}

/* Tree line styles */
:deep(.n-tree .n-tree-node-indent) {
  width: 16px;
}

:deep(.n-tree-node-switcher) {
  width: 20px;
  height: 20px;
}
</style>
