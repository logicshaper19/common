/**
 * Common Assistant Page
 * AI-powered supply chain assistant with landing and chat screens
 */
import React, { useState, useRef, useEffect, useCallback } from 'react';
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
  
  // Debug: Track every setState call
  const debugSetInputMessage = (value: string) => {
    console.log('🔧 setInputMessage CALLED with:', value, 'from:', new Error().stack?.split('\n')[2]);
    setInputMessage(value);
  };
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  

  // Core supply chain topics for the landing screen
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
    }
  ];

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);


  const startChat = useCallback((initialMessage?: string) => {
    setIsInChat(true);
    if (initialMessage) {
      debugSetInputMessage(initialMessage);
      // Auto-send the initial message
      setTimeout(() => {
        sendMessage(initialMessage);
      }, 100);
    }
  }, []);

  const handleSuggestedAction = (action: typeof suggestedActions[0]) => {
    const prompts = {
      traceability: "Explain how traceability works in our supply chain system",
      compliance: "Help me understand EUDR and RSPO compliance requirements",
      inventory: "Show me how to manage inventory batches and stock levels"
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
    debugSetInputMessage('');
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
    <div className="h-screen flex flex-col bg-gradient-to-br from-gray-50 via-purple-50/30 to-gray-100 relative overflow-hidden">
      {/* Background Pattern */}
      <div className="absolute inset-0 opacity-5">
        <div className="absolute top-20 left-20 w-32 h-32 bg-purple-400 rounded-full blur-3xl"></div>
        <div className="absolute bottom-20 right-20 w-40 h-40 bg-purple-300 rounded-full blur-3xl"></div>
        <div className="absolute top-1/2 left-1/3 w-24 h-24 bg-purple-500 rounded-full blur-2xl"></div>
        <div className="absolute top-1/4 right-1/4 w-20 h-20 bg-purple-200 rounded-full blur-2xl"></div>
        <div className="absolute bottom-1/3 left-1/2 w-28 h-28 bg-purple-400 rounded-full blur-3xl"></div>
      </div>
      
      {/* Subtle Grid Pattern */}
      <div className="absolute inset-0 opacity-[0.02]">
        <div className="w-full h-full" style={{
          backgroundImage: `radial-gradient(circle at 1px 1px, rgba(139, 92, 246, 0.3) 1px, transparent 0)`,
          backgroundSize: '40px 40px'
        }}></div>
      </div>
      
      {/* Main Content */}
      <div className="flex-1 flex flex-col items-center justify-center px-6 relative z-10">
        {/* Input Card */}
        <div className="w-full max-w-4xl mb-8">
          <Card className="bg-white/90 backdrop-blur-sm border-2 border-purple-200/50 shadow-2xl shadow-purple-500/20 hover:shadow-purple-500/30 hover:border-purple-300/70 transition-all duration-300">
            <CardBody className="p-8">
              <div className="text-center mb-8">
                <h1 className="text-3xl font-bold bg-gradient-to-r from-gray-800 to-purple-700 bg-clip-text text-transparent mb-2">
                  How can I help you today?
                </h1>
                <p className="text-gray-500 text-sm">Ask me anything about your supply chain operations</p>
              </div>
              
              <div className="flex items-start space-x-4">
                <div className="flex flex-col space-y-2">
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    className="p-3 hover:bg-purple-50 hover:text-purple-600 transition-all duration-200 rounded-xl"
                  >
                    <PlusIcon className="h-5 w-5" />
                  </Button>
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    className="p-3 hover:bg-purple-50 hover:text-purple-600 transition-all duration-200 rounded-xl"
                  >
                    <Squares2X2Icon className="h-5 w-5" />
                  </Button>
                </div>
                
                <div className="flex-1 relative">
                  <textarea
                    ref={inputRef}
                    defaultValue=""
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        if (inputRef.current) {
                          const value = inputRef.current.value.trim();
                          if (value) {
                            startChat(value);
                            inputRef.current.value = '';
                          }
                        }
                      }
                    }}
                    placeholder="Ask about your supply chain operations..."
                    className="w-full min-h-[140px] p-6 border-2 border-gray-200 rounded-2xl resize-none focus:outline-none focus:ring-4 focus:ring-purple-500/20 focus:border-purple-400 transition-all duration-300 bg-white/50 backdrop-blur-sm text-gray-800 placeholder-gray-400"
                    rows={4}
                    autoComplete="off"
                    spellCheck="false"
                  />
                  <div className="absolute bottom-3 right-3 text-xs text-gray-400">
                    Press Enter to send, Shift+Enter for new line
                  </div>
                </div>
                
                <Button
                  onClick={() => {
                    if (inputRef.current) {
                      const value = inputRef.current.value.trim();
                      if (value) {
                        startChat(value);
                        inputRef.current.value = '';
                      }
                    }
                  }}
                  variant="primary"
                  size="lg"
                  className="p-4 mt-2 rounded-2xl shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200"
                >
                  <PaperAirplaneIcon className="h-5 w-5" />
                </Button>
              </div>
            </CardBody>
          </Card>
        </div>

        {/* Suggested Actions */}
        <div className="w-full max-w-5xl">
          <div className="text-center mb-8">
            <h2 className="text-lg font-semibold text-gray-700 mb-2">Quick Actions</h2>
            <p className="text-sm text-gray-500">Choose a topic to get started</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {suggestedActions.map((action, index) => (
              <div
                key={action.id}
                className="group cursor-pointer"
                onClick={() => handleSuggestedAction(action)}
                style={{ animationDelay: `${index * 100}ms` }}
              >
                <div className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-2xl p-8 hover:bg-white/95 hover:border-purple-200 hover:shadow-xl hover:shadow-purple-500/15 transform hover:scale-105 hover:-translate-y-1 transition-all duration-300 group-hover:border-purple-300">
                  <div className="flex flex-col items-center text-center space-y-4">
                    <div className="p-4 bg-gradient-to-br from-purple-100 to-purple-200 rounded-2xl group-hover:from-purple-200 group-hover:to-purple-300 transition-all duration-300 shadow-sm">
                      <action.icon className="h-8 w-8 text-purple-600 group-hover:text-purple-700" />
                    </div>
                    <div className="space-y-2">
                      <h3 className="font-semibold text-gray-800 group-hover:text-purple-700 transition-colors duration-200 text-lg">
                        {action.label}
                      </h3>
                      <p className="text-sm text-gray-500 group-hover:text-gray-600 transition-colors duration-200 leading-relaxed">
                        {action.description}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  // Chat Screen Component
  const ChatScreen = () => (
    <div className="h-screen flex flex-col bg-gradient-to-br from-gray-50 via-purple-50/20 to-gray-100">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-sm border-b border-white/20 px-6 py-4 shadow-sm">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-gradient-to-br from-purple-100 to-purple-200 rounded-xl shadow-sm">
            <ChatBubbleLeftRightIcon className="h-6 w-6 text-purple-600" />
          </div>
          <div>
            <h1 className="text-xl font-bold bg-gradient-to-r from-gray-800 to-purple-700 bg-clip-text text-transparent">
              Common Assistant
            </h1>
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
                  "max-w-[70%] rounded-2xl px-6 py-4 shadow-sm",
                  message.type === 'user'
                    ? 'bg-gradient-to-br from-purple-600 to-purple-700 text-white shadow-purple-500/20'
                    : 'bg-white/80 backdrop-blur-sm border border-white/30 text-gray-900 shadow-gray-500/10'
                )}
              >
                <div className="text-sm leading-relaxed whitespace-pre-wrap">
                  {message.content}
                </div>
                <div
                  className={cn(
                    "text-xs mt-3 opacity-70",
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
                <div className="w-8 h-8 bg-gradient-to-br from-purple-100 to-purple-200 rounded-full flex items-center justify-center shadow-sm">
                  <SparklesIcon className="h-4 w-4 text-purple-600" />
                </div>
              </div>
              <div className="bg-white/80 backdrop-blur-sm border border-white/30 rounded-2xl px-6 py-4 shadow-sm">
                <div className="flex items-center space-x-3">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                  <span className="text-sm text-gray-600 font-medium">Thinking...</span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="bg-white/80 backdrop-blur-sm border-t border-white/20 px-6 py-6 shadow-lg">
        <div className="max-w-4xl mx-auto">
          <div className="flex gap-4 items-end">
            <div className="flex-1">
              <div className="relative">
                <textarea
                  value={inputMessage}
                  onChange={(e) => debugSetInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask about your supply chain operations..."
                  disabled={isLoading}
                  className="w-full min-h-[60px] max-h-[120px] p-4 border-2 border-gray-200 rounded-2xl resize-none focus:outline-none focus:ring-4 focus:ring-purple-500/20 focus:border-purple-400 transition-all duration-300 bg-white/70 backdrop-blur-sm text-gray-800 placeholder-gray-400 disabled:opacity-50"
                  rows={2}
                />
                <div className="absolute bottom-2 right-2 text-xs text-gray-400">
                  {inputMessage.length > 0 && `${inputMessage.length} chars`}
                </div>
              </div>
            </div>
            <Button
              onClick={() => sendMessage()}
              disabled={isLoading || !inputMessage.trim()}
              variant="primary"
              size="lg"
              className="px-6 py-4 rounded-2xl shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200 disabled:opacity-50 disabled:transform-none"
            >
              <PaperAirplaneIcon className="h-5 w-5" />
            </Button>
          </div>
          <p className="text-xs text-gray-500 mt-3 text-center">
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
