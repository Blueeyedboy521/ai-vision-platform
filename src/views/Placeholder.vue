<template>
  <div style="padding: 40px; text-align: center; color: #999;">
    <n-empty description="功能开发中，敬请期待">
      <template #icon>
        <n-icon :size="48">
          <ConstructOutline />
        </n-icon>
      </template>
    </n-empty>
  </div>
</template>

<script setup lang="ts">
import { NEmpty, NIcon } from 'naive-ui'
import { ConstructOutline } from '@vicons/ionicons5'
</script>
