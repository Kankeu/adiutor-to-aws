import { ElNotification } from 'element-plus'
import {useWebSearch} from "@/stores/web_search";
import {useChat} from "@/stores/chat";
import {speak} from "@/mixins/Global";
import {default as http,HttpExecutor} from "@/http/http"
import StreamingJsonParser from "@/utils/StreamingJsonParser"

class ChatRepository{
    stopped = false
    executor?: HttpExecutor

    stop(){
        this.stopped = true
        this.executor?.abort()
    }

    async query(data:any,speech:boolean){
        this.stopped = false
        const chat = useChat()
        const settings = chat.settings()
        chat.addMessage({...data,id:Date.now()})
        const loading_msg = {id:Date.now()+1,loading:true}
        chat.addMessage(loading_msg)
        const parser = new StreamingJsonParser()
        try{
            this.executor = http.post("api/query", {query:data.text,system_prompt:settings.system_prompt})
            const res = await this.executor.execute()
            const message = {role:"assistant",text:"",id:Date.now()}

            const reader = res?.body?.getReader() as ReadableStreamDefaultReader;

            const decoder = new TextDecoder();
            let done = false;
            let metaData: any = null;
            let metaRawData = ""
            while (!done && !this.stopped) {
                try{
                    const { value, done: doneReading } = await reader.read();
                    done = doneReading;
                    let chunkValueStr = decoder.decode(value)
                    try{
                        let action = null
                        for (const chunkValue of parser.parse(chunkValueStr?.trim())){
                            [metaRawData,metaData,action] = this._processChunkValue(chat,metaRawData,metaData,loading_msg,message,chunkValue,speech)
                            if (action=="continue")
                                continue
                            if (action=="break")
                                break
                        }
                    }catch (e) {
                        console.error(e,chunkValueStr)
                    }
                }catch (e) {
                    console.error(e)
                    break
                }
            }
            reader?.cancel()
        }catch (e){
            console.error(e)
            chat.removeMessage(data.id)
            ElNotification({
                title: 'Oops something went wrong!!!',
                message: String(e),
                type: 'error',
                duration:9000
            })
            if(speech) speak('Oops something went wrong!!!')
        }
        chat.removeMessage(loading_msg.id)

    }

    _processChunkValue(chat,metaRawData,metaData,loading_msg,message,chunkValue,speech){
        console.log(chunkValue)
        if (chunkValue.status == "done")
            return [metaRawData,metaData,"done"]
        if (chunkValue.status=="error"){
            ElNotification({
                title: 'Error',
                message: chunkValue.payload.message,
                type: 'error',
                duration: 9000
            })
            if(speech) speak(chunkValue.payload.message)
            message.text = "Please try again!"
            chat.addMessage({...message,type:"error"})
        }
        metaRawData += chunkValue

        if (chunkValue.type == "metadata"){
            const sources = chunkValue.payload.sources
            chat.updateWebSearch({current:sources.length ? sources[0].url : null, sources:sources})
            return [metaRawData,chunkValue.payload,null]
        }
        /*
        if (chunkValue.payload?.sources!=null) {
            metaData = chunkValue.payload
        } else {*/
        if(metaData && chunkValue.type=="web_search"){
            chat.removeMessage(loading_msg.id)
            //console.log("metadata",chunkValue,metaData)
            const sources = metaData.sources
            let reply = message.text + chunkValue.payload.response
            for (let i=0; i<sources.length; i++){
                const key = "WSD-#"+(i+1)
                if (reply.includes(key))
                    reply = reply.replaceAll(key,"["+(i+1)+"]("+sources[i].url+")")
            }
            message.speech = speech
            message.text = reply
            console.log(message)
            chat.addMessage({...message,...metaData})
        }
        //}
        return [metaRawData,metaData,null]
    }

    async index(form){
        try{
            const executor = http.post("api/index",form)
            const res = await executor.execute()
            const payload = await res.json()
            const webSearch = useWebSearch()
            webSearch.addWebSite(payload)
        }catch (e){
            console.error(e)
            ElNotification({
                title: 'Oops something went wrong!!!',
                message: String(e),
                type: 'error',
                duration: 9000
            })
        }
    }
}

export default new ChatRepository()