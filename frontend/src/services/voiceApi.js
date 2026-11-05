import api from './api';

export const sendVoiceQuery = async (audioBlob, farmerContext = {}) => {
  const formData = new FormData();
  formData.append('audio_file', audioBlob, 'query.webm');

  if (farmerContext.state) formData.append('state', farmerContext.state);
  if (farmerContext.district) formData.append('district', farmerContext.district);
  if (farmerContext.cropName) formData.append('crop_name', farmerContext.cropName);
  if (farmerContext.soilType) formData.append('soil_type', farmerContext.soilType);
  if (farmerContext.landSize) formData.append('land_size_acres', farmerContext.landSize);
  if (farmerContext.language) formData.append('preferred_language', farmerContext.language);
  if (farmerContext.sessionId) formData.append('session_id', farmerContext.sessionId);

  const response = await api.post('/api/v1/voice', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};

export const sendTextQuery = async (queryText, farmerContext = {}) => {
  const payload = {
    query: queryText,
    session_id: farmerContext.sessionId,
    state: farmerContext.state,
    district: farmerContext.district,
    crop_name: farmerContext.cropName,
    soil_type: farmerContext.soilType,
    land_size_acres: farmerContext.landSize,
    language: farmerContext.language,
    include_audio: true,
  };

  const response = await api.post('/api/v1/chat', payload);
  return response.data;
};

export const getConversationsHistory = async () => {
  const response = await api.get('/api/v1/conversations');
  return response.data;
};

export const submitFeedback = async (feedbackData) => {
  const response = await api.post('/api/v1/feedback/record', feedbackData);
  return response.data;
};
