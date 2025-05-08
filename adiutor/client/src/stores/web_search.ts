import {defineStore} from 'pinia'

export const useWebSearch = defineStore('webSearch', {
    state: () => (<{webPages:any[]}>{
        webPages: []
    }),
    actions: {
        setWebPages(webPages: any[]){
            this.webPages = webPages
        },
    },
})