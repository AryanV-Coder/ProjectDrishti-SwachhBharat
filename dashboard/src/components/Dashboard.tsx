import React, { useState, useEffect } from 'react';
import { mockPeople, mockStats } from '../data/mockData';

const Dashboard = () => {
  const [people, setPeople] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [selectedPerson, setSelectedPerson] = useState<any>(null);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    // Load data 
    setPeople(mockPeople);
    setStats(mockStats);
  }, []);

  const openModal = (person: any) => {
    setSelectedPerson(person);
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setSelectedPerson(null);
  };

  const formatMoney = (amount: number) => {
    return `₹${amount.toLocaleString()}`;
  };

  const formatDate = (date: any) => {
    return new Date(date).toLocaleDateString('en-IN');
  };

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <h1>Swachh Bharat Dashboard</h1>
          {stats && (
            <div className="header-stats">
              <div className="stat-item">
                <div className="stat-number">{stats.totalPeople}</div>
                <div className="stat-label">People</div>
              </div>
              <div className="stat-item">
                <div className="stat-number">{stats.totalFines}</div>
                <div className="stat-label">Fines</div>
              </div>
              <div className="stat-item">
                <div className="stat-number">{formatMoney(stats.totalAmount)}</div>
                <div className="stat-label">Total Amount</div>
              </div>
            </div>
          )}
        </div>
      </header>

      <main className="main-content">
        <h2 className="dashboard-title">Fined People</h2>
        
        <div className="people-grid">
          {people.map((person) => (
            <div key={person.id} className="person-card" onClick={() => openModal(person)}>
              <div className="person-header">
                <div className="person-name">{person.name}</div>
                <div className="fine-count">{person.fineCount} fines</div>
              </div>
              <div className="person-details">
                <div className="detail-row">
                  <span className="detail-label">Total:</span>
                  <span className="detail-value total-amount">{formatMoney(person.totalAmount)}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Last incident:</span>
                  <span className="detail-value">{formatDate(person.lastIncidentDate)}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </main>

      {showModal && selectedPerson && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">{selectedPerson.name} - Fine Details</h2>
              <button className="close-button" onClick={closeModal}>×</button>
            </div>
            <div className="modal-body">
              <div className="person-summary">
                <div className="detail-row">
                  <span className="detail-label">Total Fines:</span>
                  <span className="detail-value">{selectedPerson.fineCount}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Total Amount:</span>
                  <span className="detail-value total-amount">{formatMoney(selectedPerson.totalAmount)}</span>
                </div>
              </div>
              
              <h3>Fine History</h3>
              <div className="fines-list">
                {selectedPerson.fines.map((fine: any) => (
                  <div key={fine.id} className="fine-item">
                    <div className="fine-header">
                      <span className="fine-type">{fine.type.toUpperCase()}</span>
                      <span className="fine-amount">{formatMoney(fine.amount)}</span>
                    </div>
                    <div className="fine-details">
                      <div className="detail-row">
                        <span className="detail-label">Date:</span>
                        <span className="detail-value">{formatDate(fine.date)}</span>
                      </div>
                      <div className="detail-row">
                        <span className="detail-label">Status:</span>
                        <span className="detail-value">{fine.status}</span>
                      </div>
                      <div className="detail-row">
                        <span className="detail-label">Location:</span>
                        <span className="detail-value">{fine.location}</span>
                      </div>
                    </div>
                    <p>{fine.description}</p>
                    {fine.incidentPhotos.length > 0 && (
                      <div className="incident-photos">
                        {fine.incidentPhotos.map((photo: any) => (
                          <img key={photo.id} src={photo.url} alt="Evidence" className="incident-photo" />
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;