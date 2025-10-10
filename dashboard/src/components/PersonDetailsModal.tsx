import React from 'react';
import { Person, Fine } from '../types';
import { format } from 'date-fns';
import { X, Calendar, MapPin, IndianRupee } from 'lucide-react';

interface PersonDetailsModalProps {
  person: Person | null;
  isOpen: boolean;
  onClose: () => void;
}

const PersonDetailsModal: React.FC<PersonDetailsModalProps> = ({ person, isOpen, onClose }) => {
  if (!isOpen || !person) return null;

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0,
    }).format(amount);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'var(--warning-color)';
      case 'paid':
        return 'var(--success-color)';
      case 'overdue':
        return 'var(--error-color)';
      default:
        return 'var(--text-secondary)';
    }
  };

  const getViolationTypeDisplay = (type: string) => {
    switch (type) {
      case 'spitting':
        return 'Public Spitting';
      case 'littering':
        return 'Littering';
      case 'other':
        return 'Other Violation';
      default:
        return 'Unknown Violation';
    }
  };

  const renderFineItem = (fine: Fine) => (
    <div key={fine.id} className="fine-item">
      <div className="fine-header">
        <span className="fine-type">{getViolationTypeDisplay(fine.type)}</span>
        <span className="fine-amount">{formatCurrency(fine.amount)}</span>
      </div>
      
      <div className="fine-details">
        <div className="detail-row">
          <span className="detail-label">
            <Calendar size={16} style={{ marginRight: '0.5rem', display: 'inline' }} />
            Date:
          </span>
          <span className="detail-value">
            {format(new Date(fine.date), 'MMM dd, yyyy - HH:mm')}
          </span>
        </div>
        
        <div className="detail-row">
          <span className="detail-label">
            <MapPin size={16} style={{ marginRight: '0.5rem', display: 'inline' }} />
            Location:
          </span>
          <span className="detail-value">{fine.location}</span>
        </div>
        
        <div className="detail-row">
          <span className="detail-label">Status:</span>
          <span 
            className="detail-value" 
            style={{ color: getStatusColor(fine.status) }}
          >
            {fine.status.charAt(0).toUpperCase() + fine.status.slice(1)}
          </span>
        </div>
        
        <div className="detail-row" style={{ gridColumn: '1 / -1' }}>
          <span className="detail-label">Description:</span>
          <span className="detail-value">{fine.description}</span>
        </div>
      </div>
      
      {fine.incidentPhotos.length > 0 && (
        <div>
          <h4 style={{ 
            color: 'var(--text-secondary)', 
            fontSize: '0.875rem', 
            marginBottom: '0.5rem',
            fontWeight: '600'
          }}>
            Incident Photos:
          </h4>
          <div className="incident-photos">
            {fine.incidentPhotos.map((photo) => (
              <img
                key={photo.id}
                src={photo.url}
                alt={photo.description || 'Incident photo'}
                className="incident-photo"
                title={`${photo.description || 'Incident photo'} - ${format(new Date(photo.timestamp), 'MMM dd, yyyy HH:mm')}`}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2 className="modal-title">Fine Details - {person.name}</h2>
          <button className="close-button" onClick={onClose}>
            <X size={20} />
          </button>
        </div>
        
        <div className="modal-body">
          <div className="person-summary">
            <div className="detail-row">
              <span className="detail-label">Total Fines:</span>
              <span className="detail-value">{person.fineCount}</span>
            </div>
            
            <div className="detail-row">
              <span className="detail-label">Total Amount:</span>
              <span className="detail-value total-amount">
                <IndianRupee size={16} style={{ display: 'inline', marginRight: '0.25rem' }} />
                {formatCurrency(person.totalAmount)}
              </span>
            </div>
            
            <div className="detail-row">
              <span className="detail-label">Last Incident:</span>
              <span className="detail-value">
                {format(new Date(person.lastIncidentDate), 'MMMM dd, yyyy - HH:mm')}
              </span>
            </div>
            
            <div className="detail-row">
              <span className="detail-label">Status:</span>
              <span className="detail-value" style={{ 
                color: person.status === 'active' ? 'var(--error-color)' : 'var(--success-color)' 
              }}>
                {person.status.charAt(0).toUpperCase() + person.status.slice(1)}
              </span>
            </div>
          </div>
          
          <h3 style={{ 
            color: 'var(--text-primary)', 
            marginBottom: '1rem',
            fontSize: '1.125rem',
            fontWeight: '600'
          }}>
            Fine History ({person.fines.length})
          </h3>
          
          <div className="fines-list">
            {person.fines
              .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
              .map(renderFineItem)
            }
          </div>
        </div>
      </div>
    </div>
  );
};

export default PersonDetailsModal;