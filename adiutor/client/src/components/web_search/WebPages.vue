<template>
    <div class="web_pages">
        <el-input v-model.trim="filterText" style="margin-bottom: 15px;" placeholder="Search web pages"
            :prefix-icon="Search" />
        <el-tree ref="treeRef" :data="data" node-key="id" default-expand-all :props="defaultProps"
            :filter-node-method="filterNode" :class="{'filtered-tree':filterText.length>0}"
            :expand-on-click-node="false" >
            <template #default="{ node, data }">
                <div style="display: flex;justify-content: space-between;width: 100%;padding-top: 40px;">
                    <el-link type="primary"
                        @click="chat.updateWebSearch({ current: data.id, sources: [{ url: data.id, title: data.label }] })">{{
                        toEllipsis(data.label||'',20) }}</el-link>
                    <div>
                        <el-button type="danger" :icon="Delete" :loading="removings.includes(data.id)" size="small"
                            circle @click="remove(data)">
                        </el-button>
                    </div>
                </div>
            </template>
        </el-tree>
    </div>
</template>

<script lang="ts" setup>
import { computed, ref, watch } from 'vue'
import { storeToRefs } from 'pinia';
import { Search, Delete } from '@element-plus/icons-vue'
import type { TreeInstance } from 'element-plus'
import chatRepository from "@/repositories/ChatRepository"
import { useWebSearch } from '@/stores/web_search';
import { useChat } from '@/stores/chat';

interface Tree {
    [key: string]: any
}

chatRepository.getWebPages()
const chat = useChat()
const webSearch = useWebSearch()
const { webPages } = storeToRefs(webSearch)

const filterText = ref('')
const treeRef = ref<TreeInstance>()

const defaultProps = {
    children: 'children',
    label: 'label',
}

watch(filterText, (val) => {
    treeRef.value!.filter(val)
})

const filterNode = (value: string, data: Tree) => {
    if (!value) return true
    value = value.toLowerCase()
    console.log("filter", data.children)
    return data.label.toLowerCase().includes(value) || data.children && data.children.some((n: Tree) => n.label.toLowerCase().includes(value))
}


const data = computed<Tree[]>(() => {
    const domains = Array.from(new Set(webPages.value.map(wp => wp.domain)))
    return domains.map(domain => ({
        id: "https://" + domain,
        label: domain,
        children: webPages.value.filter(wp => wp.domain == domain).map(wp => ({
            id: wp.url,
            label: wp.title
        }))
    }))
})

const removings = ref<string[]>([])
async function remove(node: any) {
    removings.value.push(node.id)
    console.log(node)
    try {
        await chatRepository.deleteWebPages(node.children ? { domains: [node.id.slice(8)] } : { urls: [node.id] })
    } catch (e) {
        console.error(e)
    }
    removings.value.splice(removings.value.indexOf(node.id), 1)
}
</script>

<style lang="css">
.web_pages .filtered-tree .el-tree-node {
    min-height: 50px !important;
}
.web_pages .el-tree-node {
    margin-top: 5px;
}
</style>