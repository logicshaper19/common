import React, { useState, useRef, useEffect, Component } from 'react';
import { LineChart, DonutChart, GaugeChart, DataTable, NetworkGraph, MetricCards } from './Charts';
import './StreamingChatAssistant.css';

// Error Boundary Component
class StreamingChatErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({
      error: error,
      errorInfo: errorInfo
    });
    
    // Log error to console for debugging
    console.error('StreamingChat Error Boundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary">
          <div className="error-content">
            <h2>🚨 Something went wrong</h2>
            <p>The streaming chat encountered an unexpected error.</p>
            <details className="error-details">
              <summary>Error Details</summary>
              <pre>{this.state.error && this.state.error.toString()}</pre>
              <pre>{this.state.errorInfo.componentStack}</pre>
            </details>
            <button 
              className="retry-button"
              onClick={() => this.setState({ hasError: false, error: null, errorInfo: null })}
            >
              Try Again
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

const StreamingChatAssistant = () => {
  const [messages, setMessages] = useState([]);
  const [currentMessage, setCurrentMessage] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  
  // Debug logging to track what's happening
  console.log('🔄 COMPONENT RENDER - inputValue:', inputValue, 'length:', inputValue.length, 'isStreaming:', isStreaming);
  console.log('🔄 RENDER TIMESTAMP:', new Date().toISOString());
  
  useEffect(() => {
    console.log('inputValue changed:', inputValue, 'length:', inputValue.length);
  }, [inputValue]);
  
  useEffect(() => {
    console.log('isStreaming changed:', isStreaming);
  }, [isStreaming]);
  
  useEffect(() => {
    console.log('connectionStatus changed:', connectionStatus);
  }, [connectionStatus]);
  const messagesEndRef = useRef(null);
  const abortControllerRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, currentMessage]);

  const sendMessage = async () => {
    console.log('SEND MESSAGE CALLED - inputValue:', inputValue, 'isStreaming:', isStreaming);
    
    if (!inputValue || !inputValue.trim() || isStreaming) {
      console.log('SEND MESSAGE EARLY RETURN');
      return;
    }

    console.log('SEND MESSAGE PROCEEDING');
    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputValue,
      timestamp: new Date()
    };

    console.log('SETTING MESSAGES AND CLEARING INPUT');
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsStreaming(true);
    setCurrentMessage([]);
    setConnectionStatus('connecting');

    // Create abort controller for this request
    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch('/api/v1/assistant/stream-chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ 
          message: inputValue,
          include_visualizations: true,
          max_response_time: 30
        }),
        signal: abortControllerRef.current.signal
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      setConnectionStatus('connected');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let assistantMessageId = Date.now() + 1;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.type === 'complete') {
                // Move current message to messages and clear current
                setMessages(prev => [...prev, {
                  id: assistantMessageId,
                  type: 'assistant',
                  content: currentMessage,
                  timestamp: new Date()
                }]);
                setCurrentMessage([]);
                setIsStreaming(false);
                setConnectionStatus('disconnected');
                break;
              }

              // Add streaming content to current message
              setCurrentMessage(prev => [...prev, data]);
              
            } catch (e) {
              console.error('Error parsing SSE data:', e);
            }
          }
        }
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        console.log('Request was aborted');
      } else {
        console.error('Streaming error:', error);
        setCurrentMessage(prev => [...prev, {
          type: 'alert',
          content: {
            type: 'error',
            message: `Connection error: ${error.message}`,
            action: 'Please try again'
          }
        }]);
      }
      setIsStreaming(false);
      setConnectionStatus('error');
    }
  };

  const cancelStream = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setIsStreaming(false);
    setConnectionStatus('disconnected');
  };

  // Removed complex handlers - keeping it simple

  const renderContent = (contentItem) => {
    try {
      switch (contentItem.type) {
        case 'text':
          return <div className="message-text">{contentItem.content}</div>;

        case 'metric_card':
          return (
            <StreamingChatErrorBoundary>
              <MetricCards data={contentItem.content} />
            </StreamingChatErrorBoundary>
          );

        case 'chart':
          const { chart_type } = contentItem.content;
          if (chart_type === 'line') {
            return (
              <StreamingChatErrorBoundary>
                <LineChart data={contentItem.content} />
              </StreamingChatErrorBoundary>
            );
          } else if (chart_type === 'donut') {
            return (
              <StreamingChatErrorBoundary>
                <DonutChart data={contentItem.content} />
              </StreamingChatErrorBoundary>
            );
          } else if (chart_type === 'gauge') {
            return (
              <StreamingChatErrorBoundary>
                <GaugeChart data={contentItem.content} />
              </StreamingChatErrorBoundary>
            );
          } else if (chart_type === 'bar') {
            return (
              <StreamingChatErrorBoundary>
                <LineChart data={{...contentItem.content, chart_type: 'bar'}} />
              </StreamingChatErrorBoundary>
            );
          }
          break;

        case 'table':
          return (
            <StreamingChatErrorBoundary>
              <DataTable data={contentItem.content} />
            </StreamingChatErrorBoundary>
          );

        case 'graph':
          return (
            <StreamingChatErrorBoundary>
              <NetworkGraph data={contentItem.content} />
            </StreamingChatErrorBoundary>
          );

        case 'alert':
          return (
            <div className={`alert alert-${contentItem.content.type}`}>
              <div className="alert-message">{contentItem.content.message}</div>
              {contentItem.content.action && (
                <button className="alert-action">{contentItem.content.action}</button>
              )}
            </div>
          );

        case 'progress':
          return (
            <div className="progress-indicator">
              <div className="progress-text">{contentItem.content}</div>
              {contentItem.metadata?.progress && (
                <div className="progress-bar">
                  <div 
                    className="progress-fill" 
                    style={{ width: `${contentItem.metadata.progress}%` }}
                  ></div>
                </div>
              )}
            </div>
          );

        default:
          return <div className="unsupported-content">Unsupported content type: {contentItem.type}</div>;
      }
    } catch (error) {
      console.error('Error rendering content:', error, contentItem);
      return (
        <div className="content-error">
          <div className="error-message">Failed to render content</div>
          <div className="error-type">Type: {contentItem.type}</div>
        </div>
      );
    }
  };

  const getConnectionStatusIcon = () => {
    switch (connectionStatus) {
      case 'connected': return '🟢';
      case 'connecting': return '🟡';
      case 'error': return '🔴';
      default: return '⚪';
    }
  };

  return (
    <StreamingChatErrorBoundary>
      <div className="streaming-chat-container">
        <div className="chat-header">
          <div className="header-content">
            <h1>🤖 Common Assistant</h1>
            <p>Your AI-powered supply chain assistant with rich visualizations</p>
          </div>
          <div className="connection-status">
            <span className="status-icon">{getConnectionStatusIcon()}</span>
            <span className="status-text">{connectionStatus}</span>
          </div>
        </div>

      <div className="messages-area">
        {messages.length === 0 && (
          <div className="welcome-message">
            <h3>Welcome to the Common Assistant!</h3>
            <p>I can help you with:</p>
            <ul>
              <li>📦 Inventory analysis and tracking</li>
              <li>🔍 Transparency and traceability insights</li>
              <li>📊 Yield performance and efficiency metrics</li>
              <li>🏭 Supplier network visualization</li>
              <li>✅ Compliance status and EUDR tracking</li>
            </ul>
            <p>Try asking: "Show me my current inventory" or "What's our transparency score?"</p>
          </div>
        )}

        {messages.map(message => (
          <div key={message.id} className={`message ${message.type}`}>
            <div className="message-avatar">
              {message.type === 'user' ? '👤' : '🤖'}
            </div>
            <div className="message-content">
              {message.type === 'user' ? (
                <div className="message-text">{message.content}</div>
              ) : (
                <div className="rich-content">
                  {message.content.map((item, index) => (
                    <div key={index} className="content-item">
                      {renderContent(item)}
                    </div>
                  ))}
                </div>
              )}
              <div className="message-timestamp">
                {message.timestamp.toLocaleTimeString()}
              </div>
            </div>
          </div>
        ))}

        {/* Current streaming message */}
        {isStreaming && currentMessage.length > 0 && (
          <div className="message assistant streaming">
            <div className="message-avatar">🤖</div>
            <div className="message-content">
              <div className="rich-content">
                {currentMessage.map((item, index) => (
                  <div key={index} className="content-item">
                    {renderContent(item)}
                  </div>
                ))}
              </div>
              <div className="streaming-indicator">
                <div className="typing-dots">
                  <span></span><span></span><span></span>
                </div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input">
        <div style={{ padding: '10px', background: '#f0f0f0', marginBottom: '10px', fontSize: '12px' }}>
          <strong>DEBUG INFO:</strong> inputValue = "{inputValue}" | length = {inputValue.length} | isStreaming = {isStreaming.toString()}
        </div>
        <div className="input-container">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => {
              console.log('INPUT CHANGE EVENT:', e.target.value, 'current inputValue:', inputValue);
              setInputValue(e.target.value);
              console.log('setInputValue called with:', e.target.value);
            }}
            onKeyDown={(e) => {
              console.log('KEY DOWN EVENT:', e.key, 'current inputValue:', inputValue);
              if (e.key === 'Enter') {
                console.log('ENTER PRESSED - calling sendMessage');
                sendMessage();
              }
            }}
            onFocus={() => console.log('INPUT FOCUSED')}
            onBlur={() => console.log('INPUT BLURRED')}
            placeholder="Type your message here..."
          />
          <div className="input-actions">
            {isStreaming ? (
              <button onClick={cancelStream} className="cancel-button">
                Cancel
              </button>
            ) : (
              <button 
                onClick={sendMessage} 
                className="send-button"
              >
                Send
              </button>
            )}
          </div>
        </div>
        
        <div className="input-suggestions">
          <span className="suggestion-label">Try:</span>
          <button 
            className="suggestion-chip"
            onClick={() => setInputValue("Show me my current inventory")}
            disabled={isStreaming}
          >
            📦 Inventory
          </button>
          <button 
            className="suggestion-chip"
            onClick={() => setInputValue("What's our transparency score?")}
            disabled={isStreaming}
          >
            🔍 Transparency
          </button>
          <button 
            className="suggestion-chip"
            onClick={() => setInputValue("Show supplier network")}
            disabled={isStreaming}
          >
            🏭 Suppliers
          </button>
        </div>
      </div>
      </div>
    </StreamingChatErrorBoundary>
  );
};

export default StreamingChatAssistant;
