<template>
  <div class="area-tree">
    <div class="area-tree-header">
      <span class="area-tree-title">区域架构</span>
      <n-icon :size="18" color="#4318FF">
        <LocationOutline />
      </n-icon>
    </div>
    <div class="area-tree-body">
      <n-tree
        block-line
        :data="treeData"
        :default-expanded-keys="defaultExpandedKeys"
        :selected-keys="selectedKeys"
        :node-props="nodeProps"
        :theme-overrides="treeThemeOverrides"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { NTree, NIcon } from 'naive-ui'
import type { TreeOption } from 'naive-ui'
import { LocationOutline } from '@vicons/ionicons5'
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()

const emit = defineEmits<{
  (e: 'select', key: string, label: string): void
}>()

const props = defineProps<{
  selectedKey: string
}>()

const selectedKeys = computed(() => [props.selectedKey])

const treeData: TreeOption[] = [
  {
    label: '主园区',
    key: 'main-park',
    prefix: () => '🏢',
    children: [
      { label: 'A栋仓库', key: 'a-warehouse' },
      { label: 'B区办公楼', key: 'b-office' },
      { label: '安防中心', key: 'security-center' }
    ]
  },
  {
    label: '物料堆场',
    key: 'material-yard',
    prefix: () => '🏭',
    children: [
      { label: '堆场A区', key: 'yard-a' },
      { label: '堆场B区', key: 'yard-b' }
    ]
  },
  {
    label: '停车场',
    key: 'parking-lot',
    prefix: () => '🅿️',
    children: [
      { label: 'B栋 - 大厅入口', key: 'b-lobby' }
    ]
  }
]

const defaultExpandedKeys = ['main-park', 'material-yard', 'parking-lot']

function nodeProps({ option }: { option: TreeOption }) {
  return {
    onClick() {
      if (option.key && !option.children) {
        emit('select', option.key as string, option.label as string)
      }
    }
  }
}

const treeThemeOverrides = computed(() => {
  const dark = appStore.isDarkMode
  return {
    nodeTextColor: dark ? '#c0c0c8' : '#555',
    nodeColorHover: dark ? 'rgba(255,255,255,0.06)' : 'rgba(67, 24, 255, 0.04)',
    nodeColorActive: dark ? 'rgba(67, 24, 255, 0.15)' : 'rgba(67, 24, 255, 0.08)',
  }
})
</script>

<style scoped>
.area-tree {
  width: 240px;
  min-width: 240px;
  background: var(--bg-card);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  height: fit-content;
  max-height: calc(100vh - 200px);
  position: sticky;
  top: 0;
}

.area-tree-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 16px 12px;
  border-bottom: 1px solid var(--border-color);
}

.area-tree-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.area-tree-body {
  padding: 8px;
  overflow-y: auto;
  flex: 1;
}
</style>
