<script setup lang="ts">
import {watch,ref} from 'vue'

import RightSide from "@/views/RightSide.vue";
import LeftSide from "@/views/LeftSide.vue";
import Welcome from "@/components/welcome/Welcome.vue";
import WebSearch from "@/components/web_search/WebSearch.vue";


</script>

<template>
  <el-row style="background: #f0f8ff">
    <el-col :span="4">
      <LeftSide></LeftSide>
    </el-col>
    <el-col :span="14" class="m-main">
      <el-scrollbar style="height: 100vh;justify-content: center;align-items:center;display: flex">
        <Welcome  v-if="!$route.query.feature"></Welcome>
        <WebSearch v-else></WebSearch>
      </el-scrollbar>
    </el-col>
    <el-col :span="6">
      <RightSide></RightSide>
    </el-col>
  </el-row>
</template>


<style>
.card-header * {
  font-size: 1.25em;
  font-weight: bold;
}

.doc-list .el-card__body {
  padding: .25em !important;
  margin: 0 !important;
}
.m-main .el-scrollbar__wrap{
  width: 100%;
}
.m-main .el-scrollbar__view{
  height: 100%;
}
</style>