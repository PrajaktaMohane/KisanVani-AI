/**
 * Converts a base64 encoded audio string to an Audio object source URL.
 */
export function base64ToAudioUrl(base64Data, mimeType = 'audio/mp3') {
  if (!base64Data) return null;
  return `data:${mimeType};base64,${base64Data}`;
}

/**
 * Checks if browser supports required audio recording APIs.
 */
export function isAudioRecordingSupported() {
  return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia && window.MediaRecorder);
}
