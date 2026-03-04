import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { Layout } from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Progress } from '../components/ui/progress';
import { MessageSquare, Send, Loader2, Sparkles, RotateCcw } from 'lucide-react';
import { toast } from 'sonner';

export function EstimatorPage() {
  const { organization } = useAuth();
  const [sessions, setSessions] = useState([]);
  const [currentSession, setCurrentSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [completeness, setCompleteness] = useState(0);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (organization?.id) {
      fetchSessions();
    }
  }, [organization?.id]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchSessions = async () => {
    try {
      const response = await api.getEstimatorSessions(organization.id);
      setSessions(response.data);
    } catch (error) {
      console.error('Error fetching sessions:', error);
    }
  };

  const startNewSession = async () => {
    setLoading(true);
    try {
      const response = await api.startEstimatorSession(organization.id);
      setCurrentSession(response.data.session_id);
      setMessages([
        {
          role: 'assistant',
          content: response.data.message,
          timestamp: new Date().toISOString()
        }
      ]);
      setCompleteness(0);
      fetchSessions();
    } catch (error) {
      toast.error('Failed to start session');
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || !currentSession) return;

    const userMessage = {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString()
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setSending(true);

    try {
      const response = await api.sendEstimatorMessage(currentSession, input);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: response.data.message,
          timestamp: new Date().toISOString()
        }
      ]);
      setCompleteness(response.data.data_completeness_score || 0);
    } catch (error) {
      toast.error('Failed to send message');
    } finally {
      setSending(false);
    }
  };

  const loadSession = async (sessionId) => {
    try {
      const response = await api.getEstimatorSession(sessionId);
      setCurrentSession(sessionId);
      setMessages(response.data.messages || []);
      setCompleteness(response.data.data_completeness_score || 0);
    } catch (error) {
      toast.error('Failed to load session');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <Layout>
      <div className="space-y-8 animate-fade-in">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl md:text-4xl font-bold font-['Outfit'] tracking-tight" data-testid="estimator-title">
              Carbon Estimator
            </h1>
            <p className="text-muted-foreground mt-1">
              Chat with AI to estimate your organization's carbon footprint
            </p>
          </div>
          <Button
            onClick={startNewSession}
            disabled={loading}
            className="bg-primary text-primary-foreground hover:bg-primary/90 rounded-full"
            data-testid="new-session-btn"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Sparkles className="w-4 h-4 mr-2" />
            )}
            New Estimate
          </Button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Chat Section */}
          <div className="lg:col-span-3">
            <Card className="bg-card border-border h-[600px] flex flex-col" data-testid="chat-section">
              {/* Progress Bar */}
              {currentSession && (
                <div className="p-4 border-b border-border">
                  <div className="flex items-center justify-between text-sm mb-2">
                    <span>Data Completeness</span>
                    <span className="font-medium">{Math.round(completeness)}%</span>
                  </div>
                  <Progress value={completeness} className="h-2" />
                </div>
              )}

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {currentSession ? (
                  <>
                    {messages.map((msg, index) => (
                      <div
                        key={index}
                        className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                      >
                        <div
                          className={`max-w-[80%] p-4 ${
                            msg.role === 'user' ? 'chat-bubble-user' : 'chat-bubble-assistant'
                          }`}
                        >
                          <p className="whitespace-pre-wrap text-sm">{msg.content}</p>
                        </div>
                      </div>
                    ))}
                    {sending && (
                      <div className="flex justify-start">
                        <div className="chat-bubble-assistant p-4">
                          <Loader2 className="w-5 h-5 animate-spin" />
                        </div>
                      </div>
                    )}
                    <div ref={messagesEndRef} />
                  </>
                ) : (
                  <div className="h-full flex items-center justify-center text-center">
                    <div>
                      <MessageSquare className="w-16 h-16 mx-auto text-muted-foreground/50 mb-4" />
                      <h3 className="text-lg font-medium mb-2">Start a Carbon Estimate</h3>
                      <p className="text-sm text-muted-foreground mb-4">
                        Click "New Estimate" to begin chatting with AI
                      </p>
                      <Button
                        onClick={startNewSession}
                        disabled={loading}
                        variant="outline"
                        className="rounded-full"
                      >
                        <Sparkles className="w-4 h-4 mr-2" />
                        Start Now
                      </Button>
                    </div>
                  </div>
                )}
              </div>

              {/* Input */}
              {currentSession && (
                <div className="p-4 border-t border-border">
                  <div className="flex gap-3">
                    <Input
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyPress={handleKeyPress}
                      placeholder="Type your response..."
                      disabled={sending}
                      className="flex-1"
                      data-testid="chat-input"
                    />
                    <Button
                      onClick={sendMessage}
                      disabled={!input.trim() || sending}
                      className="bg-primary text-primary-foreground hover:bg-primary/90 rounded-full px-6"
                      data-testid="send-btn"
                    >
                      <Send className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              )}
            </Card>
          </div>

          {/* Sessions Sidebar */}
          <div className="lg:col-span-1">
            <Card className="bg-card border-border" data-testid="sessions-sidebar">
              <CardHeader>
                <CardTitle className="text-sm font-medium">Previous Sessions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 max-h-[500px] overflow-y-auto">
                {sessions.length > 0 ? (
                  sessions.map((session) => (
                    <button
                      key={session.id}
                      onClick={() => loadSession(session.session_id)}
                      className={`w-full text-left p-3 rounded-lg transition-colors ${
                        currentSession === session.session_id
                          ? 'bg-primary/20 border border-primary/30'
                          : 'bg-muted/50 hover:bg-muted/70'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-muted-foreground">
                          {new Date(session.created_at).toLocaleDateString()}
                        </span>
                        {session.is_complete && (
                          <span className="text-xs text-primary">Complete</span>
                        )}
                      </div>
                      {session.total_emissions && (
                        <p className="text-sm font-medium mt-1">
                          {session.total_emissions.toLocaleString()} kg CO2e
                        </p>
                      )}
                      <div className="mt-2">
                        <Progress
                          value={session.data_completeness_score || 0}
                          className="h-1"
                        />
                      </div>
                    </button>
                  ))
                ) : (
                  <p className="text-sm text-muted-foreground text-center py-4">
                    No previous sessions
                  </p>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </Layout>
  );
}
