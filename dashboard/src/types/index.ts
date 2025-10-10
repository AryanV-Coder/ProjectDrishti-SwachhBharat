// Types and interfaces for SwachhBharat Dashboard

export interface IncidentPhoto {
  id: string;
  url: string;
  timestamp: Date;
  description?: string;
}

export interface Fine {
  id: string;
  type: 'spitting' | 'littering' | 'other';
  amount: number;
  date: Date;
  location: string;
  description: string;
  status: 'pending' | 'paid' | 'overdue';
  incidentPhotos: IncidentPhoto[];
}

export interface Person {
  id: string;
  name: string;
  fineCount: number;
  totalAmount: number;
  lastIncidentDate: Date;
  fines: Fine[];
  status: 'active' | 'resolved';
}

export interface DashboardStats {
  totalPeople: number;
  totalFines: number;
  totalAmount: number;
  todayFines: number;
}