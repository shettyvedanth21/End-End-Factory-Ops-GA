import { useEffect, useState } from "react";
import { alerts } from "../services/api";
import { AlertCircle, CheckCircle, Clock } from "lucide-react";
import React from 'react';

const AlertList = () => {
    const [items, setItems] = useState([]);

    useEffect(() => {
        alerts.list({ page: 1, per_page: 50 }).then(res => setItems(res.data.data.items));
    }, []);

    const handleResolve = (id) => {
        alerts.resolve(id).then(() => {
            setItems(items.map(i => i.id === id ? { ...i, status: 'resolved' } : i));
        });
    };

    return (
        <div className="card w-full">
            <div className="flex justify-between items-center mb-6">
                <h1>System Alerts</h1>
                <div className="flex gap-2">
                    <button className="btn btn-outline text-sm">Filter: Open</button>
                    <button className="btn btn-outline text-sm">Filter: Critical</button>
                </div>
            </div>

            <div className="flex flex-col gap-4">
                {items.map(alert => (
                    <div key={alert.id} className={`p-4 border rounded-lg flex items-center justify-between ${alert.status === 'open' ? 'border-danger/30 bg-danger/5' : 'border-border-color'
                        }`}>
                        <div className="flex items-center gap-4">
                            <div className={`p-3 rounded-full ${alert.status === 'open' ? 'bg-danger/20 text-danger' : 'bg-success/20 text-success'
                                }`}>
                                {alert.status === 'open' ? <AlertCircle size={24} /> : <CheckCircle size={24} />}
                            </div>

                            <div>
                                <h3 className="text-lg font-semibold flex items-center gap-2">
                                    {alert.rule?.name || "High Pressure Alert"}
                                    <span className="text-sm font-normal text-secondary">({alert.device_id})</span>
                                </h3>
                                <div className="text-sm text-secondary flex items-center gap-4 mt-1">
                                    <span className="flex items-center gap-1">
                                        <Clock size={14} /> {new Date(alert.triggered_at).toLocaleString()}
                                    </span>
                                    <span>Rule ID: {alert.rule_id}</span>
                                </div>

                                {alert.status === 'open' && (
                                    <div className="mt-2 text-sm text-text-primary px-3 py-1 bg-bg-secondary rounded border border-border-color font-mono">
                                        Values: {JSON.stringify(alert.trigger_values)}
                                    </div>
                                )}
                            </div>
                        </div>

                        <div className="flex flex-col gap-2">
                            {alert.status === 'open' && (
                                <button
                                    onClick={() => handleResolve(alert.id)}
                                    className="btn btn-primary text-sm"
                                >
                                    Resolve Issue
                                </button>
                            )}
                            <button className="btn btn-outline text-sm">View Details</button>
                        </div>
                    </div>
                ))}

                {items.length === 0 && (
                    <div className="text-center py-12 text-secondary">
                        No active alerts found. System is healthy.
                    </div>
                )}
            </div>
        </div>
    );
};

export default AlertList;
