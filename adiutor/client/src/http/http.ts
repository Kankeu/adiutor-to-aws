export class Http{
    baseURL = import.meta.env.VITE_API_URL

    get(url:string): HttpExecutor{
        const controller = new AbortController();
        return new HttpExecutor(()=>fetch(this.fullURL(url), {method:'GET',signal:controller.signal}), controller)
    }
    post(url:string,data:any): HttpExecutor{
        const controller = new AbortController();
        return new HttpExecutor(()=>fetch(this.fullURL(url), {method:'POST',body:JSON.stringify(data),signal:controller.signal,
            headers: {
              "Content-Type": "application/json"
            }
          }), controller)
    }
    fullURL(url:string){
        return this.baseURL+"/"+url
    }

}
export class HttpExecutor{
    callback?: ()=>Promise<Response>
    controller?: AbortController
    constructor(callback:()=>Promise<Response>,controller: AbortController) {
        this.callback = callback
        this.controller = controller
    }
    async execute(): Promise<Response>{
        return await (this.callback as ()=>Promise<Response>)()
    }
    abort(): void{
        try{
            this.controller?.abort()
        }catch (e) {
            //console.error(e)
        }
    }
}
export default new Http()