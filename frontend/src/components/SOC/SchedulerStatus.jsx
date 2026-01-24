import React from 'react';
import { Play, Pause, Clock, CheckCircle2 } from 'lucide-react';
import './SchedulerStatus.css';

const SchedulerStatus = ({ status, onStart, onStop, loading }) => {
    if (!status) {
        return null;
    }

    const getNextRunDisplay = () => {
        if (!status.running || !status.next_run) {
            return 'N/A';
        }

        const nextRun = new Date(status.next_run);
        const now = new Date();
        const diffMs = nextRun - now;
        const diffMins = Math.floor(diffMs / 60000);

        if (diffMins < 1) {
            return 'Starting soon...';
        } else if (diffMins < 60) {
            return `in ${diffMins} minute${diffMins !== 1 ? 's' : ''}`;
        } else {
            return nextRun.toLocaleTimeString();
        }
    };

    return (
        <div className={`scheduler-status ${status.running ? 'running' : 'stopped'}`}>
            <div className="scheduler-header">
                <div className="scheduler-title">
                    <Clock size={18} />
                    <span>Automated Analysis Scheduler</span>
                </div>
                <div className={`scheduler-badge ${status.running ? 'badge-running' : 'badge-stopped'}`}>
                    {status.running ? (
                        <>
                            <CheckCircle2 size={14} />
                            <span>Active</span>
                        </>
                    ) : (
                        <>
                            <Pause size={14} />
                            <span>Stopped</span>
                        </>
                    )}
                </div>
            </div>

            <div className="scheduler-details">
                <div className="scheduler-info">
                    <div className="info-item">
                        <span className="info-label">Interval:</span>
                        <span className="info-value">{status.interval_minutes} minutes</span>
                    </div>
                    <div className="info-item">
                        <span className="info-label">Next Run:</span>
                        <span className="info-value">{getNextRunDisplay()}</span>
                    </div>
                </div>

                <div className="scheduler-actions">
                    {status.running ? (
                        <button
                            className="btn-stop"
                            onClick={onStop}
                            disabled={loading}
                        >
                            <Pause size={16} />
                            Stop Scheduler
                        </button>
                    ) : (
                        <button
                            className="btn-start"
                            onClick={onStart}
                            disabled={loading}
                        >
                            <Play size={16} />
                            Start Scheduler
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
};

export default SchedulerStatus;
