<template>
  <div 
    class="stat-card" 
    :style="{ 
      '--accent-color': accentColor,
      '--icon-bg': iconBg
    }"
  >
    <div class="stat-card__glow"></div>
    <div class="stat-card__icon">
      <n-icon :size="24" :color="accentColor">
        <component :is="icon" />
      </n-icon>
    </div>
    <div class="stat-card__content">
      <span class="stat-card__label">{{ label }}</span>
      <span class="stat-card__value">
        <span class="stat-card__number">{{ value }}</span>
      </span>
    </div>
    <div class="stat-card__decorator"></div>
  </div>
</template>

<script setup lang="ts">
import { NIcon } from 'naive-ui'
import type { Component } from 'vue'

defineProps<{
  icon: Component
  iconBg: string
  accentColor: string
  label: string
  value: number | string
}>()
</script>

<style scoped>
.stat-card {
  position: relative;
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  padding: var(--spacing-lg) var(--spacing-xl);
  border: 1px solid var(--border-color);
  overflow: hidden;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Glow effect */
.stat-card__glow {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: radial-gradient(
    circle at 30% 50%,
    var(--icon-bg),
    transparent 60%
  );
  opacity: 0;
  transition: opacity 0.4s ease;
  pointer-events: none;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 
    0 12px 24px -8px rgba(0, 0, 0, 0.1),
    0 0 0 1px var(--accent-color);
  border-color: transparent;
}

.stat-card:hover .stat-card__glow {
  opacity: 0.6;
}

/* Icon */
.stat-card__icon {
  position: relative;
  width: 52px;
  height: 52px;
  border-radius: var(--radius-lg);
  background: var(--icon-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 1;
}

.stat-card:hover .stat-card__icon {
  transform: scale(1.1) rotate(-5deg);
  box-shadow: 0 8px 20px -4px var(--accent-color);
}

/* Content */
.stat-card__content {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  z-index: 1;
}

.stat-card__label {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
  font-weight: var(--font-weight-medium);
  transition: color 0.3s ease;
}

.stat-card:hover .stat-card__label {
  color: var(--text-secondary);
}

.stat-card__value {
  display: flex;
  align-items: baseline;
  gap: var(--spacing-xs);
}

.stat-card__number {
  font-size: 32px;
  font-weight: var(--font-weight-bold);
  color: var(--accent-color);
  line-height: 1;
  letter-spacing: -1px;
  transition: all 0.3s ease;
}

.stat-card:hover .stat-card__number {
  transform: scale(1.05);
}

/* Decorator */
.stat-card__decorator {
  position: absolute;
  top: -20px;
  right: -20px;
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: var(--icon-bg);
  opacity: 0.3;
  transition: all 0.4s ease;
  pointer-events: none;
}

.stat-card:hover .stat-card__decorator {
  transform: scale(1.5);
  opacity: 0.5;
}

/* Border accent line */
.stat-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: var(--accent-color);
  border-radius: 4px 0 0 4px;
  transform: scaleY(0);
  transition: transform 0.3s ease;
}

.stat-card:hover::before {
  transform: scaleY(1);
}

/* Active state */
.stat-card:active {
  transform: translateY(-2px);
}

/* Animation keyframes */
@keyframes countUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.stat-card__number {
  animation: countUp 0.5s ease-out forwards;
}
</style>
