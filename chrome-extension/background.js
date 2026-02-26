/**
 * Background service worker for shoulder surfing detection extension
 */

// Socket connection to detect server
let detectionSocket = null;
let isConnected = false;
let metrics = {
  faceCount: 0,
  fps: 0,
  latency: 0
};

/**
 * Connect to local detection server
 */
function connectToDetectionServer() {
  const PORT = 8000;
  const URL = `ws://localhost:${PORT}/socket.io/?transport=websocket`;
  
  try {
    detectionSocket = new WebSocket(URL);
    
    detectionSocket.onopen = () => {
      console.log('[SS Detection] Connected to detection server');
      isConnected = true;
      chrome.action.setBadgeBackgroundColor({color: '#22c55e'});
      chrome.action.setBadgeText({text: '✓'});
    };
    
    detectionSocket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleDetectionMessage(data);
      } catch (e) {
        console.error('[SS Detection] Error parsing message:', e);
      }
    };
    
    detectionSocket.onerror = (error) => {
      console.error('[SS Detection] WebSocket error:', error);
      isConnected = false;
      chrome.action.setBadgeBackgroundColor({color: '#ef4444'});
      chrome.action.setBadgeText({text: '✗'});
    };
    
    detectionSocket.onclose = () => {
      console.log('[SS Detection] Disconnected from detection server');
      isConnected = false;
      chrome.action.setBadgeBackgroundColor({color: '#ef4444'});
      chrome.action.setBadgeText({text: '✗'});
      
      // Attempt to reconnect after 3 seconds
      setTimeout(connectToDetectionServer, 3000);
    };
  } catch (e) {
    console.error('[SS Detection] Connection error:', e);
  }
}

/**
 * Handle detection message from server
 */
function handleDetectionMessage(data) {
  const { type, payload } = data;
  
  switch (type) {
    case 'detection_update':
      metrics = {
        faceCount: payload.face_count || 0,
        fps: payload.fps || 0,
        latency: payload.latency || 0
      };
      break;
    
    case 'threat_detected':
      handleThreatDetected(payload);
      break;
    
    case 'blur_activated':
      console.log('[SS Detection] Screen blur activated');
      break;
    
    case 'blur_deactivated':
      console.log('[SS Detection] Screen blur deactivated');
      break;
  }
  
  // Update popup with new metrics
  broadcast({
    action: 'updateMetrics',
    metrics: metrics,
    lastAlert: data.type === 'threat_detected' ? {
      timestamp: Date.now(),
      faceCount: payload.face_count
    } : null
  });
}

/**
 * Handle threat detected
 */
function handleThreatDetected(payload) {
  // Show browser notification
  chrome.notifications.create('threat_detected', {
    type: 'basic',
    iconUrl: 'images/icon-128.png',
    title: 'Shoulder Surfing Threat Detected!',
    message: `Unauthorized observer detected in video. ${payload.face_count} faces detected.`,
    priority: 2
  });
  
  // Log detection event
  console.log('[SS Detection] Threat detected:', payload);
}

/**
 * Broadcast message to all tabs
 */
function broadcast(message) {
  chrome.tabs.query({}, (tabs) => {
    tabs.forEach(tab => {
      chrome.tabs.sendMessage(tab.id, message).catch(() => {
        // Tab might not be ready to receive messages
      });
    });
  });
}

/**
 * Handle messages from content scripts and popup
 */
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  switch (message.action) {
    case 'toggleBlur':
      if (isConnected && detectionSocket) {
        detectionSocket.send(JSON.stringify({
          type: 'toggle_blur',
          payload: { enabled: message.enabled }
        }));
      }
      break;
    
    case 'toggleGaze':
      if (isConnected && detectionSocket) {
        detectionSocket.send(JSON.stringify({
          type: 'toggle_gaze',
          payload: { enabled: message.enabled }
        }));
      }
      break;
    
    case 'getMetrics':
      sendResponse({ metrics });
      break;
  }
});

/**
 * When extension is installed or loaded
 */
chrome.runtime.onInstalled.addListener(() => {
  console.log('[SS Detection] Extension installed/loaded');
  connectToDetectionServer();
});

/**
 * Startup when browser starts
 */
chrome.runtime.onStartup?.(() => {
  connectToDetectionServer();
});

// Initial connection attempt
connectToDetectionServer();
