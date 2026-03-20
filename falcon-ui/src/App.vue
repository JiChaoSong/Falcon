<template>
  <a-config-provider :locale="locale">
    <router-view />
<!--    <BasicLayout />-->
  </a-config-provider>
</template>

<script setup lang="ts">
import zhCN from 'ant-design-vue/es/locale/zh_CN'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
// import HelloWorld from './components/HelloWorld.vue'
// import BasicLayout from "@/layout/BasicLayout.vue";

dayjs.locale('zh-cn')
const locale = zhCN
</script>