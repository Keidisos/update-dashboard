import React from 'react';
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Clock } from 'lucide-react';
import './SOCTimeline.css';

const SOCTimeline = ({ timeline, hours = 24 }) => {
    if (!timeline || timeline.length === 0) {
        return (
            <div className="soc-timeline-empty">
                <Clock size={48} />
                <p>No incidents in the last {hours} hours</p>
            </div>
        );
    }

    // Transform data for recharts
    const chartData = timeline.map(item => {
        const date = new Date(item.timestamp);
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');

        return {
            time: `${hours}:${minutes}`,
            fullDate: item.timestamp,
            low: item.counts.low || 0,
            medium: item.counts.medium || 0,
            high: item.counts.high || 0,
            critical: item.counts.critical || 0,
            total: (item.counts.low || 0) + (item.counts.medium || 0) + (item.counts.high || 0) + (item.counts.critical || 0)
        };
    });

    return (
        <div className="soc-timeline">
            <div className="timeline-header">
                <Clock size={20} />
                <h3>Incident Timeline ({hours}h)</h3>
            </div>

            <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                    <defs>
                        <linearGradient id="colorCritical" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#dc3545" stopOpacity={0.8} />
                            <stop offset="95%" stopColor="#dc3545" stopOpacity={0} />
                        </linearGradient>
                        <linearGradient id="colorHigh" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#fd7e14" stopOpacity={0.8} />
                            <stop offset="95%" stopColor="#fd7e14" stopOpacity={0} />
                        </linearGradient>
                        <linearGradient id="colorMedium" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#ffc107" stopOpacity={0.8} />
                            <stop offset="95%" stopColor="#ffc107" stopOpacity={0} />
                        </linearGradient>
                        <linearGradient id="colorLow" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#6c757d" stopOpacity={0.8} />
                            <stop offset="95%" stopColor="#6c757d" stopOpacity={0} />
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                    <XAxis
                        dataKey="time"
                        stroke="#ccc"
                        tick={{ fill: '#ccc', fontSize: 12 }}
                    />
                    <YAxis
                        stroke="#ccc"
                        tick={{ fill: '#ccc', fontSize: 12 }}
                        label={{ value: 'Incidents', angle: -90, position: 'insideLeft', fill: '#ccc' }}
                    />
                    <Tooltip
                        contentStyle={{
                            backgroundColor: '#1e1e1e',
                            border: '1px solid #444',
                            borderRadius: '4px',
                            color: '#fff'
                        }}
                        labelFormatter={(value) => `Time: ${value}`}
                    />
                    <Legend
                        wrapperStyle={{ color: '#ccc' }}
                        iconType="square"
                    />
                    <Area
                        type="monotone"
                        dataKey="critical"
                        stackId="1"
                        stroke="#dc3545"
                        fillOpacity={1}
                        fill="url(#colorCritical)"
                        name="Critical"
                    />
                    <Area
                        type="monotone"
                        dataKey="high"
                        stackId="1"
                        stroke="#fd7e14"
                        fillOpacity={1}
                        fill="url(#colorHigh)"
                        name="High"
                    />
                    <Area
                        type="monotone"
                        dataKey="medium"
                        stackId="1"
                        stroke="#ffc107"
                        fillOpacity={1}
                        fill="url(#colorMedium)"
                        name="Medium"
                    />
                    <Area
                        type="monotone"
                        dataKey="low"
                        stackId="1"
                        stroke="#6c757d"
                        fillOpacity={1}
                        fill="url(#colorLow)"
                        name="Low"
                    />
                </AreaChart>
            </ResponsiveContainer>

            <div className="timeline-stats">
                <div className="timeline-stat">
                    <span className="stat-label">Total Incidents:</span>
                    <span className="stat-value">{chartData.reduce((sum, d) => sum + d.total, 0)}</span>
                </div>
                <div className="timeline-stat critical-stat">
                    <span className="stat-label">Critical:</span>
                    <span className="stat-value">{chartData.reduce((sum, d) => sum + d.critical, 0)}</span>
                </div>
                <div className="timeline-stat high-stat">
                    <span className="stat-label">High:</span>
                    <span className="stat-value">{chartData.reduce((sum, d) => sum + d.high, 0)}</span>
                </div>
            </div>
        </div>
    );
};

export default SOCTimeline;
