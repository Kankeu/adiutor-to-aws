import {defineStore} from 'pinia'
import {nextTick, reactive} from "vue";
import type {Message, OnMessage, WebSearch, Settings} from '@/types/types'



type StateType = {
    web_search: WebSearch
    messages:Message[]
    _onMessage: OnMessage | null
}

export const useChat = defineStore('chat', {
    state: () => (<StateType>{
        web_search: {current: null,sources:[]},
        _onMessage: null,
        messages: [],
    }),
    getters: {
        settings(state) {
            return () => {
                try {
                    return JSON.parse(localStorage.getItem('settings')??"{}")
                } catch (e) {
                    return null
                }
            }
        },
    },
    actions: {
        addMessage(message:Message) {
            const i = this.messages.findIndex(m => m.id == message.id)
            if (i >= 0) {
                this.messages.splice(i, 1)
                nextTick(() => {
                    this.messages.splice(i, 0, message)
                    nextTick(() => {
                        if (this._onMessage) this._onMessage(message)
                    })
                })
            } else {
                this.messages.push(message)
                nextTick(() => {
                    if (this._onMessage) this._onMessage(message)
                })
            }
        },
        findMessage(id:number) {
            const i = this.messages.findIndex(m => m.id == id)
            return i >= 0 ? this.messages[i] : null
        },
        onMessage(onMessage:OnMessage) {
            this._onMessage = onMessage
        },
        removeMessage(id:number) {
            const i = this.messages.findIndex(m => m.id == id)
            if (i >= 0) this.messages.splice(i, 1)
        },
        clearMessages() {
            this.messages = []
        },
        setSettings(settings: Settings) {
            localStorage.setItem('settings', JSON.stringify(settings));
        },
        updateWebSearch(web_search: WebSearch){
            this.web_search = {...this.web_search,...web_search}
        }
    },
})