import React from 'react';
import { Person } from '../types';
import { format } from 'date-fns';

interface PersonCardProps {
  person: Person;
  onClick: (person: Person) => void;
}

const PersonCard: React.FC<PersonCardProps> = ({ person, onClick }) => {
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0,
    }).format(amount);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'var(--error-color)';
      case 'resolved':
        return 'var(--success-color)';
      default:
        return 'var(--text-secondary)';
    }
  };

  return (
    <div className="person-card" onClick={() => onClick(person)}>
      <div className="person-header">
        <h3 className="person-name">{person.name}</h3>
        <span className="fine-count">{person.fineCount} Fine{person.fineCount !== 1 ? 's' : ''}</span>
      </div>
      
      <div className="person-details">
        <div className="detail-row">
          <span className="detail-label">Total Amount:</span>
          <span className="detail-value total-amount">{formatCurrency(person.totalAmount)}</span>
        </div>
        
        <div className="detail-row">
          <span className="detail-label">Last Incident:</span>
          <span className="detail-value">
            {format(new Date(person.lastIncidentDate), 'MMM dd, yyyy')}
          </span>
        </div>
        
        <div className="detail-row">
          <span className="detail-label">Status:</span>
          <span 
            className="detail-value" 
            style={{ color: getStatusColor(person.status) }}
          >
            {person.status.charAt(0).toUpperCase() + person.status.slice(1)}
          </span>
        </div>
      </div>
    </div>
  );
};

export default PersonCard;