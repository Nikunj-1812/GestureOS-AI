import React, { useState, useEffect, useRef } from 'react';
import { 
  Camera, 
  VideoOff, 
  Cpu, 
  Hand, 
  Sparkles, 
  User, 
  Bell, 
  Settings, 
  LogOut, 
  Play, 
  Square, 
  RotateCcw, 
  Activity,
  Layers,
  ChevronRight,
  TrendingUp,
  Sliders,
  MousePointer
} from 'lucide-react';

interface TelemetryData {
  fps: number;
  hands: number;
  gesture: string;
  confidence: number;
  camera_status: string;
  frame: string | null;
  cursor_x?: number;
  cursor_y?: number;
  tracking_state?: string;
}

interface EventLog {
  id: string;
  timestamp: string;
  gesture: string;
  confidence: number;
  action: string;
}

export default function App() {
  const [fps, setFps] = useState<number>(0);
  const [hands, setHands] = useState<number>(0);
  const [gesture, setGesture] = useState<string>('None');
  const [confidence, setConfidence] = useState<number>(0);
  const [cameraStatus, setCameraStatus] = useState<string>('Disconnected');
  const [frame, setFrame] = useState<string | null>(null);
  
  const [socketStatus, setSocketStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');
  const [events, setEvents] = useState<EventLog[]>([]);
  const [activeMenu, setActiveMenu] = useState<string>('dashboard');
  const [isResetting, setIsResetting] = useState<boolean>(false);
  const [isCameraLoading, setIsCameraLoading] = useState<boolean>(false);

  // Virtual Mouse States
  const [virtualMouseEnabled, setVirtualMouseEnabled] = useState<boolean>(false);
  const [virtualMouseSensitivity, setVirtualMouseSensitivity] = useState<number>(1.5);
  const [virtualMouseDeadZone, setVirtualMouseDeadZone] = useState<number>(0.15);
  const [virtualMouseSmoothing, setVirtualMouseSmoothing] = useState<number>(0.20);
  
  const [cursorX, setCursorX] = useState<number>(0);
  const [cursorY, setCursorY] = useState<number>(0);
  const [trackingState, setTrackingState] = useState<string>('Disabled');

  // Switches State
  const [showLandmarks, setShowLandmarks] = useState<boolean>(true);
  const [showConnections, setShowConnections] = useState<boolean>(true);
  const [showBoundingBox, setShowBoundingBox] = useState<boolean>(true);
  const [showFingerStates, setShowFingerStates] = useState<boolean>(true);
  const [showDistanceMeter, setShowDistanceMeter] = useState<boolean>(true);
  const [showDebugPanel, setShowDebugPanel] = useState<boolean>(true);
  const [showHud, setShowHud] = useState<boolean>(true);

  const prevGestureRef = useRef<string>('None');
  const socketRef = useRef<WebSocket | null>(null);
  const eventIdCounterRef = useRef<number>(0);

  // Connect to the Python FastAPI WebSocket backend
  useEffect(() => {
    const connectWS = () => {
      setSocketStatus('connecting');
      const wsUrl = `ws://${window.location.hostname || '127.0.0.1'}:8000/ws`;
      console.log(`Connecting to WebSocket: ${wsUrl}`);
      
      const ws = new WebSocket(wsUrl);
      socketRef.current = ws;

      ws.onopen = () => {
        setSocketStatus('connected');
        console.log('WebSocket connection established');
      };

      ws.onmessage = (event) => {
        try {
          const data: TelemetryData = JSON.parse(event.data);
          setFps(data.fps);
          setHands(data.hands);
          setGesture(data.gesture);
          setConfidence(data.confidence);
          setCameraStatus(data.camera_status);
          setFrame(data.frame);
          setCursorX(data.cursor_x || 0);
          setCursorY(data.cursor_y || 0);
          setTrackingState(data.tracking_state || 'Disabled');

          // If gesture changed and is not None or unknown, add to recent events
          if (data.gesture !== prevGestureRef.current) {
            if (data.gesture && data.gesture !== 'None' && data.gesture !== 'unknown') {
              const timeString = new Date().toLocaleTimeString();
              eventIdCounterRef.current += 1;
              const newEvent: EventLog = {
                id: `${Date.now()}-${eventIdCounterRef.current}`,
                timestamp: timeString,
                gesture: data.gesture,
                confidence: data.confidence,
                action: `Triggered mapped shortcut for [${data.gesture}]`
              };
              setEvents(prev => [newEvent, ...prev].slice(0, 50));
            }
            prevGestureRef.current = data.gesture;
          }
        } catch (err) {
          console.error('Error decoding WebSocket JSON payload:', err);
        }
      };

      ws.onclose = () => {
        setSocketStatus('disconnected');
        console.log('WebSocket connection lost, retrying in 3 seconds...');
        setTimeout(connectWS, 3000);
      };

      ws.onerror = (error) => {
        console.error('WebSocket encountered an error:', error);
      };
    };

    connectWS();

    // Fetch initial switches configuration from backend
    fetch('http://127.0.0.1:8000/api/settings')
      .then(res => res.json())
      .then(data => {
        setShowLandmarks(data.show_landmarks);
        setShowConnections(data.show_connections);
        setShowBoundingBox(data.show_bounding_box);
        setShowFingerStates(data.show_finger_states);
        setShowDistanceMeter(data.show_distance_meter);
        setShowDebugPanel(data.show_debug_panel);
        setShowHud(data.show_hud);

        setVirtualMouseEnabled(data.virtual_mouse_enabled);
        setVirtualMouseSensitivity(data.virtual_mouse_sensitivity);
        setVirtualMouseDeadZone(data.virtual_mouse_dead_zone);
        setVirtualMouseSmoothing(data.virtual_mouse_smoothing);
      })
      .catch(err => console.error('Error loading config settings:', err));

    return () => {
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, []);

  const logSystemEvent = (msg: string) => {
    const timeString = new Date().toLocaleTimeString();
    eventIdCounterRef.current += 1;
    const newEvent: EventLog = {
      id: `${Date.now()}-${eventIdCounterRef.current}`,
      timestamp: timeString,
      gesture: 'System',
      confidence: 1.0,
      action: msg
    };
    setEvents(prev => [newEvent, ...prev].slice(0, 50));
  };

  // REST API Actions
  const handleStartCamera = async () => {
    setIsCameraLoading(true);
    logSystemEvent("Camera stream start requested.");
    try {
      const res = await fetch('http://127.0.0.1:8000/api/camera/start', { method: 'POST' });
      const data = await res.json();
      if (data.status === 'success') {
        setCameraStatus('Connected');
        logSystemEvent("Camera stream started.");
      }
    } catch (err) {
      console.error('Error starting camera:', err);
      logSystemEvent("Failed to start camera.");
    } finally {
      setIsCameraLoading(false);
    }
  };

  const handleStopCamera = async () => {
    setIsCameraLoading(true);
    logSystemEvent("Camera stream stop requested.");
    try {
      await fetch('http://127.0.0.1:8000/api/camera/stop', { method: 'POST' });
      setCameraStatus('Disconnected');
      setFrame(null);
      setFps(0);
      setHands(0);
      setGesture('None');
      setConfidence(0);
      logSystemEvent("Camera stream stopped.");
    } catch (err) {
      console.error('Error stopping camera:', err);
      logSystemEvent("Failed to stop camera.");
    } finally {
      setIsCameraLoading(false);
    }
  };

  const handleResetTracking = async () => {
    setIsResetting(true);
    logSystemEvent("Reset tracking requested.");
    try {
      await fetch('http://127.0.0.1:8000/api/camera/reset', { method: 'POST' });
      setEvents([]);
      prevGestureRef.current = 'None';
      logSystemEvent("Tracking reset complete.");
    } catch (err) {
      console.error('Error resetting tracking:', err);
      logSystemEvent("Failed to reset tracking.");
    } finally {
      setTimeout(() => setIsResetting(false), 800);
    }
  };

  const updateSetting = async (key: string, val: boolean | number) => {
    try {
      await fetch('http://127.0.0.1:8000/api/settings/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ [key]: val })
      });
    } catch (err) {
      console.error('Error updating switch setting:', err);
    }
  };

  // Format confidence display based on current gesture state
  const formatConfidence = () => {
    if (gesture === 'None' || gesture === 'unknown' || gesture === 'No Model' || hands === 0) {
      return '0%';
    }
    return `${(confidence * 100).toFixed(0)}%`;
  };

  return (
    <div className="flex h-screen bg-[#080710] font-sans antialiased text-gray-200 overflow-hidden">
      
      {/* Left Sidebar */}
      <aside className="w-72 glass-panel border-r border-glass-border flex flex-col justify-between h-full z-10">
        <div>
          {/* Logo Section */}
          <div className="flex items-center gap-3 px-6 py-6 border-b border-glass-border justify-center">
            <div className="p-2.5 bg-blue-500/10 rounded-xl border border-blue-500/20 text-accent-blue animate-pulse-slow">
              <Hand className="w-6 h-6 stroke-[2]" />
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-wider bg-gradient-to-r from-white via-gray-200 to-gray-400 bg-clip-text text-transparent">
                GestureOS
              </h1>
              <p className="text-[10px] text-gray-500 uppercase tracking-widest font-semibold">Intelligence Edition</p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="px-4 py-6 space-y-2">
            {[
              { id: 'dashboard', name: 'Dashboard', icon: Layers },
              { id: 'mouse', name: 'Virtual Mouse', icon: MousePointer },
              { id: 'shortcuts', name: 'Gestures Map', icon: Sliders },
              { id: 'analytics', name: 'Real-time Metrics', icon: TrendingUp },
              { id: 'settings', name: 'System Settings', icon: Settings }
            ].map((item) => {
              const Icon = item.icon;
              const isActive = activeMenu === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    setActiveMenu(item.id);
                    logSystemEvent(`Navigated to page: ${item.name}`);
                  }}
                  className={`w-full flex items-center justify-between px-4 py-3.5 rounded-xl transition-all duration-300 group ${
                    isActive 
                      ? 'bg-blue-600/20 border border-blue-500/30 text-white font-medium shadow-md shadow-blue-500/5' 
                      : 'text-gray-400 hover:text-white hover:bg-white/5 border border-transparent'
                  }`}
                >
                  <div className="flex items-center gap-3.5">
                    <Icon className={`w-5 h-5 transition-transform duration-300 group-hover:scale-110 ${
                      isActive ? 'text-accent-blue' : 'text-gray-400 group-hover:text-white'
                    }`} />
                    <span className="text-sm tracking-wide">{item.name}</span>
                  </div>
                  <ChevronRight className={`w-4 h-4 opacity-0 transition-all duration-300 -translate-x-2 ${
                    isActive ? 'opacity-100 translate-x-0 text-accent-blue' : 'group-hover:opacity-50 group-hover:translate-x-0'
                  }`} />
                </button>
              );
            })}
          </nav>
        </div>

        {/* Sidebar Footer */}
        <div className="p-4 border-t border-glass-border">
          <div className="glass-card rounded-xl p-4 flex flex-col gap-3">
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-400 font-medium">Core Pipeline:</span>
              <span className="text-accent-green flex items-center gap-1.5 font-semibold">
                <span className="w-1.5 h-1.5 rounded-full bg-accent-green animate-ping" />
                Active
              </span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-400 font-medium">WS Backend:</span>
              <span className={`flex items-center gap-1.5 font-semibold ${
                socketStatus === 'connected' ? 'text-accent-blue' : 'text-amber-500 animate-pulse'
              }`}>
                <span className={`w-1.5 h-1.5 rounded-full ${
                  socketStatus === 'connected' ? 'bg-accent-blue' : 'bg-amber-500'
                }`} />
                {socketStatus === 'connected' ? 'Connected' : socketStatus === 'connecting' ? 'Connecting...' : 'Offline'}
              </span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Panel Content Area */}
      <main className="flex-1 flex flex-col h-full overflow-hidden bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-blue-950/15 via-[#080710] to-[#080710]">
        
        {/* Responsive Top Header Row */}
        <header className="h-20 border-b border-glass-border px-8 flex items-center justify-between backdrop-blur-md z-10 shrink-0">
          <div>
            <h2 className="text-xl font-bold tracking-wide text-white">
              {activeMenu === 'dashboard' ? 'System Monitor' : activeMenu === 'mouse' ? 'Virtual Mouse Monitor' : 'System Configuration'}
            </h2>
            <p className="text-xs text-gray-400 mt-0.5">
              {activeMenu === 'dashboard' 
                ? 'Telemetry overview and input gesture mapping controls.' 
                : activeMenu === 'mouse' 
                ? 'Real-time mouse tracking coordinates, status, and settings.' 
                : 'Calibrate input settings and device thresholds.'}
            </p>
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-400 font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              Engine Online
            </div>

            <span className="w-px h-6 bg-glass-border hidden md:inline-block" />

            <button className="p-2.5 rounded-xl glass-card text-gray-400 hover:text-white relative group">
              <Bell className="w-5 h-5 transition-transform group-hover:scale-105" />
              <span className="absolute top-1.5 right-1.5 w-2.5 h-2.5 bg-blue-500 rounded-full border-2 border-background" />
            </button>

            <button className="p-2.5 rounded-xl glass-card text-gray-400 hover:text-white group">
              <Settings className="w-5 h-5 transition-transform duration-300 group-hover:rotate-45" />
            </button>

            <div className="flex items-center gap-3 px-3 py-1.5 rounded-xl glass-card border border-glass-border text-left select-none">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white font-bold text-sm shadow-md shadow-blue-500/10">
                <User className="w-4 h-4" />
              </div>
              <div className="hidden sm:block">
                <p className="text-xs font-semibold text-white">Operator</p>
                <p className="text-[10px] text-gray-400">Admin Role</p>
              </div>
            </div>

            <button 
              onClick={handleStopCamera}
              className="p-2.5 rounded-xl bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 hover:border-red-500/30 text-red-400 hover:text-red-300 transition-all duration-300 group"
              title="Stop Engine"
            >
              <LogOut className="w-5 h-5 transition-transform group-hover:translate-x-0.5" />
            </button>
          </div>
        </header>

        {/* Outer scrollable dashboard view */}
        <div className="flex-1 overflow-y-auto p-8 scrollbar-thin">
          <div className="max-w-6xl mx-auto space-y-6">
            
            {activeMenu === 'dashboard' ? (
              <>
                {/* Status Cards Section */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
                  
                  {/* FPS Card */}
                  <div className="glass-card p-5 rounded-2xl flex items-center gap-4 relative overflow-hidden group">
                    <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                    <div className="p-3 bg-blue-500/10 rounded-xl border border-blue-500/20 text-accent-blue">
                      <Activity className="w-6 h-6" />
                    </div>
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">Frames Per Second</p>
                      <p className="text-2xl font-bold text-white mt-1 font-mono tracking-tight">
                        {fps > 0 ? fps : '0.0'}
                      </p>
                    </div>
                  </div>

                  {/* Hands Detected Card */}
                  <div className="glass-card p-5 rounded-2xl flex items-center gap-4 relative overflow-hidden group">
                    <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                    <div className="p-3 bg-indigo-500/10 rounded-xl border border-indigo-500/20 text-accent-purple">
                      <Hand className="w-6 h-6" />
                    </div>
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">Hands Tracked</p>
                      <p className="text-2xl font-bold text-white mt-1 font-mono tracking-tight">
                        {hands}
                      </p>
                    </div>
                  </div>

                  {/* Current Gesture Card */}
                  <div className="glass-card p-5 rounded-2xl flex items-center gap-4 relative overflow-hidden group">
                    <div className="absolute inset-0 bg-gradient-to-br from-violet-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                    <div className="p-3 bg-violet-500/10 rounded-xl border border-violet-500/20 text-purple-400">
                      <Sparkles className="w-6 h-6" />
                    </div>
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">Current Gesture</p>
                      <div className="flex items-baseline gap-2 mt-1">
                        <p className="text-2xl font-bold text-white tracking-tight capitalize">
                          {gesture === 'None' || gesture === 'unknown' ? 'Idle' : gesture}
                        </p>
                        <span className="text-xs text-gray-500 font-mono">({formatConfidence()})</span>
                      </div>
                    </div>
                  </div>

                  {/* Camera Status Card */}
                  <div className="glass-card p-5 rounded-2xl flex items-center gap-4 relative overflow-hidden group">
                    <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                    <div className={`p-3 rounded-xl border transition-colors ${
                      cameraStatus === 'Connected' 
                        ? 'bg-emerald-500/10 border-emerald-500/20 text-accent-green' 
                        : 'bg-zinc-500/10 border-zinc-500/20 text-gray-400'
                    }`}>
                      {cameraStatus === 'Connected' ? <Camera className="w-6 h-6" /> : <VideoOff className="w-6 h-6" />}
                    </div>
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">Camera State</p>
                      <p className={`text-2xl font-bold mt-1 tracking-tight ${
                        cameraStatus === 'Connected' ? 'text-accent-green' : 'text-gray-400'
                      }`}>
                        {cameraStatus}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Layout Main Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  
                  {/* Camera Feed Preview Container (Left 2 columns) */}
                  <div className="lg:col-span-2 flex flex-col gap-4">
                    <div className="glass-card rounded-2xl p-4 flex flex-col h-[480px] justify-between relative group overflow-hidden">
                      <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 opacity-20" />
                      
                      {/* Top Bar for camera info */}
                      <div className="flex items-center justify-between pb-3 border-b border-glass-border">
                        <div className="flex items-center gap-2 text-sm">
                          <Camera className="w-4 h-4 text-accent-blue" />
                          <span className="font-semibold text-gray-200">Device Stream Input</span>
                        </div>
                        <div className="flex items-center gap-1.5 text-xs text-gray-400">
                          <span className={`w-1.5 h-1.5 rounded-full ${
                            cameraStatus === 'Connected' ? 'bg-accent-green animate-ping' : 'bg-red-400'
                          }`} />
                          {cameraStatus === 'Connected' ? 'Streaming live' : 'Offline'}
                        </div>
                      </div>

                      {/* Centered Camera Stream Container with aspect ratio matching (no stretching) */}
                      <div className="flex-1 flex items-center justify-center bg-black/40 rounded-xl overflow-hidden border border-glass-border relative mt-3">
                        {cameraStatus === 'Connected' && frame ? (
                          <img 
                            src={frame} 
                            alt="Camera Feed" 
                            className="w-full h-full object-contain rounded-xl"
                          />
                        ) : (
                          <div className="flex flex-col items-center justify-center p-8 text-center max-w-sm">
                            <div className="w-16 h-16 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-gray-500 mb-4 animate-pulse">
                              <VideoOff className="w-8 h-8" />
                            </div>
                            <h4 className="text-white font-medium mb-1">Camera Stream Inactive</h4>
                            <p className="text-xs text-gray-400 leading-relaxed">
                              To analyze hand geometry and process shortcuts, please launch the camera using the Quick Actions panel below.
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Sidebar Cards (Right 1 column) */}
                  <div className="flex flex-col gap-6">
                    
                    {/* Quick Actions Panel */}
                    <div className="glass-card rounded-2xl p-5 flex flex-col justify-between">
                      <div>
                        <h3 className="text-sm font-bold uppercase tracking-wider text-gray-400 flex items-center gap-2">
                          <Sliders className="w-4 h-4 text-accent-purple" />
                          Quick Actions
                        </h3>
                        <p className="text-xs text-gray-500 mt-1 mb-4">Immediate system state triggers.</p>
                      </div>
                      
                      <div className="space-y-3">
                        <button
                          onClick={handleStartCamera}
                          disabled={cameraStatus === 'Connected' || isCameraLoading}
                          className="w-full flex items-center justify-center gap-2.5 px-4 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 disabled:from-zinc-800 disabled:to-zinc-800 disabled:border-zinc-700 disabled:opacity-50 text-white font-semibold rounded-xl transition-all duration-300 shadow-lg shadow-blue-500/10 border border-blue-500/30 active:scale-98"
                        >
                          <Play className="w-4 h-4 fill-white" />
                          Start Camera
                        </button>
                        
                        <button
                          onClick={handleStopCamera}
                          disabled={cameraStatus !== 'Connected' || isCameraLoading}
                          className="w-full flex items-center justify-center gap-2.5 px-4 py-3 bg-white/5 hover:bg-red-500/10 hover:text-red-400 border border-glass-border hover:border-red-500/25 disabled:opacity-50 disabled:hover:bg-white/5 disabled:hover:text-gray-400 text-gray-300 font-semibold rounded-xl transition-all duration-300 active:scale-98"
                        >
                          <Square className="w-4 h-4" />
                          Stop Camera
                        </button>

                        <button
                          onClick={handleResetTracking}
                          disabled={isResetting}
                          className="w-full flex items-center justify-center gap-2.5 px-4 py-3 bg-white/5 hover:bg-white/10 border border-glass-border disabled:opacity-50 text-gray-300 font-semibold rounded-xl transition-all duration-300 active:scale-98"
                        >
                          <RotateCcw className={`w-4 h-4 ${isResetting ? 'animate-spin' : ''}`} />
                          Reset Tracking
                        </button>
                      </div>
                    </div>

                    {/* Display Settings Switches */}
                    <div className="glass-card rounded-2xl p-5">
                      <h3 className="text-sm font-bold uppercase tracking-wider text-gray-400 flex items-center gap-2">
                        <Sliders className="w-4 h-4 text-accent-blue" />
                        Display Settings
                      </h3>
                      <p className="text-xs text-gray-500 mt-1 mb-4">Toggle live stream visual overlays.</p>
                      
                      <div className="grid grid-cols-2 gap-y-3.5 gap-x-2 text-[11px]">
                        {[
                          { id: 'show_landmarks', label: 'Landmarks', value: showLandmarks, setter: setShowLandmarks },
                          { id: 'show_connections', label: 'Connections', value: showConnections, setter: setShowConnections },
                          { id: 'show_bounding_box', label: 'Bounding Box', value: showBoundingBox, setter: setShowBoundingBox },
                          { id: 'show_finger_states', label: 'Finger States', value: showFingerStates, setter: setShowFingerStates },
                          { id: 'show_distance_meter', label: 'Distance Meter', value: showDistanceMeter, setter: setShowDistanceMeter },
                          { id: 'show_debug_panel', label: 'Debug Panel', value: showDebugPanel, setter: setShowDebugPanel },
                          { id: 'show_hud', label: 'HUD Overlay', value: showHud, setter: setShowHud },
                        ].map(item => (
                          <label key={item.id} className="flex items-center gap-2.5 cursor-pointer text-gray-300 hover:text-white select-none">
                            <input
                              type="checkbox"
                              checked={item.value}
                              onChange={(e) => {
                                const checked = e.target.checked;
                                item.setter(checked);
                                updateSetting(item.id, checked);
                              }}
                              className="w-3.5 h-3.5 rounded border-glass-border bg-[#080710] text-blue-500 focus:ring-blue-500/40 cursor-pointer"
                            />
                            <span>{item.label}</span>
                          </label>
                        ))}
                      </div>
                    </div>

                    {/* Recent Activity Logs Panel */}
                    <div className="glass-card rounded-2xl p-5 flex flex-col flex-1 min-h-[220px] justify-between">
                      <div>
                        <h3 className="text-sm font-bold uppercase tracking-wider text-gray-400 flex items-center gap-2">
                          <Cpu className="w-4 h-4 text-accent-blue" />
                          Activity Log
                        </h3>
                        <p className="text-xs text-gray-500 mt-1 mb-4">Real-time prediction event stream.</p>
                      </div>

                      <div className="flex-1 overflow-y-auto bg-black/60 rounded-xl border border-glass-border p-3 font-mono text-[11px] leading-relaxed scrollbar-thin text-blue-400/90 h-[120px]">
                        {events.length === 0 ? (
                          <div className="text-gray-600 flex items-center justify-center h-full">
                            <span>Waiting for events...</span>
                          </div>
                        ) : (
                          <div className="space-y-2.5">
                            {events.map((evt) => (
                              <div key={evt.id} className="border-b border-white/5 pb-1.5 last:border-0 last:pb-0">
                                 <div className="flex items-center justify-between text-gray-500 font-semibold mb-0.5">
                                  <span>[{evt.timestamp}]</span>
                                  {evt.gesture !== 'System' && <span className="text-accent-green">{(evt.confidence * 100).toFixed(0)}%</span>}
                                </div>
                                <div className="text-white">
                                  {evt.gesture === 'System' ? (
                                    <span>Event: <span className="text-accent-purple font-bold">System Log</span></span>
                                  ) : (
                                    <span>Gesture: <span className="capitalize text-accent-blue font-bold">{evt.gesture}</span></span>
                                  )}
                                </div>
                                <div className="text-gray-400 text-[10px]">
                                  {evt.action}
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>

                  </div>
                </div>
              </>
            ) : activeMenu === 'mouse' ? (
              <>
                {/* Hero Header Section */}
                <div className="glass-panel rounded-3xl p-6 flex flex-col md:flex-row md:items-center justify-between border border-glass-border relative overflow-hidden">
                  <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 opacity-20" />
                  <div>
                    <h2 className="text-2xl font-bold tracking-wide text-white">Virtual Mouse Controls</h2>
                    <p className="text-xs text-gray-400 mt-1 max-w-xl">
                      Control your system cursor in real-time using your index finger. Calibrate tracking properties below.
                    </p>
                  </div>
                  <div className="mt-4 md:mt-0">
                    <span className={`px-4 py-2 rounded-full text-xs font-semibold border ${
                      virtualMouseEnabled 
                        ? 'bg-emerald-500/10 border-emerald-500/20 text-accent-green' 
                        : 'bg-zinc-500/10 border-zinc-500/20 text-gray-400'
                    }`}>
                      {virtualMouseEnabled ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                </div>

                {/* Two-Column Main Content Layout */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {/* Left: Camera Feed Preview (2 Columns) */}
                  <div className="lg:col-span-2 flex flex-col gap-4">
                    <div className="glass-card rounded-2xl p-4 flex flex-col h-[480px] justify-between relative group overflow-hidden">
                      <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 opacity-20" />
                      
                      <div className="flex items-center justify-between pb-3 border-b border-glass-border">
                        <div className="flex items-center gap-2 text-sm">
                          <Camera className="w-4 h-4 text-accent-blue" />
                          <span className="font-semibold text-gray-200">Device Stream Input</span>
                        </div>
                        <div className="flex items-center gap-1.5 text-xs text-gray-400">
                          <span className={`w-1.5 h-1.5 rounded-full ${
                            cameraStatus === 'Connected' ? 'bg-accent-green animate-ping' : 'bg-red-400'
                          }`} />
                          {cameraStatus === 'Connected' ? 'Streaming live' : 'Offline'}
                        </div>
                      </div>

                      {/* Centered Camera Stream */}
                      <div className="flex-1 flex items-center justify-center bg-black/40 rounded-xl overflow-hidden border border-glass-border relative mt-3">
                        {cameraStatus === 'Connected' && frame ? (
                          <img 
                            src={frame} 
                            alt="Camera Feed" 
                            className="w-full h-full object-contain rounded-xl"
                          />
                        ) : (
                          <div className="flex flex-col items-center justify-center p-8 text-center max-w-sm">
                            <div className="w-16 h-16 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-gray-500 mb-4 animate-pulse">
                              <VideoOff className="w-8 h-8" />
                            </div>
                            <h4 className="text-white font-medium mb-1">Camera Stream Inactive</h4>
                            <p className="text-xs text-gray-400 leading-relaxed">
                              To analyze hand geometry and process mouse tracking, please launch the camera using the Quick Actions panel or back on the Dashboard.
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Right: Telemetry & Controls Panel (1 Column) */}
                  <div className="flex flex-col gap-6">
                    {/* Telemetry Dashboard Card */}
                    <div className="glass-card rounded-2xl p-5 flex flex-col justify-between">
                      <div>
                        <h3 className="text-sm font-bold uppercase tracking-wider text-gray-400 flex items-center gap-2">
                          <Activity className="w-4 h-4 text-accent-blue" />
                          Telemetry Dashboard
                        </h3>
                        <p className="text-xs text-gray-500 mt-1 mb-4">Real-time coordinates and performance.</p>
                      </div>

                      <div className="space-y-4">
                        <div className="flex justify-between items-center text-sm border-b border-glass-border pb-2">
                          <span className="text-gray-400">Cursor Coordinates</span>
                          <span className="font-mono font-bold text-white">
                            {trackingState === 'Tracking' ? `X: ${cursorX} , Y: ${cursorY}` : '-- , --'}
                          </span>
                        </div>
                        <div className="flex justify-between items-center text-sm border-b border-glass-border pb-2">
                          <span className="text-gray-400">Tracking State</span>
                          <span className={`font-semibold ${
                            trackingState === 'Tracking' ? 'text-accent-green' : trackingState === 'Disabled' ? 'text-gray-400' : 'text-rose-400'
                          }`}>
                            {trackingState}
                          </span>
                        </div>
                        <div className="flex justify-between items-center text-sm">
                          <span className="text-gray-400">Stream FPS</span>
                          <span className="font-mono font-bold text-white">
                            {fps > 0 ? `${fps.toFixed(1)} FPS` : '-- FPS'}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Tracking Settings Card */}
                    <div className="glass-card rounded-2xl p-5">
                      <h3 className="text-sm font-bold uppercase tracking-wider text-gray-400 flex items-center gap-2">
                        <Sliders className="w-4 h-4 text-accent-purple" />
                        Tracking Settings
                      </h3>
                      <p className="text-xs text-gray-500 mt-1 mb-4">Configure virtual mouse parameters.</p>

                      <div className="space-y-5">
                        {/* Enable Toggle Switch */}
                        <label className="flex items-center justify-between cursor-pointer group">
                          <span className="text-sm font-semibold text-gray-300 group-hover:text-white">Enable Virtual Mouse</span>
                          <div className="relative">
                            <input 
                              type="checkbox" 
                              checked={virtualMouseEnabled} 
                              onChange={(e) => {
                                const checked = e.target.checked;
                                setVirtualMouseEnabled(checked);
                                updateSetting('virtual_mouse_enabled', checked);
                                logSystemEvent(`Virtual Mouse set to: ${checked ? 'Enabled' : 'Disabled'}`);
                              }}
                              className="sr-only peer" 
                            />
                            <div className="w-11 h-6 bg-zinc-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                          </div>
                        </label>

                        {/* Sensitivity Slider */}
                        <div className="space-y-2">
                          <div className="flex justify-between text-xs">
                            <span className="text-gray-400">Sensitivity</span>
                            <span className="text-white font-mono">{virtualMouseSensitivity.toFixed(2)}x</span>
                          </div>
                          <input 
                            type="range" 
                            min="0.5" 
                            max="3.0" 
                            step="0.1"
                            value={virtualMouseSensitivity} 
                            onChange={(e) => {
                              const val = parseFloat(e.target.value);
                              setVirtualMouseSensitivity(val);
                              updateSetting('virtual_mouse_sensitivity', val);
                            }}
                            className="w-full h-1.5 bg-zinc-700 rounded-lg appearance-none cursor-pointer accent-blue-500" 
                          />
                        </div>

                        {/* Dead Zone Slider */}
                        <div className="space-y-2">
                          <div className="flex justify-between text-xs">
                            <span className="text-gray-400">Dead Zone Padding</span>
                            <span className="text-white font-mono">{Math.round(virtualMouseDeadZone * 100)}%</span>
                          </div>
                          <input 
                            type="range" 
                            min="0.05" 
                            max="0.30" 
                            step="0.01"
                            value={virtualMouseDeadZone} 
                            onChange={(e) => {
                              const val = parseFloat(e.target.value);
                              setVirtualMouseDeadZone(val);
                              updateSetting('virtual_mouse_dead_zone', val);
                            }}
                            className="w-full h-1.5 bg-zinc-700 rounded-lg appearance-none cursor-pointer accent-blue-500" 
                          />
                        </div>

                        {/* Smoothing Slider */}
                        <div className="space-y-2">
                          <div className="flex justify-between text-xs">
                            <span className="text-gray-400">Smoothing (Response)</span>
                            <span className="text-white font-mono">{virtualMouseSmoothing.toFixed(2)}</span>
                          </div>
                          <input 
                            type="range" 
                            min="0.05" 
                            max="0.50" 
                            step="0.02"
                            value={virtualMouseSmoothing} 
                            onChange={(e) => {
                              const val = parseFloat(e.target.value);
                              setVirtualMouseSmoothing(val);
                              updateSetting('virtual_mouse_smoothing', val);
                            }}
                            className="w-full h-1.5 bg-zinc-700 rounded-lg appearance-none cursor-pointer accent-blue-500" 
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </>
            ) : (
              <div className="glass-card rounded-2xl p-8 text-center text-gray-400">
                <p>This page is currently under construction. Please use the Dashboard or Virtual Mouse navigation links.</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
