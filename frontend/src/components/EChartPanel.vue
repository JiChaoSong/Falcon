<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { CanvasRenderer } from 'echarts/renderers';
import { LineChart, type LineSeriesOption } from 'echarts/charts';
import {
  GridComponent,
  LegendComponent,
  TooltipComponent,
  type GridComponentOption,
  type LegendComponentOption,
  type TooltipComponentOption,
} from 'echarts/components';
import {
  init,
  use,
  type ComposeOption,
  type ECharts,
} from 'echarts/core';

use([
  CanvasRenderer,
  LineChart,
  GridComponent,
  LegendComponent,
  TooltipComponent,
]);

interface SeriesConfig {
  name: string;
  data: number[];
  color: string;
  areaColor?: string;
  dashed?: boolean;
  yAxisIndex?: number;
}

const props = defineProps<{
  title: string;
  subtitle?: string;
  labels: string[];
  series: SeriesConfig[];
  legend?: string[];
}>();

const chartRef = ref<HTMLDivElement | null>(null);
type ECOption = ComposeOption<
  LineSeriesOption |
  GridComponentOption |
  LegendComponentOption |
  TooltipComponentOption
>;

let chartInstance: ECharts | null = null;

const option = computed<ECOption>(() => {
  const hasSecondaryAxis = props.series.some((item) => item.yAxisIndex === 1);

  return {
    animation: false,
    grid: {
      left: 16,
      right: hasSecondaryAxis ? 26 : 16,
      top: 20,
      bottom: 24,
      containLabel: true
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(15, 23, 42, 0.92)',
      borderWidth: 0,
      textStyle: {
        color: '#f8fafc'
      }
    },
    legend: {
      show: false
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: props.labels,
      axisLine: {
        lineStyle: {
          color: '#cbd5e1'
        }
      },
      axisLabel: {
        color: '#64748b',
        fontSize: 11
      },
      splitLine: {
        show: false
      }
    },
    yAxis: [
      {
        type: 'value',
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: {
          lineStyle: {
            color: 'rgba(148, 163, 184, 0.18)'
          }
        },
        axisLabel: {
          color: '#64748b',
          fontSize: 11
        }
      },
      {
        type: 'value',
        show: hasSecondaryAxis,
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: {
          color: '#94a3b8',
          fontSize: 11
        }
      }
    ],
    series: props.series.map((item) => ({
      name: item.name,
      type: 'line',
      smooth: true,
      symbol: 'none',
      showSymbol: false,
      yAxisIndex: item.yAxisIndex ?? 0,
      data: item.data,
      lineStyle: {
        width: 3,
        color: item.color,
        type: item.dashed ? 'dashed' : 'solid'
      },
      itemStyle: {
        color: item.color
      },
      areaStyle: item.areaColor ? {
        color: item.areaColor
      } : undefined
    }))
  };
});

const renderChart = async () => {
  await nextTick();

  if (!chartRef.value) {
    return;
  }

  if (!chartInstance) {
    chartInstance = init(chartRef.value);
  }

  chartInstance.setOption(option.value, true);
  chartInstance.resize();
};

const handleResize = () => {
  chartInstance?.resize();
};

watch(option, () => {
  renderChart();
}, { deep: true });

onMounted(() => {
  renderChart();
  window.addEventListener('resize', handleResize);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize);
  chartInstance?.dispose();
  chartInstance = null;
});
</script>

<template>
  <div class="chart-card">
    <div class="chart-head">
      <div>
        <div class="chart-title">{{ title }}</div>
        <div class="chart-subtitle">{{ subtitle }}</div>
      </div>
      <div class="chart-legend" v-if="legend?.length">
        <span class="legend-item" v-for="(name, index) in legend" :key="name">
          <i class="legend-dot" :style="{ backgroundColor: series[index]?.color || '#2563eb' }"></i>
          <span>{{ name }}</span>
        </span>
      </div>
    </div>

    <div ref="chartRef" class="chart-canvas"></div>
  </div>
</template>

<style scoped>
.chart-card {
  padding: 18px;
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 18px;
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.06);
}

.chart-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.chart-title {
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
}

.chart-subtitle {
  margin-top: 4px;
  color: #64748b;
  font-size: 13px;
}

.chart-legend {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #64748b;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
}

.chart-canvas {
  height: 260px;
  margin-top: 14px;
}

@media (max-width: 768px) {
  .chart-head {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
