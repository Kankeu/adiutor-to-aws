<template>
    <el-button @click="inputing=true" type="primary" style="width: 100%;" v-if="!inputing">Add a web page &nbsp;
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
import { Close, CirclePlus,Edit } from '@element-plus/icons-vue'
import chatRepository from "@/repositories/ChatRepository"

const inputing = ref(false)
const loading = ref(false)
const form = ref({url: ''})
async function index(){
    loading.value = true
    await chatRepository.index(form.value)
    loading.value = false
}
</script>