/**
 * Content script for Google Meet integration
 */

// Listen for messages from background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'updateMetrics') {
    // Update UI if needed
    addDetectionStatusIndicator(message.metrics);
  }
});

/**
 * Add detection status indicator to Google Meet UI
 */
function addDetectionStatusIndicator(metrics) {
  let indicator = document.getElementById('ss-detection-indicator');
  
  if (!indicator) {
    indicator = document.createElement('div');
    indicator.id = 'ss-detection-indicator';
    indicator.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: white;
      border-radius: 8px;
      padding: 10px 15px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      z-index: 10000;
      font-family: 'Segoe UI', sans-serif;
      font-size: 12px;
      min-width: 180px;
    `;
    document.body.appendChild(indicator);
  }
  
  // Update indicator content
  const alertColor = metrics.faceCount > 1 ? '#dc2626' : '#16a34a';
  indicator.innerHTML = `
    <div style="margin-bottom: 6px; font-weight: 600; color: ${alertColor}">
      🔒 Shoulder Surfing Detection
    </div>
    <div style="color: #6b7280; font-size: 11px; line-height: 1.4">
      <div>Faces: <strong>${metrics.faceCount}</strong></div>
      <div>FPS: <strong>${(metrics.fps || 0).toFixed(1)}</strong></div>
      <div>Status: <strong>${metrics.faceCount > 1 ? '⚠️ ALERT' : '✓ SAFE'}</strong></div>
    </div>
  `;
}

// Initialize indicator when page loads
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    console.log('[SS Detection] Initialized on Google Meet');
  });
} else {
  console.log('[SS Detection] Initialized on Google Meet');
}

// Periodically check for threat status
setInterval(() => {
  chrome.runtime.sendMessage({ action: 'getMetrics' }, (response) => {
    if (response) {
      addDetectionStatusIndicator(response.metrics);
    }
  });
}, 1000);
