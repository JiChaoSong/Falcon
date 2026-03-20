<!-- WarningButton.vue -->
<template>
  <a-button
      v-bind="$attrs"
      :class="['warning-button', sizeClass]"
      @click="handleClick"
  >
    <slot />
  </a-button>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps({
  size: {
    type: String,
    default: 'middle',
    validator: (value: string) => ['small', 'middle', 'large'].includes(value)
  },
  loading: {
    type: Boolean,
    default: false
  },
  disabled: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['click']);

const sizeClass = computed(() => {
  return `warning-button-${props.size}`;
});

const handleClick = (e: Event) => {
  if (!props.disabled && !props.loading) {
    emit('click', e);
  }
};
</script>

<style scoped>
.warning-button {
  background: linear-gradient(135deg, #faad14 0%, #ffc53d 100%);
  border-color: #faad14;
  color: #fff;
  font-weight: 500;
  transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
}

.warning-button:hover {
  background: linear-gradient(135deg, #ffc53d 0%, #ffd666 100%);
  border-color: #ffc53d;
  color: #fff;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(250, 173, 20, 0.3);
}

.warning-button:focus {
  background: linear-gradient(135deg, #d48806 0%, #faad14 100%);
  border-color: #d48806;
  color: #fff;
  box-shadow: 0 0 0 2px rgba(250, 173, 20, 0.2);
}

.warning-button:active {
  transform: translateY(0);
}

.warning-button.warning-button-small {
  height: 24px;
  padding: 0 7px;
  font-size: 12px;
}

.warning-button.warning-button-middle {
  height: 32px;
  padding: 4px 15px;
  font-size: 14px;
}

.warning-button.warning-button-large {
  height: 40px;
  padding: 6.4px 15px;
  font-size: 16px;
}

.warning-button[disabled] {
  background: #f5f5f5;
  border-color: #d9d9d9;
  color: rgba(0, 0, 0, 0.25);
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.warning-button[disabled]:hover {
  background: #f5f5f5;
  border-color: #d9d9d9;
  transform: none;
  box-shadow: none;
}
</style>