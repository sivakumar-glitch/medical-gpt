const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

function requireAuthToken(token: string | null): string {
    if (!token || !token.trim()) {
        throw new Error('Authentication required. Please sign in.');
    }
    return token;
}

export async function* streamChat(message: string, token: string | null, conversationId?: string) {
    const authToken = requireAuthToken(token);
    const response = await fetch(`${API_BASE}/rag/chat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({
            query: message,
            conversation_id: conversationId
        })
    });

    if (!response.ok) {
        let serverMessage = '';
        try {
            serverMessage = await response.text();
        } catch {
            serverMessage = '';
        }
        throw new Error(`Chat request failed (${response.status} ${response.statusText})${serverMessage ? `: ${serverMessage}` : ''}`);
    }
    if (!response.body) throw new Error('No response body');

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        // Parse SSE format (data: ...)
        const lines = chunk.split('\n');
        for (const line of lines) {
            if (line.startsWith('data: ')) {
                yield line.slice(6);
            }
        }
    }
}

export async function login(username: string, password: string): Promise<string> {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData,
    });

    if (!response.ok) {
        throw new Error('Invalid email or password');
    }

    const data = await response.json();
    return data.access_token;
}

// Chat History API Functions
export interface Message {
    role: string;
    content: string;
    timestamp: string;
}

export interface Conversation {
    id: string;
    user_id: number;
    title: string;
    messages: Message[];
    created_at: string;
    updated_at: string;
}

export interface ConversationListItem {
    id: string;
    title: string;
    created_at: string;
    updated_at: string;
    message_count: number;
}

export async function getConversations(token: string): Promise<ConversationListItem[]> {
    const authToken = requireAuthToken(token);
    const response = await fetch(`${API_BASE}/chat-history/conversations`, {
        headers: {
            'Authorization': `Bearer ${authToken}`
        }
    });

    if (!response.ok) throw new Error('Failed to fetch conversations');
    return response.json();
}

export async function getConversation(conversationId: string, token: string): Promise<Conversation> {
    const authToken = requireAuthToken(token);
    const response = await fetch(`${API_BASE}/chat-history/conversations/${conversationId}`, {
        headers: {
            'Authorization': `Bearer ${authToken}`
        }
    });

    if (!response.ok) throw new Error('Failed to fetch conversation');
    return response.json();
}

export async function createConversation(title: string, token: string): Promise<Conversation> {
    const authToken = requireAuthToken(token);
    const response = await fetch(`${API_BASE}/chat-history/conversations`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({ title, messages: [] })
    });

    if (!response.ok) throw new Error('Failed to create conversation');
    return response.json();
}

export async function updateConversation(
    conversationId: string,
    data: { title?: string; messages?: Message[] },
    token: string
): Promise<Conversation> {
    const authToken = requireAuthToken(token);
    const response = await fetch(`${API_BASE}/chat-history/conversations/${conversationId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify(data)
    });

    if (!response.ok) throw new Error('Failed to update conversation');
    return response.json();
}

export async function deleteConversation(conversationId: string, token: string): Promise<void> {
    const authToken = requireAuthToken(token);
    const response = await fetch(`${API_BASE}/chat-history/conversations/${conversationId}`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${authToken}`
        }
    });

    if (!response.ok) throw new Error('Failed to delete conversation');
}

export async function transcribeAudio(audioFile: File, token: string): Promise<string> {
    const authToken = requireAuthToken(token);
    const formData = new FormData();
    formData.append('file', audioFile);

    const response = await fetch(`${API_BASE}/stt/transcribe`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${authToken}`
        },
        body: formData
    });

    if (!response.ok) throw new Error('Transcription failed');
    const data = await response.json();
    return data.transcription;
}

export async function uploadFile(file: File, token: string): Promise<string> {
    const authToken = requireAuthToken(token);
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE}/upload/upload`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${authToken}`
        },
        body: formData
    });

    if (!response.ok) throw new Error('Upload failed');
    const data = await response.json();
    return data.message;
}
