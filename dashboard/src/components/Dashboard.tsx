import React, { useState, useEffect } from 'react';
import { Person, DashboardStats } from '../types';
import { fetchPeople, fetchStats } from '../data/mockData';
import PersonCard from './PersonCard';
import PersonDetailsModal from './PersonDetailsModal';
import { Shield, Users, IndianRupee, AlertTriangle } from 'lucide-react';

const Dashboard: React.FC = () => {
  const [people, setPeople] = useState<Person[]>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [selectedPerson, setSelectedPerson] = useState<Person | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const [peopleData, statsData] = await Promise.all([
          fetchPeople(),
          fetchStats()
        ]);
        setPeople(peopleData);
        setStats(statsData);
      } catch (error) {
        console.error('Error loading data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  const handlePersonClick = (person: Person) => {
    setSelectedPerson(person);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedPerson(null);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0,
    }).format(amount);
  };

  if (loading) {
    return (
      <div className="app">
        <div className="loading">
          <Shield size={48} style={{ marginBottom: '1rem' }} />
          <h2>Loading SwachhBharat Dashboard...</h2>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <h1>
            <Shield size={24} />
            SwachhBharat Monitoring System
          </h1>
          
          {stats && (
            <div className="header-stats">
              <div className="stat-item">
                <div className="stat-number">
                  <Users size={20} style={{ display: 'inline', marginRight: '0.5rem' }} />
                  {stats.totalPeople}
                </div>
                <div className="stat-label">Total People</div>
              </div>
              
              <div className="stat-item">
                <div className="stat-number">
                  <AlertTriangle size={20} style={{ display: 'inline', marginRight: '0.5rem' }} />
                  {stats.totalFines}
                </div>
                <div className="stat-label">Total Fines</div>
              </div>
              
              <div className="stat-item">
                <div className="stat-number">
                  <IndianRupee size={20} style={{ display: 'inline', marginRight: '0.5rem' }} />
                  {formatCurrency(stats.totalAmount).replace('₹', '')}
                </div>
                <div className="stat-label">Total Amount</div>
              </div>
              
              <div className="stat-item">
                <div className="stat-number">{stats.todayFines}</div>
                <div className="stat-label">Today's Fines</div>
              </div>
            </div>
          )}
        </div>
      </header>

      <main className="main-content">
        <h2 className="dashboard-title">People with Imposed Fines</h2>
        
        {people.length > 0 ? (
          <div className="people-grid">
            {people.map((person) => (
              <PersonCard
                key={person.id}
                person={person}
                onClick={handlePersonClick}
              />
            ))}
          </div>
        ) : (
          <div className="no-data">
            <Shield size={48} style={{ marginBottom: '1rem' }} />
            <h3>No fines recorded</h3>
            <p>The system is monitoring, but no violations have been detected yet.</p>
          </div>
        )}
      </main>

      <PersonDetailsModal
        person={selectedPerson}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
      />
    </div>
  );
};

export default Dashboard;