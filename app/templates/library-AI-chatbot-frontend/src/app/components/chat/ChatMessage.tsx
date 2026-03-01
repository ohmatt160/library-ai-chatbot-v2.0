import { formatDistanceToNow } from 'date-fns';
import ReactMarkdown, { LinkInlineRenderer } from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ThumbsUp, ThumbsDown } from 'lucide-react';
import type { Message } from '../../types';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { cn } from '../ui/utils';

interface ChatMessageProps {
  message: Message;
  onFeedback: (messageId: string, feedback: 'thumbs_up' | 'thumbs_down') => void;
  onFollowUp: (message: string) => void;
}

// Custom link component that opens in new tab
export function ChatMessage({ message, onFeedback, onFollowUp }: ChatMessageProps) {
  const isUser = message.sender === 'user';

  const LinkRenderer: LinkInlineRenderer = ({ href, children }) => (
    <a 
      href={href} 
      target="_blank" 
      rel="noopener noreferrer"
      className="text-blue-500 underline hover:text-blue-600 transition-colors"
    >
      {children}
    </a>
  );

  const components = {
    a: LinkRenderer
  };

  return (
    <div className={cn('flex', isUser ? 'justify-end' : 'justify-start')}>
      <div className={cn('max-w-[80%] space-y-2', isUser ? 'items-end' : 'items-start')}>
        <div
          className={cn(
            'rounded-lg px-4 py-3 backdrop-blur-sm',
            isUser
              ? 'bg-primary text-primary-foreground ml-auto'
              : 'bg-card border border-border/50'
          )}
        >
          {isUser ? (
            <p>{message.content}</p>
          ) : (
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <ReactMarkdown 
                remarkPlugins={[remarkGfm]}
                components={components}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        <div className="flex items-center gap-2 px-2">
          <span className="text-xs text-muted-foreground">
            {formatDistanceToNow(new Date(message.timestamp), { addSuffix: true })}
          </span>

          {!isUser && (
            <div className="flex gap-1">
              <Button
                variant="ghost"
                size="sm"
                className={cn(
                  'h-6 w-6 p-0',
                  message.feedback === 'thumbs_up' && 'text-green-500'
                )}
                onClick={() => onFeedback(message.id, 'thumbs_up')}
              >
                <ThumbsUp className="h-3 w-3" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className={cn(
                  'h-6 w-6 p-0',
                  message.feedback === 'thumbs_down' && 'text-red-500'
                )}
                onClick={() => onFeedback(message.id, 'thumbs_down')}
              >
                <ThumbsDown className="h-3 w-3" />
              </Button>
            </div>
          )}
        </div>

        {!isUser && message.suggestedFollowUps && message.suggestedFollowUps.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {message.suggestedFollowUps.map((followUp, index) => (
              <Badge
                key={index}
                variant="outline"
                className="cursor-pointer hover:bg-accent"
                onClick={() => onFollowUp(followUp)}
              >
                {followUp}
              </Badge>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
