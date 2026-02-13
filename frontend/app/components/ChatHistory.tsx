'use client';

import { useState } from 'react';
import { Trash2, Edit2, Check, X } from 'lucide-react';
import { ConversationListItem } from '@/lib/api';

interface ChatHistoryProps {
    conversations: ConversationListItem[];
    currentConversationId: string | null;
    onSelectConversation: (id: string) => void;
    onNewChat: () => void;
    onDeleteConversation: (id: string) => void;
    onRenameConversation: (id: string, newTitle: string) => void;
    isCollapsed: boolean;
    onToggleCollapse: () => void;
}

export default function ChatHistory({
    conversations,
    currentConversationId,
    onSelectConversation,
    onNewChat,
    onDeleteConversation,
    onRenameConversation,
    isCollapsed,
    onToggleCollapse
}: ChatHistoryProps) {
    const [editingId, setEditingId] = useState<string | null>(null);
    const [editTitle, setEditTitle] = useState('');

    const handleStartEdit = (conv: ConversationListItem) => {
        setEditingId(conv.id);
        setEditTitle(conv.title);
    };

    const handleSaveEdit = (id: string) => {
        if (editTitle.trim()) {
            onRenameConversation(id, editTitle.trim());
        }
        setEditingId(null);
    };

    const handleCancelEdit = () => {
        setEditingId(null);
        setEditTitle('');
    };

    if (isCollapsed) {
        return (
            <div className="w-16 bg-gray-900 border-r border-gray-700 flex flex-col items-center py-4">
                <button
                    onClick={onToggleCollapse}
                    className="p-3 hover:bg-gray-800 rounded-lg transition-colors mb-4"
                    title="Expand sidebar"
                >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                    </svg>
                </button>
                <button
                    onClick={onNewChat}
                    className="p-3 hover:bg-gray-800 rounded-lg transition-colors"
                    title="New chat"
                >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                </button>
            </div>
        );
    }

    return (
        <aside className="w-80 bg-gray-900 border-r border-gray-700 flex flex-col transition-all duration-300">
            {/* Header */}
            <div className="p-4 border-b border-gray-700">
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-lg font-semibold text-blue-400">MedAI Chat</h2>
                    <button
                        onClick={onToggleCollapse}
                        className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
                        title="Collapse sidebar"
                    >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
                        </svg>
                    </button>
                </div>
                <button
                    onClick={onNewChat}
                    className="w-full bg-blue-600 hover:bg-blue-500 text-white rounded-lg p-3 transition-colors flex items-center justify-center gap-2"
                >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    New Chat
                </button>
            </div>

            {/* Conversations List */}
            <div className="flex-1 overflow-y-auto p-2">
                {conversations.length === 0 ? (
                    <div className="text-center text-gray-500 mt-8 px-4">
                        <p className="text-sm">No conversations yet</p>
                        <p className="text-xs mt-2">Start a new chat to begin</p>
                    </div>
                ) : (
                    <div className="space-y-1">
                        {conversations.map((conv) => (
                            <div
                                key={conv.id}
                                className={`group relative rounded-lg transition-colors ${currentConversationId === conv.id
                                    ? 'bg-gray-800 border border-gray-600'
                                    : 'hover:bg-gray-800 border border-transparent'
                                    }`}
                            >
                                {editingId === conv.id ? (
                                    <div className="p-3 flex items-center gap-2">
                                        <input
                                            type="text"
                                            value={editTitle}
                                            onChange={(e) => setEditTitle(e.target.value)}
                                            onKeyDown={(e) => {
                                                if (e.key === 'Enter') handleSaveEdit(conv.id);
                                                if (e.key === 'Escape') handleCancelEdit();
                                            }}
                                            className="flex-1 bg-gray-700 text-white text-sm px-2 py-1 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                                            autoFocus
                                        />
                                        <button
                                            onClick={() => handleSaveEdit(conv.id)}
                                            className="p-1 hover:bg-gray-700 rounded"
                                        >
                                            <Check className="w-4 h-4 text-green-500" />
                                        </button>
                                        <button
                                            onClick={handleCancelEdit}
                                            className="p-1 hover:bg-gray-700 rounded"
                                        >
                                            <X className="w-4 h-4 text-red-500" />
                                        </button>
                                    </div>
                                ) : (
                                    <>
                                        <button
                                            onClick={() => onSelectConversation(conv.id)}
                                            className="w-full text-left p-3 pr-20"
                                        >
                                            <div className="text-sm font-medium text-gray-200 truncate">
                                                {conv.title}
                                            </div>
                                            <div className="text-xs text-gray-500 mt-1">
                                                {new Date(conv.updated_at).toLocaleDateString()}
                                            </div>
                                        </button>
                                        <div className="absolute right-2 top-1/2 -translate-y-1/2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    handleStartEdit(conv);
                                                }}
                                                className="p-2 hover:bg-gray-700 rounded transition-colors"
                                                title="Rename"
                                            >
                                                <Edit2 className="w-4 h-4 text-gray-400" />
                                            </button>
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    if (confirm('Delete this conversation?')) {
                                                        onDeleteConversation(conv.id);
                                                    }
                                                }}
                                                className="p-2 hover:bg-gray-700 rounded transition-colors"
                                                title="Delete"
                                            >
                                                <Trash2 className="w-4 h-4 text-red-400" />
                                            </button>
                                        </div>
                                    </>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-gray-700">
                <div className="text-xs text-gray-500">
                    {conversations.length} conversation{conversations.length !== 1 ? 's' : ''}
                </div>
            </div>
        </aside>
    );
}
