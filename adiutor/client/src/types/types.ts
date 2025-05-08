export interface Message{
    id: number,
    loading: boolean
    speech?: boolean
    cost?: number
    role?: string
    text?: string
    sources?: MessageSource[]
}

export interface MessageSource{
    url: string
    title: string
    score: number
    text: string
}

export interface WebPage{
    id: number
    domain: string
    url: string
    title: string
    html: string
    created_at: string
    updated_at: string
}

export interface Settings{
    url: string
    api_token: string
    system_prompt: string
}

export type WebSearch = {
    current: string | null
    sources: MessageSource[]
}
export type OnMessage = (_:Message) => any