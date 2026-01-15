export const config = {
  env: process.env.NODE_ENV || 'development',
  api: {
    baseUrl: process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1',
  },
  auth: {
    googleClientId: process.env.REACT_APP_GOOGLE_CLIENT_ID || '',
    bypassAuth: false,
  },
};
