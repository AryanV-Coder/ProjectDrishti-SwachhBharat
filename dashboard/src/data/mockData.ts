// Mock data for SwachhBharat Dashboard
import { Person, DashboardStats, Fine, IncidentPhoto } from '../types';

// Sample incident photos (using placeholder images)
const samplePhotos: IncidentPhoto[] = [
  {
    id: '1',
    url: 'https://via.placeholder.com/300x200/1a2332/ffffff?text=Incident+Photo+1',
    timestamp: new Date('2024-10-10T10:30:00'),
    description: 'CCTV capture of violation'
  },
  {
    id: '2',
    url: 'https://via.placeholder.com/300x200/1a2332/ffffff?text=Incident+Photo+2',
    timestamp: new Date('2024-10-10T10:30:05'),
    description: 'Additional angle'
  },
  {
    id: '3',
    url: 'https://via.placeholder.com/300x200/1a2332/ffffff?text=Incident+Photo+3',
    timestamp: new Date('2024-10-09T15:45:00'),
    description: 'Evidence photo'
  }
];

// Sample fines data
const sampleFines: Fine[] = [
  {
    id: 'fine-1',
    type: 'spitting',
    amount: 500,
    date: new Date('2024-10-10T10:30:00'),
    location: 'Connaught Place, New Delhi',
    description: 'Spitting in public area near metro station',
    status: 'pending',
    incidentPhotos: [samplePhotos[0], samplePhotos[1]]
  },
  {
    id: 'fine-2',
    type: 'littering',
    amount: 1000,
    date: new Date('2024-10-09T15:45:00'),
    location: 'Marine Drive, Mumbai',
    description: 'Throwing plastic bottle on the road',
    status: 'paid',
    incidentPhotos: [samplePhotos[2]]
  },
  {
    id: 'fine-3',
    type: 'spitting',
    amount: 500,
    date: new Date('2024-10-08T09:15:00'),
    location: 'Brigade Road, Bangalore',
    description: 'Spitting near bus stop',
    status: 'overdue',
    incidentPhotos: [samplePhotos[0]]
  },
  {
    id: 'fine-4',
    type: 'littering',
    amount: 1000,
    date: new Date('2024-10-07T14:20:00'),
    location: 'Park Street, Kolkata',
    description: 'Disposing cigarette butt on street',
    status: 'pending',
    incidentPhotos: [samplePhotos[1], samplePhotos[2]]
  }
];

// Sample people data
export const mockPeople: Person[] = [
  {
    id: 'person-1',
    name: 'Rahul Sharma',
    fineCount: 2,
    totalAmount: 1500,
    lastIncidentDate: new Date('2024-10-10T10:30:00'),
    fines: [sampleFines[0], sampleFines[1]],
    status: 'active'
  },
  {
    id: 'person-2',
    name: 'Priya Patel',
    fineCount: 1,
    totalAmount: 500,
    lastIncidentDate: new Date('2024-10-08T09:15:00'),
    fines: [sampleFines[2]],
    status: 'active'
  },
  {
    id: 'person-3',
    name: 'Amit Kumar',
    fineCount: 3,
    totalAmount: 2500,
    lastIncidentDate: new Date('2024-10-09T16:45:00'),
    fines: [
      sampleFines[3],
      {
        id: 'fine-5',
        type: 'spitting',
        amount: 500,
        date: new Date('2024-10-06T11:30:00'),
        location: 'India Gate, New Delhi',
        description: 'Spitting near monument area',
        status: 'paid',
        incidentPhotos: [samplePhotos[0]]
      },
      {
        id: 'fine-6',
        type: 'littering',
        amount: 1000,
        date: new Date('2024-10-05T13:15:00'),
        location: 'Juhu Beach, Mumbai',
        description: 'Throwing food wrapper on beach',
        status: 'pending',
        incidentPhotos: [samplePhotos[1], samplePhotos[2]]
      }
    ],
    status: 'active'
  },
  {
    id: 'person-4',
    name: 'Sneha Reddy',
    fineCount: 1,
    totalAmount: 1000,
    lastIncidentDate: new Date('2024-10-07T14:20:00'),
    fines: [
      {
        id: 'fine-7',
        type: 'littering',
        amount: 1000,
        date: new Date('2024-10-07T14:20:00'),
        location: 'Phoenix Mall, Chennai',
        description: 'Disposing plastic bag in parking area',
        status: 'pending',
        incidentPhotos: [samplePhotos[0]]
      }
    ],
    status: 'active'
  },
  {
    id: 'person-5',
    name: 'Vikram Singh',
    fineCount: 4,
    totalAmount: 3000,
    lastIncidentDate: new Date('2024-10-09T12:30:00'),
    fines: [
      {
        id: 'fine-8',
        type: 'spitting',
        amount: 500,
        date: new Date('2024-10-09T12:30:00'),
        location: 'Sector 17, Chandigarh',
        description: 'Spitting near shopping complex',
        status: 'pending',
        incidentPhotos: [samplePhotos[2]]
      },
      {
        id: 'fine-9',
        type: 'littering',
        amount: 1000,
        date: new Date('2024-10-08T16:45:00'),
        location: 'MG Road, Pune',
        description: 'Throwing paper cup on road',
        status: 'overdue',
        incidentPhotos: [samplePhotos[0], samplePhotos[1]]
      },
      {
        id: 'fine-10',
        type: 'spitting',
        amount: 500,
        date: new Date('2024-10-06T10:15:00'),
        location: 'Lal Chowk, Srinagar',
        description: 'Spitting in market area',
        status: 'paid',
        incidentPhotos: [samplePhotos[2]]
      },
      {
        id: 'fine-11',
        type: 'littering',
        amount: 1000,
        date: new Date('2024-10-04T15:20:00'),
        location: 'Clock Tower, Jodhpur',
        description: 'Throwing banana peel on street',
        status: 'paid',
        incidentPhotos: [samplePhotos[1]]
      }
    ],
    status: 'active'
  }
];

// Dashboard statistics
export const mockStats: DashboardStats = {
  totalPeople: mockPeople.length,
  totalFines: mockPeople.reduce((sum, person) => sum + person.fineCount, 0),
  totalAmount: mockPeople.reduce((sum, person) => sum + person.totalAmount, 0),
  todayFines: mockPeople.reduce((sum, person) => {
    const todayFines = person.fines.filter(fine => {
      const today = new Date();
      const fineDate = new Date(fine.date);
      return fineDate.toDateString() === today.toDateString();
    });
    return sum + todayFines.length;
  }, 0)
};

// API simulation functions (for future backend integration)
export const fetchPeople = async (): Promise<Person[]> => {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 1000));
  return mockPeople;
};

export const fetchStats = async (): Promise<DashboardStats> => {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 500));
  return mockStats;
};

export const fetchPersonDetails = async (personId: string): Promise<Person | null> => {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 300));
  return mockPeople.find(person => person.id === personId) || null;
};