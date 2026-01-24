import React, { useState } from 'react';
import { AlertTriangle, Link2, Shield, TrendingUp, X } from 'lucide-react';
import './CorrelationView.css';

const CorrelationView = ({ correlations, onResolveGroup }) => {
    const [expandedGroup, setExpandedGroup] = useState(null);

    if (!correlations || correlations.length === 0) {
        return (
            <div className="correlation-empty">
                <Link2 size={48} />
                <p>No correlated incidents detected</p>
            </div>
        );
    }

    const getThreatColor = (score) => {
        if (score >= 80) return '#dc3545';
        if (score >= 60) return '#fd7e14';
        if (score >= 40) return '#ffc107';
        return '#28a745';
    };

    const getSeverityClass = (severity) => {
        return `severity-${severity.toLowerCase()}`;
    };

    return (
        <div className="correlation-view">
            <div className="correlation-header">
                <Link2 size={20} />
                <h3>Correlated Incidents</h3>
            </div>

            <div className="correlation-grid">
                {correlations.map((group) => (
                    <div
                        key={group.correlation_id}
                        className={`correlation-card ${expandedGroup === group.correlation_id ? 'expanded' : ''}`}
                    >
                        <div className="correlation-card-header">
                            <div className="correlation-info">
                                <div className="correlation-title">
                                    <AlertTriangle size={20} className={getSeverityClass(group.max_severity)} />
                                    <span>Distributed Attack Pattern</span>
                                </div>
                                <div className="correlation-meta">
                                    <span className="meta-item">
                                        {group.incident_count} incidents
                                    </span>
                                    <span className="meta-item">
                                        {group.affected_hosts} hosts
                                    </span>
                                </div>
                            </div>

                            <div className="threat-score" style={{ borderColor: getThreatColor(group.threat_score) }}>
                                <TrendingUp size={16} style={{ color: getThreatColor(group.threat_score) }} />
                                <span style={{ color: getThreatColor(group.threat_score) }}>
                                    {Math.round(group.threat_score)}
                                </span>
                            </div>
                        </div>

                        <div className="correlation-card-body">
                            <div className="correlation-stats">
                                <div className="stat-item">
                                    <span className="stat-label">First Detected:</span>
                                    <span className="stat-value">
                                        {new Date(group.first_detected).toLocaleString()}
                                    </span>
                                </div>
                                <div className="stat-item">
                                    <span className="stat-label">Last Detected:</span>
                                    <span className="stat-value">
                                        {new Date(group.last_detected).toLocaleString()}
                                    </span>
                                </div>
                                <div className="stat-item">
                                    <span className="stat-label">Max Severity:</span>
                                    <span className={`stat-value severity-badge ${getSeverityClass(group.max_severity)}`}>
                                        {group.max_severity.toUpperCase()}
                                    </span>
                                </div>
                            </div>

                            <div className="correlation-actions">
                                <button
                                    className="btn-expand"
                                    onClick={() => setExpandedGroup(
                                        expandedGroup === group.correlation_id ? null : group.correlation_id
                                    )}
                                >
                                    {expandedGroup === group.correlation_id ? 'Hide Details' : 'Show Details'}
                                </button>
                                <button
                                    className="btn-resolve"
                                    onClick={() => onResolveGroup(group.correlation_id)}
                                >
                                    <Shield size={16} />
                                    Resolve Group
                                </button>
                            </div>

                            {expandedGroup === group.correlation_id && (
                                <div className="correlation-incidents">
                                    <h4>Correlated Incidents:</h4>
                                    <div className="incidents-list">
                                        {group.incidents && group.incidents.map((incident) => (
                                            <div key={incident.id} className="incident-mini">
                                                <div className="incident-mini-header">
                                                    <span className={`severity-dot ${getSeverityClass(incident.severity.value)}`}></span>
                                                    <span className="incident-title">{incident.title}</span>
                                                </div>
                                                <div className="incident-mini-details">
                                                    <span>Host ID: {incident.host_id}</span>
                                                    {incident.source_ips && incident.source_ips.length > 0 && (
                                                        <span>IPs: {incident.source_ips.slice(0, 2).join(', ')}</span>
                                                    )}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default CorrelationView;
