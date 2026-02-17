import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useState } from "react";
import React from 'react';

const Login = () => {
    const { login } = useAuth();
    const navigate = useNavigate();
    const [slug, setSlug] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            await login(email, password, slug);
            navigate("/dashboard");
        } catch (err) {
            setError(err.response?.data?.error?.message || "Login failed");
        }
    };

    return (
        <div className="flex items-center justify-center h-full min-h-screen bg-primary">
            <div className="card w-full max-w-md glass">
                <h2 className="text-center text-accent-primary">Secure Access</h2>
                <p className="text-center mb-6 text-secondary">FactoryOps AI</p>

                {error && <div className="badge badge-alert mb-4 w-full text-center">{error}</div>}

                <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                    <div>
                        <label>Factory ID / Slug</label>
                        <input
                            type="text"
                            placeholder="e.g. plant-munich"
                            value={slug}
                            onChange={(e) => setSlug(e.target.value)}
                            required
                        />
                    </div>
                    <div>
                        <label>Email</label>
                        <input
                            type="email"
                            placeholder="operator@factory.com"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                        />
                    </div>
                    <div>
                        <label>Password</label>
                        <input
                            type="password"
                            placeholder="••••••••"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                        />
                    </div>
                    <button type="submit" className="btn btn-primary justify-center mt-2">
                        Sign In
                    </button>
                </form>
            </div>
        </div>
    );
};

export default Login;
