# SwachhBharat Dashboard - Backend Integration Guide

## Overview

This document provides detailed instructions for connecting the SwachhBharat React dashboard with a backend API system. The frontend is designed to be API-ready and can easily connect to REST or GraphQL endpoints.

## Current Architecture

### Frontend Structure
```
src/
├── components/
│   ├── Dashboard.tsx          # Main dashboard component
│   ├── PersonCard.tsx         # Individual person card component
│   └── PersonDetailsModal.tsx # Modal for detailed fine information
├── data/
│   └── mockData.ts           # Mock data (to be replaced with API calls)
├── types/
│   └── index.ts              # TypeScript interfaces
└── App.tsx                   # Main application component
```

### Data Models

The application uses the following TypeScript interfaces that should match your backend models:

```typescript
interface Person {
  id: string;
  name: string;
  fineCount: number;
  totalAmount: number;
  lastIncidentDate: Date;
  fines: Fine[];
  status: 'active' | 'resolved';
}

interface Fine {
  id: string;
  type: 'spitting' | 'littering' | 'other';
  amount: number;
  date: Date;
  location: string;
  description: string;
  status: 'pending' | 'paid' | 'overdue';
  incidentPhotos: IncidentPhoto[];
}

interface IncidentPhoto {
  id: string;
  url: string;
  timestamp: Date;
  description?: string;
}

interface DashboardStats {
  totalPeople: number;
  totalFines: number;
  totalAmount: number;
  todayFines: number;
}
```

## Backend API Requirements

### Required Endpoints

#### 1. Get Dashboard Statistics
```
GET /api/dashboard/stats
Response: DashboardStats
```

#### 2. Get All People with Fines
```
GET /api/people
Query Parameters:
  - page?: number (for pagination)
  - limit?: number (for pagination)
  - status?: 'active' | 'resolved' | 'all'
  - sortBy?: 'name' | 'fineCount' | 'totalAmount' | 'lastIncidentDate'
  - sortOrder?: 'asc' | 'desc'

Response: {
  data: Person[],
  pagination: {
    currentPage: number,
    totalPages: number,
    totalItems: number,
    itemsPerPage: number
  }
}
```

#### 3. Get Person Details
```
GET /api/people/:personId
Response: Person
```

#### 4. Get Person's Fines
```
GET /api/people/:personId/fines
Query Parameters:
  - page?: number
  - limit?: number
  - status?: 'pending' | 'paid' | 'overdue' | 'all'

Response: {
  data: Fine[],
  pagination: PaginationInfo
}
```

#### 5. Real-time Updates (Optional)
```
WebSocket: /ws/dashboard
Events:
  - new_fine: { person: Person, fine: Fine }
  - fine_status_updated: { fineId: string, newStatus: string }
  - stats_updated: DashboardStats
```

## Integration Steps

### Step 1: Install HTTP Client

Choose one of the following HTTP clients:

**Option A: Axios**
```bash
cd dashboard
npm install axios
```

**Option B: Native Fetch with Custom Hook**
```bash
# No additional installation needed
```

### Step 2: Create API Service Layer

Replace the mock data functions in `src/data/mockData.ts` with actual API calls:

**Example with Axios:**

```typescript
// src/services/api.ts
import axios from 'axios';
import { Person, DashboardStats, Fine } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:3001/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for authentication if needed
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export const fetchStats = async (): Promise<DashboardStats> => {
  const response = await apiClient.get('/dashboard/stats');
  return response.data;
};

export const fetchPeople = async (params?: {
  page?: number;
  limit?: number;
  status?: string;
  sortBy?: string;
  sortOrder?: string;
}): Promise<Person[]> => {
  const response = await apiClient.get('/people', { params });
  return response.data.data; // Assuming paginated response
};

export const fetchPersonDetails = async (personId: string): Promise<Person> => {
  const response = await apiClient.get(`/people/${personId}`);
  return response.data;
};
```

### Step 3: Update Components

Update the Dashboard component to use real API calls:

```typescript
// In src/components/Dashboard.tsx
import { fetchPeople, fetchStats } from '../services/api';

// Replace the import and useEffect in Dashboard component
useEffect(() => {
  const loadData = async () => {
    try {
      setLoading(true);
      const [peopleData, statsData] = await Promise.all([
        fetchPeople({ sortBy: 'lastIncidentDate', sortOrder: 'desc' }),
        fetchStats()
      ]);
      setPeople(peopleData);
      setStats(statsData);
    } catch (error) {
      console.error('Error loading data:', error);
      // Add proper error handling here
    } finally {
      setLoading(false);
    }
  };

  loadData();
}, []);
```

### Step 4: Environment Configuration

Create environment files for different deployments:

**`.env.development`**
```
REACT_APP_API_URL=http://localhost:3001/api
REACT_APP_WEBSOCKET_URL=ws://localhost:3001/ws
```

**`.env.production`**
```
REACT_APP_API_URL=https://your-api-domain.com/api
REACT_APP_WEBSOCKET_URL=wss://your-api-domain.com/ws
```

### Step 5: Add Error Handling

Create an error handling system:

```typescript
// src/hooks/useErrorHandler.ts
import { useState } from 'react';

export const useErrorHandler = () => {
  const [error, setError] = useState<string | null>(null);

  const handleError = (error: any) => {
    const message = error.response?.data?.message || error.message || 'An error occurred';
    setError(message);
    console.error('Application Error:', error);
  };

  const clearError = () => setError(null);

  return { error, handleError, clearError };
};
```

### Step 6: Add Loading States

Enhance loading states for better UX:

```typescript
// src/hooks/useLoading.ts
import { useState } from 'react';

export const useLoading = () => {
  const [loading, setLoading] = useState(false);

  const withLoading = async (fn: () => Promise<any>) => {
    setLoading(true);
    try {
      return await fn();
    } finally {
      setLoading(false);
    }
  };

  return { loading, withLoading, setLoading };
};
```

### Step 7: Implement Real-time Updates (Optional)

Add WebSocket support for real-time updates:

```typescript
// src/hooks/useWebSocket.ts
import { useEffect, useRef } from 'react';

export const useWebSocket = (url: string, onMessage: (data: any) => void) => {
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    ws.current = new WebSocket(url);
    
    ws.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (error) {
        console.error('WebSocket message parse error:', error);
      }
    };

    ws.current.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [url, onMessage]);

  return ws.current;
};
```

## Security Considerations

### 1. Authentication
- Implement JWT token-based authentication
- Store tokens securely (consider httpOnly cookies)
- Add token refresh mechanism

### 2. API Security
- Implement CORS properly
- Use HTTPS in production
- Add rate limiting
- Validate all inputs on the backend

### 3. Data Privacy
- Ensure personal data is properly encrypted
- Implement proper access controls
- Consider GDPR compliance for personal data

## Deployment Considerations

### 1. Environment Variables
```typescript
// src/config/environment.ts
export const config = {
  apiUrl: process.env.REACT_APP_API_URL!,
  websocketUrl: process.env.REACT_APP_WEBSOCKET_URL!,
  isDevelopment: process.env.NODE_ENV === 'development',
  isProduction: process.env.NODE_ENV === 'production',
};
```

### 2. Build Optimization
```bash
# Build for production
npm run build

# Analyze bundle size
npm install --save-dev webpack-bundle-analyzer
npx webpack-bundle-analyzer build/static/js/*.js
```

### 3. Performance Monitoring
Consider adding performance monitoring tools:
- React DevTools Profiler
- Web Vitals
- Error tracking (Sentry, Bugsnag)

## Testing the Integration

### 1. Unit Tests
```bash
npm install --save-dev @testing-library/react @testing-library/jest-dom
```

### 2. API Integration Tests
```typescript
// src/__tests__/api.test.ts
import { fetchStats, fetchPeople } from '../services/api';

describe('API Integration', () => {
  test('fetchStats returns valid data', async () => {
    const stats = await fetchStats();
    expect(stats).toHaveProperty('totalPeople');
    expect(stats).toHaveProperty('totalFines');
  });

  test('fetchPeople returns array of people', async () => {
    const people = await fetchPeople();
    expect(Array.isArray(people)).toBe(true);
  });
});
```

## Troubleshooting

### Common Issues

1. **CORS Errors**: Ensure your backend allows requests from the frontend domain
2. **Network Timeouts**: Increase timeout values for slower networks
3. **Memory Leaks**: Properly cleanup WebSocket connections and API calls
4. **State Management**: Consider Redux or Zustand for complex state management

### Debug Mode

Add debug logging in development:

```typescript
// src/utils/logger.ts
export const logger = {
  debug: (message: string, data?: any) => {
    if (process.env.NODE_ENV === 'development') {
      console.log(`[DEBUG] ${message}`, data);
    }
  },
  error: (message: string, error?: any) => {
    console.error(`[ERROR] ${message}`, error);
  },
};
```

## Next Steps

1. Implement the backend API according to the specifications above
2. Replace mock data functions with API calls
3. Add proper error handling and loading states
4. Test the integration thoroughly
5. Add authentication if required
6. Implement real-time updates if needed
7. Deploy and monitor the application

This guide provides a comprehensive foundation for integrating the dashboard with a backend system while maintaining the professional, modern design and functionality.