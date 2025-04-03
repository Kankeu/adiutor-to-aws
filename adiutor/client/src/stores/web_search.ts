import {defineStore} from 'pinia'
import {nextTick, reactive} from "vue";

export const useWebSearch = defineStore('webSearch', {
    state: () => ({
        edges: [],
        webSite: null
    }),
    actions: {
        addWebSite(webSite){
            this.webSite = webSite
        },
        addEdge(edge) {
            const i = this.edges.findIndex(t => t==edge)
            if (i >= 0) {
                this.edges.splice(i, 1)
                nextTick(() => {
                    this.edges.splice(i, 0, edge)
                })
            } else {
                this.edges.push(edge)
            }
        },
        clearTasks() {
            this.edges = []
        }
    },
})