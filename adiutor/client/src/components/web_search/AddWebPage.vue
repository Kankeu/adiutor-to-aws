<template>
    <el-card v-if="webSite?.url&&!inputing" shadow="hover" @click="navigate(f)"
          :style="{ cursor: 'pointer', marginBottom: '.75em', border: '1px solid var(--el-border-color)', opacity: !!$route.query.web_search ? .6 : 1, ...($route.query.web_search ? { opacity: 1, borderColor: 'blue', borderLeftWidth: '3px' } : {}) }">
        <el-space style="justify-content: space-between;width: 100%">
        <div style="font-size: 16px;width: 100%;text-align: left">
            <template>
            <el-icon>
                <Edit></Edit>
            </el-icon>
            </template>
            {{ toEllipsis(webSite.url,30) }}
        </div>
        <el-button @click.stop="inputing=true" :icon="Edit" circle></el-button>
        </el-space>
    </el-card>
    <el-button @click="inputing=true" type="primary" style="width: 100%;" v-else-if="!inputing">Add a web page &nbsp;
        <el-icon size="20">
            <CirclePlus></CirclePlus>
        </el-icon>
    </el-button>
    <el-input v-model.trim="form.url" placeholder="https://example.com" v-else>
        <template #prepend>
            <el-button @click="inputing=false" type="primary" :icon="Close" circle/>
        </template>
        <template #append>
            <el-button @click="index" :loading="loading" type="primary">Index</el-button>
        </template>
    </el-input>
</template>

<script setup lang="ts">
import {ref} from 'vue'
import {storeToRefs} from "pinia"
import { Close, CirclePlus,Edit } from '@element-plus/icons-vue'
import chatRepository from "@/repositories/ChatRepository"
import {useWebSearch} from "@/stores/web_search"

const webSearch = useWebSearch()
const {webSite} = storeToRefs(webSearch)
const inputing = ref(false)
const loading = ref(false)
const form = ref({url: ''})
async function index(){
    loading.value = true
    await chatRepository.index(form.value)
    loading.value = false
}
function navigate(){

}
</script>