import { createContext, useContext, useState, useEffect } from 'react';
import { auth } from '../services/api';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [token, setToken] = useState(localStorage.getItem('token'));
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const initUser = async () => {
            if (token) {
                try {
                    // Verify token/session
                    const res = await auth.me(); // Assume /auth/me returns user profile
                    if (res.data.success) {
                        setUser(res.data.data);
                    }
                } catch (e) {
                    logout();
                }
            }
            setLoading(false);
        };
        initUser();
    }, [token]);

    const login = async (email, password, factory_slug) => {
        try {
            const resp = await auth.login({ email, password, factory_slug });
            if (resp.data.success) {
                const { access_token, user } = resp.data.data;
                localStorage.setItem('token', access_token);
                setToken(access_token);
                setUser(user);
                return true;
            }
        } catch (error) {
            console.error("Login failed", error);
            throw error;
        }
        return false;
    };

    const logout = () => {
        localStorage.removeItem('token');
        setToken(null);
        setUser(null);
        window.location.href = '/login';
    };

    return (
        <AuthContext.Provider value={{ user, token, login, logout, loading }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);
