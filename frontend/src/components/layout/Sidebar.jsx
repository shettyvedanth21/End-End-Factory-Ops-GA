import { Link, useLocation } from "react-router-dom";
import { LayoutDashboard, Radio, Bell, Settings, FileText, Menu, AlertCircle } from "lucide-react";
import React from 'react';

const Sidebar = ({ user, logout }) => {
    const location = useLocation();
    const isActive = (path) => location.pathname.startsWith(path);

    return (
        <div className="sidebar">
            <div className="sidebar-logo">
                <LayoutDashboard size={24} />
                FactoryOps AI
            </div>

            <nav className="flex flex-col gap-2">
                <Link to="/dashboard" className={`nav-link ${isActive('/dashboard') ? 'active' : ''}`}>
                    <LayoutDashboard size={18} /> Dashboard
                </Link>
                <Link to="/devices" className={`nav-link ${isActive('/devices') ? 'active' : ''}`}>
                    <Radio size={18} /> Devices
                </Link>
                <Link to="/rules" className={`nav-link ${isActive('/rules') ? 'active' : ''}`}>
                    <Settings size={18} /> Rules
                </Link>
                <Link to="/alerts" className={`nav-link ${isActive('/alerts') ? 'active' : ''}`}>
                    <Bell size={18} /> Alerts
                </Link>
                <Link to="/analytics" className={`nav-link ${isActive('/analytics') ? 'active' : ''}`}>
                    <FileText size={18} /> Analytics
                </Link>
            </nav>

            <div className="mt-auto">
                <div className="card p-4 mb-4">
                    <p className="text-secondary text-sm">Logged in as:</p>
                    <strong>{user?.email}</strong> <br />
                    <small className="badge badge-active">{user?.role}</small>
                </div>
                <button onClick={logout} className="btn btn-outline w-full justify-center">
                    Sign Out
                </button>
            </div>
        </div>
    );
};

export default Sidebar;
