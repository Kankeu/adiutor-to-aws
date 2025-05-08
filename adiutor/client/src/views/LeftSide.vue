<script setup lang="ts">
import { storeToRefs } from 'pinia';
import { getCurrentInstance } from 'vue'
import { Search, InfoFilled, HomeFilled } from '@element-plus/icons-vue'
import SettingDialog from "@/components/setting/SettingDialog.vue";
import AddWebPage from '@/components/web_search/AddWebPage.vue';
import { useWebSearch } from '@/stores/web_search';
import { useChat } from '@/stores/chat';
import WebPages from '@/components/web_search/WebPages.vue';

const chat = useChat()
const webSearch = useWebSearch()
const { webPages } = storeToRefs(webSearch)

const vm = getCurrentInstance()
const proxy = vm?.proxy as any


const features = [
  {
    "icon": HomeFilled,
    "id": null,
    "name": "Welcome",
  },
  {
    "icon": Search,
    "id": "web_search",
    "name": "Web Search",
    "description": "Perform web searches using RAG."
  },
]

function navigate(f) {
  if (f.id) {
    proxy.pushQuery({ feature: f.id })
  } else {
    proxy.popQuery('feature')
  }
}
</script>

<template>
  <el-card :style="{ padding: 0, margin: 0, height: innerHeight + 'px' }" shadow="never" class="doc-list">
    <template #header>
      <el-space style="justify-content: space-between;width: 100%;">
        <div class="card-header">
          <span>Menu</span>
        </div>
      </el-space>
    </template>
    <el-scrollbar :style="{ height: (innerHeight - 70) + 'px' }">
      <el-scrollbar
        :style="{ height: .8 * (innerHeight - 70) + 'px', paddingTop: '1em', paddingBottom: '1em', paddingLeft: '.5em', paddingRight: '.5em' }">
        <el-card shadow="hover" @click="navigate(f)" v-for="f in features" :key="f"
          :style="{ cursor: 'pointer', marginBottom: '.75em', border: '1px solid var(--el-border-color)', opacity: !!$route.query.feature ? .6 : 1, ...(f.id == $route.query.feature ? { opacity: 1, borderColor: 'blue', borderLeftWidth: '3px' } : {}) }">
          <el-space style="justify-content: space-between;width: 100%">
            <div style="font-size: 16px;width: 100%;text-align: left">
              <template>
                <el-icon>
                  <component :is="f.icon"></component>
                </el-icon>
              </template>
              {{ f.name }}
            </div>
            <el-tooltip v-if="f.description" :content="f.description" placement="top">
              <el-icon size="20">
                <InfoFilled></InfoFilled>
              </el-icon>
            </el-tooltip>
          </el-space>
        </el-card>
        <AddWebPage></AddWebPage>
        <el-divider></el-divider>
        <WebPages></WebPages>
        <el-card v-if="false" v-for="domain in new Set(webPages.map(wp => wp.domain))" :key="domain" shadow="hover"
          :style="{ cursor: 'pointer', marginBottom: '.75em', border: '1px solid var(--el-border-color)', opacity: !!$route.query.web_search ? .6 : 1, ...($route.query.web_search ? { opacity: 1, borderColor: 'blue', borderLeftWidth: '3px' } : {}) }">
          <div slot="header" class="clearfix" style="font-size: 16px;width: 100%;text-align: left">
            <span>{{ toEllipsis(domain, 30) }}</span>
            <el-button style="float: right; padding: 3px 0" type="text">Operation button</el-button>
          </div>
          <div v-for="webPage in webPages.filter(wp => wp.domain == domain)" :key="webPage.id" class="text item"
            @click.prevent.stop="chat.updateWebSearch({ current: webPage.url, sources: [] })">
            {{ toEllipsis(webPage.url, 30) }}
          </div>
        </el-card>
      </el-scrollbar>
      <el-divider></el-divider>
      <el-image style="padding-left: .5em;padding-right: .5em;" src="/images/defaults/rptu-h.png"></el-image>
      <el-row style="padding: .5em;">
        <el-space style="justify-content: space-between;width: 100%">
          Made by KFIN
          <SettingDialog></SettingDialog>
        </el-space>
      </el-row>
    </el-scrollbar>
  </el-card>

</template>