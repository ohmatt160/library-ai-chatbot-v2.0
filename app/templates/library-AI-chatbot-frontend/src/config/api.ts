// src/config/api.ts

const isProduction = process.env.NODE_ENV === 'production';

// For Render deployment
const PRODUCTION_API_URL = '/api';

// For local development
const DEVELOPMENT_API_URL = 'http://localhost:5000/api';

export const API_URL = isProduction ? PRODUCTION_API_URL : DEVELOPMENT_API_URL;

