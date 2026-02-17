import { useEffect, useState } from "react";
import { analytics } from "../services/api";
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend } from "recharts";
import { FileText, Play } from "lucide-react";
import React from 'react';

const Analytics = () => {
    const [jobs, setJobs] = useState([]);

    useEffect(() => {
        analytics.jobs().then(res => setJobs(res.data.data.items));
    }, []);

    return (
        <div className="grid grid-cols-1 gap-6">
            <div className="card">
                <div className="flex justify-between items-center mb-6">
                    <h1>Active Jobs</h1>
                    <button className="btn btn-primary text-sm flex gap-2">
                        <Play size={16} /> New Analysis
                    </button>
                </div>

                <table>
                    <thead>
                        <tr>
                            <th>Job ID</th>
                            <th>Name</th>
                            <th>Status</th>
                            <th>Metrics</th>
                        </tr>
                    </thead>
                    <tbody>
                        {jobs.map(job => (
                            <tr key={job.id}>
                                <td>{job.id.substring(0, 8)}</td>
                                <td className="font-medium">{job.name}</td>
                                <td>
                                    <span className={`badge badge-${job.status}`}>
                                        {job.status}
                                    </span>
                                </td>
                                <td>
                                    <small>{JSON.stringify(job.metrics || "-")}</small>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            <div className="grid grid-cols-2 gap-6">
                <div className="card h-64">
                    <h3>Prediction Accuracy</h3>
                    <p className="text-secondary text-sm">Model performance over time</p>
                    {/* Placeholder Chart */}
                </div>
            </div>
        </div>
    );
};

export default Analytics;
