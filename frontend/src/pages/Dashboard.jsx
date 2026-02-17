import { useEffect, useState } from "react";
import { devices, alerts } from "../services/api";
import {
    BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid
} from "recharts";
import { Activity, Thermometer, AlertTriangle } from "lucide-react";
import React from 'react';

const Dashboard = () => {
    const [deviceStats, setDeviceStats] = useState({ total: 0, active: 0, inactive: 0 });
    const [recentAlerts, setRecentAlerts] = useState([]);
    const [metrics, setMetrics] = useState([]); // Dummy data for chart

    useEffect(() => {
        const fetchData = async () => {
            try {
                const devRes = await devices.list({ page: 1, per_page: 100 });
                const devs = devRes.data.data.items;
                setDeviceStats({
                    total: devs.length,
                    active: devs.filter(d => d.status === 'active').length,
                    inactive: devs.filter(d => d.status === 'inactive').length
                });

                const alertRes = await alerts.list({ page: 1, per_page: 5 });
                setRecentAlerts(alertRes.data.data.items || []);

                // Mock Chart Data if no aggregated endpoint available yet
                setMetrics([
                    { name: '08:00', value: 400 },
                    { name: '10:00', value: 300 },
                    { name: '12:00', value: 550 },
                    { name: '14:00', value: 450 },
                    { name: '16:00', value: 600 },
                ]);

            } catch (e) {
                console.error("Dashboard load failed", e);
            }
        };
        fetchData();
    }, []);

    return (
        <div className="grid grid-cols-1 gap-6">
            {/* KPI Cards */}
            <div className="grid grid-cols-3 gap-6">
                <div className="card flex items-center gap-4">
                    <div className="p-4 bg-accent-primary/10 rounded-full text-accent-primary">
                        <Activity size={32} />
                    </div>
                    <div>
                        <h3>Active Devices</h3>
                        <p className="text-2xl font-bold">{deviceStats.active} / {deviceStats.total}</p>
                    </div>
                </div>

                <div className="card flex items-center gap-4">
                    <div className="p-4 bg-accent-secondary/10 rounded-full text-accent-secondary">
                        <Thermometer size={32} />
                    </div>
                    <div>
                        <h3>Avg Temperature</h3>
                        <p className="text-2xl font-bold text-success">68.2°C</p>
                    </div>
                </div>

                <div className="card flex items-center gap-4 border-danger/50 bg-danger/5">
                    <div className="p-4 bg-danger/10 rounded-full text-danger">
                        <AlertTriangle size={32} />
                    </div>
                    <div>
                        <h3 className="text-danger">Critical Alerts</h3>
                        <p className="text-2xl font-bold text-danger">{recentAlerts.length}</p>
                    </div>
                </div>
            </div>

            {/* Main Chart Section */}
            <div className="card h-96">
                <h2 className="mb-4">Production Throughput (Last 8h)</h2>
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={metrics}>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                        <XAxis dataKey="name" stroke="var(--text-secondary)" />
                        <YAxis stroke="var(--text-secondary)" />
                        <Tooltip
                            contentStyle={{ backgroundColor: 'var(--bg-secondary)', borderColor: 'var(--border-color)' }}
                            itemStyle={{ color: 'var(--text-primary)' }}
                        />
                        <Bar dataKey="value" fill="var(--accent-primary)" radius={[4, 4, 0, 0]} />
                    </BarChart>
                </ResponsiveContainer>
            </div>

            {/* Recent Alerts Table */}
            <div className="card">
                <h2>Recent Critical Events</h2>
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Device</th>
                            <th>Status</th>
                            <th>Time</th>
                        </tr>
                    </thead>
                    <tbody>
                        {recentAlerts.map(alert => (
                            <tr key={alert.id}>
                                <td>{alert.id.substring(0, 8)}...</td>
                                <td>{alert.device_id}</td>
                                <td>
                                    <span className={`badge ${alert.status === 'open' ? 'badge-alert' : 'badge-active'}`}>
                                        {alert.status}
                                    </span>
                                </td>
                                <td>{new Date(alert.triggered_at).toLocaleString()}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default Dashboard;
