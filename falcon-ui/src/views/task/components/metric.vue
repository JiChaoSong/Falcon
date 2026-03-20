<script setup lang="ts">


import {message} from "ant-design-vue";

let controlSocket: WebSocket | null = null;

const state = ref(null)

const connectControlWebSocket = () => {
  try {
    controlSocket = new WebSocket('ws://localhost:8000/ws/metric')


    controlSocket.onopen = () => {
      // message.success('')

    }
    controlSocket.onmessage = (event: MessageEvent) => {
      try {
        state.value = JSON.parse(event.data)

      } catch (error) {
        console.log("解析WebSocket 消息失败")
      }
    }

    controlSocket.onerror = (error) => {
      console.error('WebSocket 错误:', error);
      message.error("连接错误");
    }

    controlSocket.onclose = () => {
      console.log('WebSocket 连接已关闭');
    }

  } catch (error) {
    console.error('创建 WebSocket 连接失败:', error);
    message.error("创建连接失败");
  }
}


</script>

<template>

</template>

<style scoped>

</style>