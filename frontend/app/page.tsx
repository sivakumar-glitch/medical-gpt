'use client';

import { useState, useEffect, useRef } from 'react';
import { streamChat, getConversations, createConversation, updateConversation, deleteConversation, ConversationListItem, Message as APIMessage, transcribeAudio, uploadFile } from '@/lib/api';
import ReactMarkdown from 'react-markdown';
import LoginForm from './components/LoginForm';
import ChatHistory from './components/ChatHistory';

interface Message {
    role: string;
    content: string;
}

interface LocalConversation {
    id: string;
    title: string;
    messages: Message[];
    createdAt: string;
    updatedAt: string;
}

export default function ChatPage() {
    const [conversations, setConversations] = useState<ConversationListItem[]>([]);
    const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
    const [currentMessages, setCurrentMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [token, setToken] = useState<string | null>(null);
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
    const [isRecording, setIsRecording] = useState(false);
    const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
    const scrollRef = useRef<HTMLDivElement>(null);

    // Load token and conversations on mount
    useEffect(() => {
        const storedToken = localStorage.getItem('token');
        if (storedToken) {
            setToken(storedToken);
            loadConversations(storedToken);
        }
    }, []);

    // Auto-scroll to bottom when messages change
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [currentMessages]);

    const loadConversations = async (authToken: string) => {
        try {
            const convs = await getConversations(authToken);
            setConversations(convs);
        } catch (error) {
            console.error('Failed to load conversations:', error);
        }
    };

    const startRecording = async () => {
        if (!navigator.mediaDevices) {
            alert('Media devices not supported');
            return;
        }
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const preferredTypes = [
                'audio/webm;codecs=opus',
                'audio/webm',
                'audio/ogg;codecs=opus',
                'audio/ogg'
            ];
            const mimeType = preferredTypes.find((type) => MediaRecorder.isTypeSupported(type));
            const recorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);
            setMediaRecorder(recorder);
            const chunks: Blob[] = [];
            recorder.ondataavailable = (e) => chunks.push(e.data);
            recorder.onstop = async () => {
                const blobType = mimeType || 'audio/webm';
                const extension = blobType.includes('ogg') ? 'ogg' : 'webm';
                const blob = new Blob(chunks, { type: blobType });
                const file = new File([blob], `recording.${extension}`, { type: blobType });
                if (token) {
                    try {
                        const transcription = await transcribeAudio(file, token);
                        setInput(transcription);
                    } catch (error) {
                        console.error('Transcription failed:', error);
                        alert('Transcription failed');
                    }
                }
            };
            recorder.start();
            setIsRecording(true);
        } catch (error) {
            console.error('Error starting recording:', error);
        }
    };

    const stopRecording = () => {
        if (mediaRecorder) {
            mediaRecorder.stop();
            setIsRecording(false);
            mediaRecorder.stream.getTracks().forEach(track => track.stop());
        }
    };

    const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        console.log("File selected:", file);
        if (!file || !token) {
            console.log("No file or no token");
            return;
        }
        try {
            console.log("Uploading file...");
            const message = await uploadFile(file, token);
            console.log("Upload response:", message);
            alert(message);
        } catch (error) {
            console.error('Upload failed:', error);
            alert('Upload failed');
        }
    };

    const handleLoginSuccess = (newToken: string) => {
        setToken(newToken);
        localStorage.setItem('token', newToken);
        loadConversations(newToken);
    };

    const handleLogout = () => {
        setToken(null);
        localStorage.removeItem('token');
        setConversations([]);
        setCurrentConversationId(null);
        setCurrentMessages([]);
    };

    const handleNewChat = () => {
        setCurrentConversationId(null);
        setCurrentMessages([]);
    };

    const handleSelectConversation = async (conversationId: string) => {
        if (!token) return;

        try {
            // Load from localStorage first for instant response
            const localConvs = JSON.parse(localStorage.getItem('conversations') || '{}');
            if (localConvs[conversationId]) {
                setCurrentMessages(localConvs[conversationId].messages);
                setCurrentConversationId(conversationId);
            }
        } catch (error) {
            console.error('Failed to load conversation:', error);
        }
    };

    const handleDeleteConversation = async (conversationId: string) => {
        if (!token) return;

        try {
            await deleteConversation(conversationId, token);

            // Remove from localStorage
            const localConvs = JSON.parse(localStorage.getItem('conversations') || '{}');
            delete localConvs[conversationId];
            localStorage.setItem('conversations', JSON.stringify(localConvs));

            // Reload conversations
            await loadConversations(token);

            // If deleted conversation was current, clear it
            if (currentConversationId === conversationId) {
                handleNewChat();
            }
        } catch (error) {
            console.error('Failed to delete conversation:', error);
        }
    };

    const handleRenameConversation = async (conversationId: string, newTitle: string) => {
        if (!token) return;

        try {
            await updateConversation(conversationId, { title: newTitle }, token);

            // Update localStorage
            const localConvs = JSON.parse(localStorage.getItem('conversations') || '{}');
            if (localConvs[conversationId]) {
                localConvs[conversationId].title = newTitle;
                localStorage.setItem('conversations', JSON.stringify(localConvs));
            }

            // Reload conversations
            await loadConversations(token);
        } catch (error) {
            console.error('Failed to rename conversation:', error);
        }
    };

    const saveConversationToLocalStorage = (convId: string, title: string, messages: Message[]) => {
        const localConvs = JSON.parse(localStorage.getItem('conversations') || '{}');
        localConvs[convId] = {
            id: convId,
            title,
            messages,
            createdAt: localConvs[convId]?.createdAt || new Date().toISOString(),
            updatedAt: new Date().toISOString()
        };
        localStorage.setItem('conversations', JSON.stringify(localConvs));
    };

    const generateTitle = (message: string): string => {
        // Generate title from first message (max 50 chars)
        return message.length > 50 ? message.substring(0, 50) + '...' : message;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isLoading || !token) return;

        const userMessage: Message = { role: 'user', content: input };
        const newMessages = [...currentMessages, userMessage];
        setCurrentMessages(newMessages);
        setInput('');
        setIsLoading(true);

        // Create conversation if this is the first message
        let convId = currentConversationId;
        let convTitle = '';

        if (!convId) {
            try {
                convTitle = generateTitle(input);
                const newConv = await createConversation(convTitle, token);
                convId = newConv.id;
                setCurrentConversationId(convId);
                await loadConversations(token);
            } catch (error) {
                console.error('Failed to create conversation:', error);
            }
        }

        const assistantMessage: Message = { role: 'assistant', content: '' };
        setCurrentMessages((prev) => [...prev, assistantMessage]);

        try {
            const stream = streamChat(input, token, convId || undefined);
            for await (const chunk of stream) {
                setCurrentMessages((prev) => {
                    const last = prev[prev.length - 1];
                    const updated = { ...last, content: last.content + chunk };
                    return [...prev.slice(0, -1), updated];
                });
            }

            // Save to backend and localStorage after streaming completes
            const finalMessages = [...newMessages, { ...assistantMessage, content: assistantMessage.content }];

            if (convId) {
                try {
                    // Convert to API format
                    const apiMessages: APIMessage[] = finalMessages.map(m => ({
                        role: m.role,
                        content: m.content,
                        timestamp: new Date().toISOString()
                    }));

                    await updateConversation(convId, { messages: apiMessages }, token);
                    saveConversationToLocalStorage(convId, convTitle || conversations.find(c => c.id === convId)?.title || 'Chat', finalMessages);
                    await loadConversations(token);
                } catch (error) {
                    console.error('Failed to save conversation:', error);
                }
            }
        } catch (error) {
            console.error(error);
            setCurrentMessages((prev) => [
                ...prev.slice(0, -1),
                { role: 'assistant', content: 'Sorry, something went wrong. Please check if the backend is running.' }
            ]);
        } finally {
            setIsLoading(false);
        }
    };

    if (!token) {
        return <LoginForm onLoginSuccess={handleLoginSuccess} />;
    }

    return (
        <div className="flex h-screen bg-white">
            {/* Chat History Sidebar */}
            <ChatHistory
                conversations={conversations}
                currentConversationId={currentConversationId}
                onSelectConversation={handleSelectConversation}
                onNewChat={handleNewChat}
                onDeleteConversation={handleDeleteConversation}
                onRenameConversation={handleRenameConversation}
                isCollapsed={sidebarCollapsed}
                onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
            />

            {/* Main Chat Area - Full Screen */}
            <main className="flex-1 flex flex-col items-center justify-center relative bg-gray-50">
                {/* Header with Logout */}
                <div className="absolute top-4 right-4 z-10">
                    <button
                        onClick={handleLogout}
                        className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-200 rounded-lg transition-colors"
                    >
                        Sign Out
                    </button>
                </div>

                {/* Messages Area - Centered like ChatGPT */}
                <div className="flex-1 w-full max-w-4xl overflow-y-auto px-4 py-8">
                    {currentMessages.length === 0 && (
                        <div className="flex flex-col items-center justify-center h-full text-center">
                            <h1 className="text-4xl font-semibold mb-4 text-gray-800">
                                How can I help you today?
                            </h1>
                            <p className="text-gray-600 text-lg max-w-md">
                                Ask any medical question. Our AI assistant will provide helpful information.
                            </p>
                        </div>
                    )}

                    <div className="space-y-6">
                        {currentMessages.map((m, i) => (
                            <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                <div className={`max-w-[80%] p-4 rounded-2xl shadow-sm ${
                                    m.role === 'user'
                                        ? 'bg-blue-600 text-white'
                                        : 'bg-white text-gray-800 border border-gray-200'
                                }`}>
                                    <ReactMarkdown className="prose prose-sm max-w-none">
                                        {m.content}
                                    </ReactMarkdown>
                                </div>
                            </div>
                        ))}
                        {isLoading && (
                            <div className="flex justify-start">
                                <div className="bg-white p-4 rounded-2xl border border-gray-200 shadow-sm">
                                    <div className="flex gap-1">
                                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* Input Area - Fixed at Bottom, Centered */}
                <div className="w-full max-w-4xl p-6 bg-white border-t border-gray-200">
                    <form onSubmit={handleSubmit} className="relative max-w-2xl mx-auto">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="Ask a medical question..."
                            className="w-full bg-gray-50 border border-gray-300 rounded-xl py-3 pl-4 pr-24 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-base"
                        />
                        <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center space-x-2">
                            {isRecording && (
                                <div className="waveform mr-1">
                                    <span className="wave-bar" style={{ animationDelay: '0ms' }}></span>
                                    <span className="wave-bar" style={{ animationDelay: '120ms' }}></span>
                                    <span className="wave-bar" style={{ animationDelay: '240ms' }}></span>
                                    <span className="wave-bar" style={{ animationDelay: '360ms' }}></span>
                                    <span className="wave-bar" style={{ animationDelay: '480ms' }}></span>
                                </div>
                            )}
                            <button
                                type="button"
                                onClick={isRecording ? stopRecording : startRecording}
                                className={`p-2 rounded-lg transition-colors ${isRecording ? 'text-red-500' : 'text-gray-500 hover:text-gray-700'}`}
                            >
                                <svg viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
                                    <path d="M12 1a4 4 0 00-4 4v6a4 4 0 008 0V5a4 4 0 00-4-4z"/>
                                    <path d="M19 10v1a7 7 0 01-14 0v-1H3v1a9 9 0 0018 0v-1h-2z"/>
                                </svg>
                            </button>
                            <label htmlFor="file-upload" className="p-2 text-gray-500 hover:text-gray-700 cursor-pointer">
                                <input id="file-upload" type="file" accept=".txt,.pdf" onChange={handleFileUpload} className="hidden" />
                                <svg viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
                                    <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                                    <path d="M14 2v6h6"/>
                                </svg>
                            </label>
                            <button
                                type="submit"
                                disabled={isLoading || !input.trim()}
                                className="p-2 text-blue-600 hover:text-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                            >
                                <svg viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
                                    <path d="M3.478 2.405a.75.75 0 00-.926.94l2.432 7.905H13.5a.75.75 0 010 1.5H4.984l-2.432 7.905a.75.75 0 00.926.94 60.519 60.519 0 0018.445-8.986.75.75 0 000-1.218A60.517 60.517 0 003.478 2.405z" />
                                </svg>
                            </button>
                        </div>
                    </form>
                    <p className="text-xs text-center mt-3 text-gray-500">
                        MedAI can make mistakes. Consider checking with a doctor for critical information.
                    </p>
                </div>
            </main>
        </div>
    );
}
