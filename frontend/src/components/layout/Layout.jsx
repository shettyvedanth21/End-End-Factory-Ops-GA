import { useAuth } from "../../context/AuthContext";
import Sidebar from "./Sidebar";
import { Outlet } from "react-router-dom";
import React from 'react';

const Layout = () => {
    const { user, logout } = useAuth();
    if (!user) return null; // Or redirect

    return (
        <div className="flex">
            <Sidebar user={user} logout={logout} />
            <main className="main-content flex-1 bg-primary">
                <div className="navbar mb-8">
                    <h2 className="text-secondary font-bold">Factory: {user.factory_id}</h2>
                    <div className="flex items-center gap-4">
                        <button className="btn btn-secondary">
                            Notifications
                        </button>
                    </div>
                </div>
                <Outlet />
            </main>
        </div>
    );
};

export default Layout;
