import { useState, useEffect, useRef } from 'react';
import { useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';
import { chatApi } from '../../services/api';
import { useChatStore } from '../../store/chat';
import type { Message } from '../../types';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { TypingIndicator } from './TypingIndicator';
import { ScrollArea } from '../ui/scroll-area';
import { Card } from '../ui/card';

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const { sessionId, setSessionId } = useChatStore();

  const sendMessageMutation = useMutation({
    mutationFn: chatApi.sendMessage,
    onSuccess: (data) => {
      setSessionId(data.session_id);

      const botMessage: Message = {
        id: Date.now().toString(),
        content: data.response,
        sender: 'bot',
        timestamp: data.timestamp || new Date().toISOString(),
        suggestedFollowUps: data.suggested_follow_ups,
        confidence: data.confidence,
        processingMethod: data.processing_method,
      };

      setMessages((prev) => [...prev, botMessage]);
      setIsTyping(false);
      scrollToBottom();
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || error.response?.data?.message || 'Failed to send message');
      setIsTyping(false);
    },
  });

  const handleSendMessage = (content: string) => {
    if (!content.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content,
      sender: 'user',
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsTyping(true);
    scrollToBottom();

    sendMessageMutation.mutate({
      message: content,
      session_id: sessionId || undefined,
    });
  };

  const handleFeedback = async (messageId: string, feedback: 'thumbs_up' | 'thumbs_down') => {
    try {
      await chatApi.sendFeedback({ message_id: messageId, rating: feedback });
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === messageId ? { ...msg, feedback } : msg
        )
      );
      toast.success('Thank you for your feedback!');
    } catch (error) {
      toast.error('Failed to send feedback');
    }
  };

  const scrollToBottom = () => {
    setTimeout(() => {
      scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  return (
    <div className="flex flex-col h-full">
      <Card className="flex-1 overflow-hidden backdrop-blur-sm bg-card/80 border border-border/50">
        <ScrollArea className="h-full p-4">
          <div className="space-y-4">
            {messages.length === 0 && (
              <div className="text-center text-muted-foreground py-12">
                <h3 className="mb-2">Welcome to Library AI Assistant</h3>
                <p>Ask me anything about books, search our catalog, or get recommendations!</p>
              </div>
            )}
            {messages.map((message) => (
              <ChatMessage
                key={message.id}
                message={message}
                onFeedback={handleFeedback}
                onFollowUp={handleSendMessage}
              />
            ))}
            {isTyping && <TypingIndicator />}
            <div ref={scrollRef} />
          </div>
        </ScrollArea>
      </Card>
      <ChatInput onSend={handleSendMessage} disabled={isTyping} />
    </div>
  );
}
