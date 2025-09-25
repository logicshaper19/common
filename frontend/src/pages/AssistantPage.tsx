/**
 * Common Assistant Page
 * AI-powered supply chain assistant with landing and chat screens
 */
import React, { useState, useRef, useEffect } from 'react';
import { Button } from '../components/ui/Button';
import Input from '../components/ui/Input';
import { Card, CardHeader, CardTitle, CardBody } from '../components/ui/Card';
import { 
  PaperAirplaneIcon,
  ChatBubbleLeftRightIcon,
  UserIcon,
  SparklesIcon,
  ChartBarIcon,
  ShieldCheckIcon,
  ArchiveBoxIcon,
  BeakerIcon,
  LightBulbIcon,
  PlusIcon,
  Squares2X2Icon,
  ChevronDownIcon
} from '@heroicons/react/24/outline';
import { cn } from '../lib/utils';
import { useAuth } from '../contexts/AuthContext';
import { assistantApi } from '../services/assistantApi';

interface Message {
  id: number;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

const AssistantPage: React.FC = () => {
  const { user } = useAuth();
  const [isInChat, setIsInChat] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Supply chain topics for the landing screen
  const suggestedActions = [
    {
      id: 'traceability',
      label: 'Traceability',
      icon: ChartBarIcon,
      description: 'Track products from origin to consumer'
    },
    {
      id: 'compliance',
      label: 'Compliance',
      icon: ShieldCheckIcon,
      description: 'EUDR, RSPO, and regulatory requirements'
    },
    {
      id: 'inventory',
      label: 'Inventory',
      icon: ArchiveBoxIcon,
      description: 'Manage batches and stock levels'
    },
    {
      id: 'transformation',
      label: 'Transformation',
      icon: BeakerIcon,
      description: 'Processing and manufacturing events'
    },
    {
      id: 'choice',
      label: 'Assistant\'s choice',
      icon: LightBulbIcon,
      description: 'Let me suggest something useful'
    }
  ];

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const startChat = (initialMessage?: string) => {
    setIsInChat(true);
    if (initialMessage) {
      setInputMessage(initialMessage);
      // Auto-send the initial message
      setTimeout(() => {
        sendMessage(initialMessage);
      }, 100);
    }
  };

  const handleSuggestedAction = (action: typeof suggestedActions[0]) => {
    const prompts = {
      traceability: "Explain how traceability works in our supply chain system",
      compliance: "Help me understand EUDR and RSPO compliance requirements",
      inventory: "Show me how to manage inventory batches and stock levels",
      transformation: "Explain the transformation process for processing events",
      choice: "What's the most important thing I should focus on today?"
    };
    
    startChat(prompts[action.id as keyof typeof prompts]);
  };

  const sendMessage = async (messageText?: string) => {
    const messageToSend = messageText || inputMessage.trim();
    if (!messageToSend || isLoading) return;

    const userMessage: Message = {
      id: Date.now(),
      type: 'user',
      content: messageToSend,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    // Call backend assistant API
    try {
      const response = await assistantApi.sendMessage(userMessage.content);
      const assistantMessage: Message = {
        id: Date.now() + 1,
        type: 'assistant',
        content: response.response,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error getting assistant response:', error);
      const errorMessage: Message = {
        id: Date.now() + 1,
        type: 'assistant',
        content: "I'm sorry, I'm having trouble connecting to the backend right now. Please try again later.",
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  // Landing Screen Component
  const LandingScreen = () => (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Main Content */}
      <div className="flex-1 flex flex-col items-center justify-center px-6">
        {/* Input Card */}
        <div className="w-full max-w-4xl mb-8">
          <Card className="bg-white border border-gray-200 shadow-sm">
            <CardBody className="p-6">
              <div className="text-center mb-6">
                <p className="text-lg text-gray-600">How can I help you today?</p>
              </div>
              
              <div className="flex items-start space-x-3">
                <Button variant="ghost" size="sm" className="p-2 mt-2">
                  <PlusIcon className="h-4 w-4 text-gray-500" />
                </Button>
                <Button variant="ghost" size="sm" className="p-2 mt-2">
                  <Squares2X2Icon className="h-4 w-4 text-gray-500" />
                </Button>
                
                <div className="flex-1">
                  <textarea
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), startChat())}
                    placeholder="Ask about your supply chain operations..."
                    className="w-full min-h-[120px] p-4 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    rows={4}
                  />
                </div>
                
                <Button
                  onClick={() => startChat()}
                  disabled={!inputMessage.trim()}
                  variant="primary"
                  size="sm"
                  className="p-2 mt-2"
                >
                  <PaperAirplaneIcon className="h-4 w-4" />
                </Button>
              </div>
            </CardBody>
          </Card>
        </div>

        {/* Suggested Actions */}
        <div className="w-full max-w-4xl">
          <div className="flex flex-wrap gap-3 justify-center">
            {suggestedActions.map((action) => (
              <Button
                key={action.id}
                variant="outline"
                size="sm"
                onClick={() => handleSuggestedAction(action)}
                className="flex items-center space-x-2 px-4 py-2 bg-white border-gray-200 hover:border-purple-300 hover:bg-purple-50"
              >
                <action.icon className="h-4 w-4 text-gray-600" />
                <span className="text-gray-700">{action.label}</span>
              </Button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  // Chat Screen Component
  const ChatScreen = () => (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-purple-100 rounded-lg">
            <ChatBubbleLeftRightIcon className="h-6 w-6 text-purple-600" />
          </div>
          <div>
            <h1 className="text-xl font-semibold text-gray-900">Common Assistant</h1>
            <p className="text-sm text-gray-600">Your AI-powered supply chain assistant</p>
          </div>
        </div>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        <div className="max-w-4xl mx-auto space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={cn(
                "flex gap-3",
                message.type === 'user' ? 'justify-end' : 'justify-start'
              )}
            >
              {message.type === 'assistant' && (
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                    <SparklesIcon className="h-4 w-4 text-purple-600" />
                  </div>
                </div>
              )}
              
              <div
                className={cn(
                  "max-w-[70%] rounded-lg px-4 py-3",
                  message.type === 'user'
                    ? 'bg-purple-600 text-white'
                    : 'bg-white border border-gray-200 text-gray-900'
                )}
              >
                <div className="text-sm leading-relaxed whitespace-pre-wrap">
                  {message.content}
                </div>
                <div
                  className={cn(
                    "text-xs mt-2",
                    message.type === 'user' ? 'text-purple-100' : 'text-gray-500'
                  )}
                >
                  {formatTime(message.timestamp)}
                </div>
              </div>

              {message.type === 'user' && (
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center">
                    <UserIcon className="h-4 w-4 text-gray-600" />
                  </div>
                </div>
              )}
            </div>
          ))}
          
          {isLoading && (
            <div className="flex gap-3 justify-start">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                  <SparklesIcon className="h-4 w-4 text-purple-600" />
                </div>
              </div>
              <div className="bg-white border border-gray-200 rounded-lg px-4 py-3">
                <div className="flex items-center space-x-2">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                  <span className="text-sm text-gray-500">Thinking...</span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="bg-white border-t border-gray-200 px-6 py-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex gap-3">
            <div className="flex-1">
              <Input
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask about your supply chain operations..."
                disabled={isLoading}
                className="w-full"
              />
            </div>
            <Button
              onClick={() => sendMessage()}
              disabled={isLoading || !inputMessage.trim()}
              variant="primary"
              size="md"
              leftIcon={<PaperAirplaneIcon className="h-4 w-4" />}
            >
              Send
            </Button>
          </div>
          <p className="text-xs text-gray-500 mt-2 text-center">
            Press Enter to send, Shift+Enter for new line
          </p>
        </div>
      </div>
    </div>
  );

  // Main return - choose between landing and chat screens
  return isInChat ? <ChatScreen /> : <LandingScreen />;
};

export default AssistantPage;
