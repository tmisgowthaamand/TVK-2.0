import React, { useState, useEffect } from 'react';
import { X, Download, ChevronDown } from 'lucide-react';
import axios from 'axios';

export default function ChatViewer({ refId, onClose, API_BASE }) {
    const [messages, setMessages] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (refId) {
            fetchChat();
        }
    }, [refId]);

    const fetchChat = async () => {
        try {
            setLoading(true);
            setError(null);
            const res = await axios.get(`${API_BASE}/api/dashboard/chat/${refId}`);
            if (res.data && res.data.messages) {
                setMessages(res.data.messages);
            } else {
                setMessages([]);
            }
        } catch (err) {
            console.error("Error fetching chat:", err);
            // Don't show error, just show empty state
            setMessages([]);
        } finally {
            setLoading(false);
        }
    };

    const exportChat = () => {
        let text = `Chat History - ${refId}\n`;
        text += `Total Messages: ${messages.length}\n`;
        text += '=' .repeat(50) + '\n\n';

        messages.forEach(msg => {
            const sender = msg.sender === 'user' ? 'User' : 'Bot';
            const time = new Date(msg.timestamp).toLocaleString();
            text += `[${time}] ${sender}: ${msg.content}\n`;
            if (msg.location) {
                text += `  📍 Location: ${msg.location.lat}, ${msg.location.lon}\n`;
            }
            if (msg.media_id) {
                text += `  📸 Media ID: ${msg.media_id}\n`;
            }
        });

        const blob = new Blob([text], { type: 'text/plain' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `chat-${refId}.txt`;
        a.click();
    };

    return (
        <div className="chat-viewer-modal">
            <div className="chat-viewer-content">
                <div className="chat-viewer-header">
                    <div>
                        <h2>Conversation History</h2>
                        <p>Reference ID: {refId} • {messages.length} messages</p>
                    </div>
                    <div className="chat-viewer-actions">
                        <button onClick={exportChat} className="chat-export-btn" title="Export chat">
                            <Download size={18} />
                        </button>
                        <button onClick={onClose} className="chat-close-btn" title="Close">
                            <X size={18} />
                        </button>
                    </div>
                </div>

                <div className="chat-viewer-body">
                    {loading && <div className="chat-loading">Loading conversation...</div>}
                    {error && <div className="chat-error">⚠️ {error}</div>}

                    {!loading && messages.length === 0 && !error && (
                        <div className="chat-empty">
                            <div style={{marginBottom: '16px', fontSize: '24px'}}>💬</div>
                            <div style={{fontWeight: 600, marginBottom: '8px', fontSize: '14px'}}>No messages yet</div>
                            <div style={{fontSize: '12px', color: 'var(--text-dim)', lineHeight: '1.6'}}>
                                This submission doesn't have any chat messages recorded yet.<br/>
                                Messages will appear here as the user interacts with the bot.
                            </div>
                        </div>
                    )}

                    {!loading && messages.length > 0 && (
                        <div className="messages-list">
                            {messages.map((msg, idx) => (
                                <div key={idx} className={`message message-${msg.sender}`}>
                                    <div className="message-sender">{msg.sender === 'user' ? '👤 User' : '🤖 Bot'}</div>
                                    <div className="message-content">
                                        {msg.content}
                                        {msg.location && (
                                            <div className="message-meta">
                                                📍 {msg.location.lat.toFixed(4)}, {msg.location.lon.toFixed(4)}
                                            </div>
                                        )}
                                        {msg.media_id && (
                                            <div className="message-meta">
                                                📸 Image attached
                                            </div>
                                        )}
                                    </div>
                                    <div className="message-time">
                                        {msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString() : 'Unknown time'}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
