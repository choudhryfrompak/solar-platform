// frontend/src/App.js - Fixed with Timezone Support
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Icon components
const Icons = {
  Lightning: () => (
    <svg className="icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
    </svg>
  ),
  Plus: () => (
    <svg className="icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
    </svg>
  ),
  Play: () => (
    <svg className="icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1m4 0h1m-6 4h8m-9-4v8a2 2 0 002 2h8a2 2 0 002-2v-8M5 6a2 2 0 012-2h10a2 2 0 012 2v2a2 2 0 01-2 2H7a2 2 0 01-2-2V6z" />
    </svg>
  ),
  Stop: () => (
    <svg className="icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
    </svg>
  ),
  Trash: () => (
    <svg className="icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
    </svg>
  ),
  Chart: () => (
    <svg className="icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
    </svg>
  ),
  Refresh: () => (
    <svg className="icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
    </svg>
  ),
  Grid: () => (
    <svg className="icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
    </svg>
  ),
  List: () => (
    <svg className="icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
    </svg>
  ),
  Close: () => (
    <svg className="icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
    </svg>
  ),
  Server: () => (
    <svg className="icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
    </svg>
  ),
  Sun: () => (
    <svg className="icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
    </svg>
  ),
  Clock: () => (
    <svg className="icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  )
};

// Common timezones
const TIMEZONES = [
  { value: 'UTC', label: 'UTC' },
  { value: 'America/New_York', label: 'Eastern Time (US)' },
  { value: 'America/Chicago', label: 'Central Time (US)' },
  { value: 'America/Denver', label: 'Mountain Time (US)' },
  { value: 'America/Los_Angeles', label: 'Pacific Time (US)' },
  { value: 'Europe/London', label: 'London' },
  { value: 'Europe/Paris', label: 'Paris' },
  { value: 'Europe/Berlin', label: 'Berlin' },
  { value: 'Asia/Tokyo', label: 'Tokyo' },
  { value: 'Asia/Shanghai', label: 'Shanghai' },
  { value: 'Asia/Kolkata', label: 'Mumbai' },
  { value: 'Australia/Sydney', label: 'Sydney' },
  { value: 'Australia/Melbourne', label: 'Melbourne' },
  { value: 'Australia/Perth', label: 'Perth' },
  { value: 'Pacific/Auckland', label: 'Auckland' }
];

// Utility functions
const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return 'Invalid Date';
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    });
  } catch {
    return 'Invalid Date';
  }
};

const formatDateTime = (dateString) => {
  if (!dateString) return 'N/A';
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return 'Invalid Date';
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch {
    return 'Invalid Date';
  }
};

function App() {
  const [inverters, setInverters] = useState([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [selectedInverter, setSelectedInverter] = useState(null);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState('grid');

  useEffect(() => {
    fetchInverters();
  }, []);

  const fetchInverters = async () => {
    try {
      const response = await axios.get(`${API_BASE}/inverters`);
      setInverters(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching inverters:', error);
      setLoading(false);
    }
  };

  const handleAddInverter = async (data) => {
    try {
      await axios.post(`${API_BASE}/inverters`, data);
      fetchInverters();
      setShowAddForm(false);
    } catch (error) {
      console.error('Error adding inverter:', error);
    }
  };

  const handleDeleteInverter = async (id) => {
    if (window.confirm('Are you sure you want to delete this inverter?')) {
      try {
        await axios.delete(`${API_BASE}/inverters/${id}`);
        fetchInverters();
      } catch (error) {
        console.error('Error deleting inverter:', error);
      }
    }
  };

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <div className="brand">
            <div className="brand-icon">
              <Icons.Lightning />
            </div>
            <div className="brand-text">
              <h1>Solar Monitor</h1>
              <p>Admin Dashboard</p>
            </div>
          </div>
          <button className="btn btn-primary" onClick={() => setShowAddForm(true)}>
            <Icons.Plus />
            <span>Add Inverter</span>
          </button>
        </div>
      </header>

      <main className="main">
        {loading ? (
          <div className="loading">
            <div className="spinner"></div>
            <span>Loading inverters...</span>
          </div>
        ) : (
          <div className="content">
            <div className="stats-bar">
              <div className="stat">
                <div className="stat-icon">
                  <Icons.Server />
                </div>
                <div className="stat-content">
                  <span className="stat-number">{inverters.length}</span>
                  <span className="stat-label">Total Inverters</span>
                </div>
              </div>
              <div className="stat">
                <div className="stat-icon active">
                  <Icons.Play />
                </div>
                <div className="stat-content">
                  <span className="stat-number">{inverters.filter(i => i.status === 'active').length}</span>
                  <span className="stat-label">Active</span>
                </div>
              </div>
              <div className="stat">
                <div className="stat-icon inactive">
                  <Icons.Stop />
                </div>
                <div className="stat-content">
                  <span className="stat-number">{inverters.filter(i => i.status === 'inactive').length}</span>
                  <span className="stat-label">Inactive</span>
                </div>
              </div>
              <div className="stat">
                <div className="stat-icon error">
                  <Icons.Lightning />
                </div>
                <div className="stat-content">
                  <span className="stat-number">{inverters.filter(i => i.status === 'error').length}</span>
                  <span className="stat-label">Error</span>
                </div>
              </div>
            </div>

            <div className="inverters-section">
              <div className="section-header">
                <h2>Inverters</h2>
                <div className="view-controls">
                  <button 
                    className={`view-btn ${viewMode === 'grid' ? 'active' : ''}`}
                    onClick={() => setViewMode('grid')}
                  >
                    <Icons.Grid />
                    <span>Grid</span>
                  </button>
                  <button 
                    className={`view-btn ${viewMode === 'list' ? 'active' : ''}`}
                    onClick={() => setViewMode('list')}
                  >
                    <Icons.List />
                    <span>List</span>
                  </button>
                </div>
              </div>
              
              {inverters.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-icon">
                    <Icons.Sun />
                  </div>
                  <h3>No inverters configured</h3>
                  <p>Add your first solar inverter to start monitoring</p>
                  <button className="btn btn-primary" onClick={() => setShowAddForm(true)}>
                    <Icons.Plus />
                    <span>Add Inverter</span>
                  </button>
                </div>
              ) : (
                <div className={`inverters-container ${viewMode}`}>
                  {inverters.map(inverter => (
                    viewMode === 'grid' ? (
                      <InverterCard
                        key={inverter.id}
                        inverter={inverter}
                        onView={() => setSelectedInverter(inverter)}
                        onDelete={() => handleDeleteInverter(inverter.id)}
                        onRefresh={fetchInverters}
                      />
                    ) : (
                      <InverterListItem
                        key={inverter.id}
                        inverter={inverter}
                        onView={() => setSelectedInverter(inverter)}
                        onDelete={() => handleDeleteInverter(inverter.id)}
                        onRefresh={fetchInverters}
                      />
                    )
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </main>

      {showAddForm && (
        <AddInverterModal
          onClose={() => setShowAddForm(false)}
          onAdd={handleAddInverter}
        />
      )}

      {selectedInverter && (
        <InverterDetailsModal
          inverter={selectedInverter}
          onClose={() => setSelectedInverter(null)}
          onRefresh={fetchInverters}
        />
      )}
    </div>
  );
}

function InverterCard({ inverter, onView, onDelete, onRefresh }) {
  const [loading, setLoading] = useState(false);

  const handleStart = async () => {
    setLoading(true);
    try {
      await axios.post(`${API_BASE}/inverters/${inverter.id}/start`);
      setTimeout(() => {
        onRefresh();
        setLoading(false);
      }, 3000);
    } catch (error) {
      console.error('Error starting:', error);
      setLoading(false);
    }
  };

  const handleStop = async () => {
    setLoading(true);
    try {
      await axios.post(`${API_BASE}/inverters/${inverter.id}/stop`);
      setTimeout(() => {
        onRefresh();
        setLoading(false);
      }, 2000);
    } catch (error) {
      console.error('Error stopping:', error);
      setLoading(false);
    }
  };

  const getStatusConfig = (status) => {
    switch (status) {
      case 'active':
        return { color: 'var(--success)', text: 'Running' };
      case 'inactive':
        return { color: 'var(--text-light)', text: 'Stopped' };
      case 'error':
        return { color: 'var(--danger)', text: 'Error' };
      default:
        return { color: 'var(--warning)', text: 'Pending' };
    }
  };

  const statusConfig = getStatusConfig(inverter.status);

  return (
    <div className="inverter-card">
      <div className="card-header">
        <div className="card-title">
          <h3>{inverter.name}</h3>
          <span className="inverter-type">{inverter.inverter_type}</span>
        </div>
        <div className="status-indicator" style={{ backgroundColor: statusConfig.color }}>
          <div className="status-dot"></div>
          <span className="status-text">{loading ? 'Processing...' : statusConfig.text}</span>
        </div>
      </div>
      
      <div className="card-metrics">
        <div className="metric">
          <span className="metric-label">Region</span>
          <span className="metric-value">{inverter.region.toUpperCase()}</span>
        </div>
        <div className="metric">
          <span className="metric-label">Timezone</span>
          <span className="metric-value">{inverter.timezone}</span>
        </div>
        <div className="metric">
          <span className="metric-label">Interval</span>
          <span className="metric-value">{inverter.interval}s</span>
        </div>
        <div className="metric">
          <span className="metric-label">Created</span>
          <span className="metric-value">{formatDate(inverter.created_at)}</span>
        </div>
      </div>
      
      <div className="card-actions">
        <button className="btn btn-outline" onClick={onView}>
          <Icons.Chart />
          <span>Details</span>
        </button>
        
        {inverter.status === 'active' ? (
          <button className="btn btn-warning" onClick={handleStop} disabled={loading}>
            <Icons.Stop />
            <span>Stop</span>
          </button>
        ) : (
          <button className="btn btn-success" onClick={handleStart} disabled={loading}>
            <Icons.Play />
            <span>Start</span>
          </button>
        )}
        
        <button className="btn btn-danger-outline" onClick={onDelete}>
          <Icons.Trash />
        </button>
      </div>
    </div>
  );
}

function InverterListItem({ inverter, onView, onDelete, onRefresh }) {
  const [loading, setLoading] = useState(false);

  const handleStart = async () => {
    setLoading(true);
    try {
      await axios.post(`${API_BASE}/inverters/${inverter.id}/start`);
      setTimeout(() => {
        onRefresh();
        setLoading(false);
      }, 3000);
    } catch (error) {
      console.error('Error starting:', error);
      setLoading(false);
    }
  };

  const handleStop = async () => {
    setLoading(true);
    try {
      await axios.post(`${API_BASE}/inverters/${inverter.id}/stop`);
      setTimeout(() => {
        onRefresh();
        setLoading(false);
      }, 2000);
    } catch (error) {
      console.error('Error stopping:', error);
      setLoading(false);
    }
  };

  const getStatusConfig = (status) => {
    switch (status) {
      case 'active':
        return { color: 'var(--success)', text: 'Running' };
      case 'inactive':
        return { color: 'var(--text-light)', text: 'Stopped' };
      case 'error':
        return { color: 'var(--danger)', text: 'Error' };
      default:
        return { color: 'var(--warning)', text: 'Pending' };
    }
  };

  const statusConfig = getStatusConfig(inverter.status);

  return (
    <div className="inverter-list-item">
      <div className="list-item-main">
        <div className="list-item-info">
          <h3>{inverter.name}</h3>
          <div className="list-item-details">
            <span>{inverter.inverter_type}</span>
            <span>{inverter.region.toUpperCase()}</span>
            <span>{inverter.timezone}</span>
            <span>{inverter.interval}s interval</span>
            <span>Created {formatDate(inverter.created_at)}</span>
          </div>
        </div>
        <div className="list-item-status">
          <div className="status-indicator" style={{ backgroundColor: statusConfig.color }}>
            <div className="status-dot"></div>
            <span className="status-text">{loading ? 'Processing...' : statusConfig.text}</span>
          </div>
        </div>
      </div>
      
      <div className="list-item-actions">
        <button className="btn btn-outline btn-sm" onClick={onView}>
          <Icons.Chart />
          <span>Details</span>
        </button>
        
        {inverter.status === 'active' ? (
          <button className="btn btn-warning btn-sm" onClick={handleStop} disabled={loading}>
            <Icons.Stop />
            <span>Stop</span>
          </button>
        ) : (
          <button className="btn btn-success btn-sm" onClick={handleStart} disabled={loading}>
            <Icons.Play />
            <span>Start</span>
          </button>
        )}
        
        <button className="btn btn-danger-outline btn-sm" onClick={onDelete}>
          <Icons.Trash />
        </button>
      </div>
    </div>
  );
}

function AddInverterModal({ onClose, onAdd }) {
  const [formData, setFormData] = useState({
    name: '',
    inverter_type: 'goodwe',
    region: 'au',
    timezone: 'UTC',
    sems_username: '',
    sems_password: '',
    interval: 300
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onAdd(formData);
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'interval' ? parseInt(value) : value
    }));
  };

  return (
    <div className="modal-overlay">
      <div className="modal">
        <div className="modal-header">
          <div>
            <h2>Add New Inverter</h2>
            <p className="modal-subtitle">Configure solar inverter monitoring</p>
          </div>
          <button className="close-btn" onClick={onClose}>
            <Icons.Close />
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="form">
          <div className="modal-body">
            <div className="form-section">
              <h3>Inverter Configuration</h3>
              
              <div className="form-group">
                <label>Inverter Name</label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  placeholder="e.g., House Solar System"
                  required
                />
              </div>
              
              <div className="form-row">
                <div className="form-group">
                  <label>Type</label>
                  <select name="inverter_type" value={formData.inverter_type} onChange={handleChange}>
                    <option value="goodwe">GoodWe</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Region</label>
                  <select name="region" value={formData.region} onChange={handleChange}>
                    <option value="au">Australia</option>
                    <option value="eu">Europe</option>
                    <option value="us">United States</option>
                  </select>
                </div>
              </div>
              
              <div className="form-row">
                <div className="form-group">
                  <label>Timezone</label>
                  <select name="timezone" value={formData.timezone} onChange={handleChange}>
                    {TIMEZONES.map(tz => (
                      <option key={tz.value} value={tz.value}>{tz.label}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label>Data Collection Interval</label>
                  <select name="interval" value={formData.interval} onChange={handleChange}>
                    <option value={60}>1 minute</option>
                    <option value={300}>5 minutes</option>
                    <option value={600}>10 minutes</option>
                    <option value={1800}>30 minutes</option>
                    <option value={3600}>1 hour</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="form-section">
              <h3>SEMS Portal Credentials</h3>
              <div className="form-group">
                <label>Username/Email</label>
                <input
                  type="text"
                  name="sems_username"
                  value={formData.sems_username}
                  onChange={handleChange}
                  placeholder="your.email@example.com"
                  required
                />
              </div>
              <div className="form-group">
                <label>Password</label>
                <input
                  type="password"
                  name="sems_password"
                  value={formData.sems_password}
                  onChange={handleChange}
                  placeholder="••••••••"
                  required
                />
              </div>
            </div>
          </div>

          <div className="form-actions">
            <button type="button" className="btn btn-outline" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary">
              <Icons.Plus />
              <span>Add Inverter</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function InverterDetailsModal({ inverter, onClose, onRefresh }) {
  const [logs, setLogs] = useState('');
  const [status, setStatus] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchLogs();
    fetchStatus();
  }, [inverter.id]);

  const fetchLogs = async () => {
    try {
      const response = await axios.get(`${API_BASE}/inverters/${inverter.id}/logs`);
      setLogs(response.data.logs);
    } catch (error) {
      console.error('Error fetching logs:', error);
    }
  };

  const fetchStatus = async () => {
    try {
      const response = await axios.get(`${API_BASE}/inverters/${inverter.id}/status`);
      setStatus(response.data.status);
    } catch (error) {
      console.error('Error fetching status:', error);
    }
  };

  const handleRestart = async () => {
    setLoading(true);
    try {
      await axios.post(`${API_BASE}/inverters/${inverter.id}/stop`);
      setTimeout(async () => {
        await axios.post(`${API_BASE}/inverters/${inverter.id}/start`);
        setTimeout(() => {
          onRefresh();
          fetchStatus();
          setLoading(false);
        }, 3000);
      }, 2000);
    } catch (error) {
      console.error('Error restarting:', error);
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal modal-large">
        <div className="modal-header">
          <div>
            <h2>{inverter.name}</h2>
            <span className="modal-subtitle">Inverter Details & Monitoring</span>
          </div>
          <button className="close-btn" onClick={onClose}>
            <Icons.Close />
          </button>
        </div>
        
        <div className="modal-body">
          <div className="details-tabs">
            <section className="details-section">
              <h3>Configuration</h3>
              <div className="config-grid">
                <div className="config-item">
                  <label>Name</label>
                  <span>{inverter.name}</span>
                </div>
                <div className="config-item">
                  <label>Type</label>
                  <span>{inverter.inverter_type}</span>
                </div>
                <div className="config-item">
                  <label>Region</label>
                  <span>{inverter.region}</span>
                </div>
                <div className="config-item">
                  <label>Timezone</label>
                  <span>{inverter.timezone}</span>
                </div>
                <div className="config-item">
                  <label>Interval</label>
                  <span>{inverter.interval}s</span>
                </div>
                <div className="config-item">
                  <label>Status</label>
                  <span className={`status ${inverter.status}`}>{inverter.status}</span>
                </div>
                <div className="config-item">
                  <label>Container</label>
                  <span className="container-id">{inverter.container_id?.slice(0, 12) || 'None'}</span>
                </div>
              </div>
            </section>

            <section className="details-section">
              <div className="section-header">
                <h3>Container Management</h3>
                <button className="btn btn-primary" onClick={handleRestart} disabled={loading}>
                  <Icons.Refresh />
                  <span>{loading ? 'Restarting...' : 'Restart'}</span>
                </button>
              </div>
              <div className="status-info">
                <div className="status-item">
                  <label>Current Status</label>
                  <span className={`status ${status}`}>{status || 'Unknown'}</span>
                </div>
                <div className="status-item">
                  <label>Last Update</label>
                  <span>{formatDateTime(inverter.last_update)}</span>
                </div>
              </div>
            </section>

            <section className="details-section">
              <div className="section-header">
                <h3>Container Logs</h3>
                <button className="btn btn-outline" onClick={fetchLogs}>
                  <Icons.Refresh />
                  <span>Refresh</span>
                </button>
              </div>
              <div className="logs-container">
                <pre>{logs || 'No logs available'}</pre>
              </div>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;