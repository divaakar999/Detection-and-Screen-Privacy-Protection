/**
 * Popup script for the Shoulder Surfing Detection Chrome Extension
 */

// DOM Elements
const statusIndicator = document.getElementById('status-indicator');
const blurToggle = document.getElementById('blur-toggle');
const gazeToggle = document.getElementById('gaze-toggle');
const facesCount = document.getElementById('faces-count');
const alertStatus = document.getElementById('alert-status');
const fpsValue = document.getElementById('fps-value');
const latencyValue = document.getElementById('latency-value');
const alertContainer = document.getElementById('alert-container');
const settingsButton = document.getElementById('settings-button');

// Storage keys
const STORAGE_KEYS = {
  BLUR_ENABLED: 'blurEnabled',
  GAZE_ENABLED: 'gazeEnabled',
  DETECTION_RUNNING: 'detectionRunning'
};

/**
 * Initialize popup
 */
function initializePopup() {
  loadSettings();
  attachEventListeners();
  updateMetrics();
  
  // Periodically update metrics
  setInterval(updateMetrics, 1000);
}

/**
 * Load settings from storage
 */
function loadSettings() {
  chrome.storage.local.get(
    [STORAGE_KEYS.BLUR_ENABLED, STORAGE_KEYS.GAZE_ENABLED],
    (result) => {
      const blurEnabled = result[STORAGE_KEYS.BLUR_ENABLED] !== false;
      const gazeEnabled = result[STORAGE_KEYS.GAZE_ENABLED] !== false;
      
      updateToggle(blurToggle, blurEnabled);
      updateToggle(gazeToggle, gazeEnabled);
    }
  );
}

/**
 * Update toggle visual state
 */
function updateToggle(toggleElement, isEnabled) {
  if (isEnabled) {
    toggleElement.classList.add('enabled');
  } else {
    toggleElement.classList.remove('enabled');
  }
}

/**
 * Attach event listeners
 */
function attachEventListeners() {
  blurToggle.addEventListener('click', () => {
    const isEnabled = blurToggle.classList.contains('enabled');
    chrome.storage.local.set({
      [STORAGE_KEYS.BLUR_ENABLED]: !isEnabled
    });
    updateToggle(blurToggle, !isEnabled);
    
    // Notify background script
    chrome.runtime.sendMessage({
      action: 'toggleBlur',
      enabled: !isEnabled
    });
  });
  
  gazeToggle.addEventListener('click', () => {
    const isEnabled = gazeToggle.classList.contains('enabled');
    chrome.storage.local.set({
      [STORAGE_KEYS.GAZE_ENABLED]: !isEnabled
    });
    updateToggle(gazeToggle, !isEnabled);
    
    // Notify background script
    chrome.runtime.sendMessage({
      action: 'toggleGaze',
      enabled: !isEnabled
    });
  });
  
  settingsButton.addEventListener('click', () => {
    chrome.runtime.openOptionsPage();
  });
}

/**
 * Update metrics display
 */
function updateMetrics() {
  chrome.storage.local.get(['metrics', 'lastAlert'], (result) => {
    const metrics = result.metrics || {};
    const lastAlert = result.lastAlert;
    
    // Update face count
    facesCount.textContent = metrics.faceCount || 0;
    
    // Update alert status
    if (lastAlert && Date.now() - lastAlert.timestamp < 3000) {
      alertStatus.textContent = 'THREAT DETECTED';
      alertStatus.style.color = '#dc2626';
      showAlert(lastAlert);
    } else {
      alertStatus.textContent = 'SAFE';
      alertStatus.style.color = '#16a34a';
      clearAlert();
    }
    
    // Update FPS
    fpsValue.textContent = (metrics.fps || 0).toFixed(1);
    
    // Update latency
    latencyValue.textContent = (metrics.latency || 0).toFixed(0) + 'ms';
    
    // Update status indicator
    const isDetectionRunning = result[STORAGE_KEYS.DETECTION_RUNNING] !== false;
    if (isDetectionRunning) {
      statusIndicator.classList.add('active');
    } else {
      statusIndicator.classList.remove('active');
    }
  });
}

/**
 * Show alert notification
 */
function showAlert(alert) {
  if (alertContainer.querySelector('.alert-box')) {
    return; // Already showing
  }
  
  const alertBox = document.createElement('div');
  alertBox.className = 'alert-box warning';
  alertBox.innerHTML = `
    <strong>⚠️ Unauthorized Observer Detected!</strong><br>
    <small>Faces: ${alert.faceCount} | Time: ${new Date(alert.timestamp).toLocaleTimeString()}</small>
  `;
  alertContainer.appendChild(alertBox);
  
  // Auto-remove after 5 seconds
  setTimeout(() => {
    clearAlert();
  }, 5000);
}

/**
 * Clear alert notification
 */
function clearAlert() {
  alertContainer.innerHTML = '';
}

/**
 * Listen for messages from background script
 */
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'updateMetrics') {
    chrome.storage.local.set({
      metrics: message.metrics,
      lastAlert: message.lastAlert
    });
    updateMetrics();
  }
});

// Initialize when popup loads
document.addEventListener('DOMContentLoaded', initializePopup);
