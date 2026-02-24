import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

// Default admin account
const DEFAULT_USERS = {
    'TVKVIJAY': {
        password: 'TVKVIJAY',
        displayName: 'TVK Kavndampalayam',
        role: 'ADMIN',
        createdAt: new Date().toISOString()
    }
};

function getStoredUsers() {
    try {
        const stored = localStorage.getItem('tvk_users');
        if (stored) {
            const parsed = JSON.parse(stored);
            // Ensure default admin always exists
            if (!parsed['TVKVIJAY']) {
                parsed['TVKVIJAY'] = DEFAULT_USERS['TVKVIJAY'];
                localStorage.setItem('tvk_users', JSON.stringify(parsed));
            } else if (parsed['TVKVIJAY'].displayName === 'TVK Vijay') {
                parsed['TVKVIJAY'].displayName = 'TVK Kavndampalayam';
                localStorage.setItem('tvk_users', JSON.stringify(parsed));
            }
            return parsed;
        }
    } catch (e) {
        console.error('Error reading users from storage', e);
    }
    localStorage.setItem('tvk_users', JSON.stringify(DEFAULT_USERS));
    return { ...DEFAULT_USERS };
}

function saveUsers(users) {
    localStorage.setItem('tvk_users', JSON.stringify(users));
}

export function AuthProvider({ children }) {
    const [currentUser, setCurrentUser] = useState(null);
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        // Check for existing session
        const session = localStorage.getItem('tvk_session') || sessionStorage.getItem('tvk_session');
        if (session) {
            try {
                const sessionData = JSON.parse(session);
                const users = getStoredUsers();
                if (users[sessionData.userId]) {
                    setCurrentUser({
                        userId: sessionData.userId,
                        ...users[sessionData.userId]
                    });
                    setIsAuthenticated(true);
                }
            } catch (e) {
                localStorage.removeItem('tvk_session');
                sessionStorage.removeItem('tvk_session');
            }
        }
        setIsLoading(false);
    }, []);

    const login = (userId, password, rememberMe = false) => {
        const users = getStoredUsers();
        const upperUserId = userId.toUpperCase();

        if (!users[upperUserId]) {
            return { success: false, error: 'User ID not found. Please check your credentials.' };
        }

        if (users[upperUserId].password !== password) {
            return { success: false, error: 'Incorrect password. Please try again.' };
        }

        const userData = {
            userId: upperUserId,
            ...users[upperUserId]
        };

        setCurrentUser(userData);
        setIsAuthenticated(true);

        const sessionData = JSON.stringify({ userId: upperUserId, loginAt: new Date().toISOString() });
        if (rememberMe) {
            localStorage.setItem('tvk_session', sessionData);
        } else {
            sessionStorage.setItem('tvk_session', sessionData);
        }

        return { success: true };
    };

    const logout = () => {
        setCurrentUser(null);
        setIsAuthenticated(false);
        localStorage.removeItem('tvk_session');
        sessionStorage.removeItem('tvk_session');
    };

    const register = (userId, password, displayName) => {
        const users = getStoredUsers();
        const upperUserId = userId.toUpperCase();

        if (users[upperUserId]) {
            return { success: false, error: 'This User ID is already taken. Please choose another.' };
        }

        if (userId.length < 3) {
            return { success: false, error: 'User ID must be at least 3 characters long.' };
        }

        if (password.length < 4) {
            return { success: false, error: 'Password must be at least 4 characters long.' };
        }

        users[upperUserId] = {
            password,
            displayName: displayName || upperUserId,
            role: 'USER',
            createdAt: new Date().toISOString()
        };

        saveUsers(users);
        return { success: true };
    };

    const changePassword = (userId, currentPassword, newPassword) => {
        const users = getStoredUsers();
        const upperUserId = userId.toUpperCase();

        if (!users[upperUserId]) {
            return { success: false, error: 'User ID not found.' };
        }

        if (users[upperUserId].password !== currentPassword) {
            return { success: false, error: 'Current password is incorrect.' };
        }

        if (newPassword.length < 4) {
            return { success: false, error: 'New password must be at least 4 characters long.' };
        }

        users[upperUserId].password = newPassword;
        saveUsers(users);
        return { success: true };
    };

    const resetPassword = (userId) => {
        const users = getStoredUsers();
        const upperUserId = userId.toUpperCase();

        if (!users[upperUserId]) {
            return { success: false, error: 'User ID not found. Cannot reset password.' };
        }

        // Reset password to the userId itself
        const newPassword = upperUserId;
        users[upperUserId].password = newPassword;
        saveUsers(users);
        return { success: true, newPassword };
    };

    return (
        <AuthContext.Provider value={{
            currentUser,
            isAuthenticated,
            isLoading,
            login,
            logout,
            register,
            changePassword,
            resetPassword
        }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}
