<template>
    <el-button @click="inputing = true" type="primary" style="width: 100%;" v-if="!inputing">Add a web page &nbsp;
        <el-icon size="20">
            <CirclePlus></CirclePlus>
        </el-icon>
    </el-button>
    <el-input v-model.trim="form.url" placeholder="https://example.com" v-else>
        <template #prepend>
            <el-button @click="inputing = false" type="primary" :icon="Close" circle />
        </template>
        <template #append>
            <el-popconfirm confirm-button-text="Yes" cancel-button-text="No" :icon="InfoFilled" icon-color="info"
                title="Would you like to use a dynamic page crawler (slower and accurate)?" @confirm="index(false)" @cancel="index(true)" placement="top-start">
                <template #reference>
                    <el-button :loading="loading" type="primary">Index</el-button>
                </template> @click="index"
            </el-popconfirm>
        </template>
    </el-input>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Close, CirclePlus, InfoFilled } from '@element-plus/icons-vue'
import chatRepository from "@/repositories/ChatRepository"

const inputing = ref(false)
const loading = ref(false)
const form = ref({ url: '',fast:true })
async function index(fast:boolean) {
    if(form.value.url.length==0) return
    loading.value = true
    form.value.fast = fast
    await chatRepository.index(form.value)
    loading.value = false
}
</script>