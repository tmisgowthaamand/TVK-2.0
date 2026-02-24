import React, { useState } from 'react';
import { useAuth } from './AuthContext';
import {
    LogIn,
    KeyRound,
    ShieldQuestion,
    Eye,
    EyeOff,
    ArrowLeft,
    CheckCircle,
    AlertCircle,
    Lock,
    User
} from 'lucide-react';
import tvkLogo from './assets/tvk_logo.png';

export default function LoginPage() {
    const { login, changePassword, resetPassword } = useAuth();

    // Views: 'login' | 'changePassword' | 'forgotPassword'
    const [view, setView] = useState('login');

    // Form states
    const [userId, setUserId] = useState(() => localStorage.getItem('tvk_remembered_userId') || '');
    const [password, setPassword] = useState(() => localStorage.getItem('tvk_remembered_password') || '');
    const [rememberMe, setRememberMe] = useState(() => localStorage.getItem('tvk_remembered_userId') ? true : false);
    const [currentPassword, setCurrentPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [showCurrentPassword, setShowCurrentPassword] = useState(false);
    const [showNewPassword, setShowNewPassword] = useState(false);

    // Feedback
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    const clearForm = () => {
        setUserId(localStorage.getItem('tvk_remembered_userId') || '');
        setPassword(localStorage.getItem('tvk_remembered_password') || '');
        setCurrentPassword('');
        setNewPassword('');
        setRememberMe(localStorage.getItem('tvk_remembered_userId') ? true : false);
        setShowPassword(false);
        setShowCurrentPassword(false);
        setShowNewPassword(false);
        setError('');
        setSuccess('');
    };

    const switchView = (newView) => {
        clearForm();
        setView(newView);
    };

    const handleLogin = (e) => {
        e.preventDefault();
        setError('');
        setSuccess('');
        setIsSubmitting(true);

        setTimeout(() => {
            const result = login(userId, password, rememberMe);
            if (!result.success) {
                setError(result.error);
            } else {
                if (rememberMe) {
                    localStorage.setItem('tvk_remembered_userId', userId);
                    localStorage.setItem('tvk_remembered_password', password);
                } else {
                    localStorage.removeItem('tvk_remembered_userId');
                    localStorage.removeItem('tvk_remembered_password');
                }
            }
            setIsSubmitting(false);
        }, 600);
    };



    const handleChangePassword = (e) => {
        e.preventDefault();
        setError('');
        setSuccess('');
        setIsSubmitting(true);

        setTimeout(() => {
            const result = changePassword(userId, currentPassword, newPassword);
            if (result.success) {
                setSuccess('Password changed successfully! Redirecting to sign in...');
                setTimeout(() => switchView('login'), 2000);
            } else {
                setError(result.error);
            }
            setIsSubmitting(false);
        }, 600);
    };

    const handleForgotPassword = (e) => {
        e.preventDefault();
        setError('');
        setSuccess('');
        setIsSubmitting(true);

        setTimeout(() => {
            const result = resetPassword(userId);
            if (result.success) {
                setSuccess(`Password reset successfully! Your new password is: ${result.newPassword}`);
            } else {
                setError(result.error);
            }
            setIsSubmitting(false);
        }, 600);
    };

    const renderLoginForm = () => (
        <form onSubmit={handleLogin} className="login-form" id="login-form">
            <div className="login-input-group">
                <label htmlFor="login-userid">User ID</label>
                <div className="login-input-wrapper">
                    <User size={18} className="login-input-icon" />
                    <input
                        id="login-userid"
                        type="text"
                        placeholder="Enter your User ID"
                        value={userId}
                        onChange={(e) => setUserId(e.target.value)}
                        required
                        autoFocus
                    />
                </div>
            </div>

            <div className="login-input-group">
                <label htmlFor="login-password">Password</label>
                <div className="login-input-wrapper">
                    <Lock size={18} className="login-input-icon" />
                    <input
                        id="login-password"
                        type={showPassword ? 'text' : 'password'}
                        placeholder="Enter your password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                    />
                    <button
                        type="button"
                        className="login-toggle-password"
                        onClick={() => setShowPassword(!showPassword)}
                        tabIndex={-1}
                    >
                        {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                </div>
            </div>

            <div className="login-checkbox-group" onClick={() => setRememberMe(!rememberMe)}>
                <input
                    type="checkbox"
                    id="remember-me"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    onClick={(e) => e.stopPropagation()}
                />
                <label htmlFor="remember-me">Remember me</label>
            </div>

            <button type="submit" className="login-btn login-btn-primary" id="login-submit" disabled={isSubmitting}>
                {isSubmitting ? (
                    <span className="login-spinner"></span>
                ) : (
                    <>
                        <LogIn size={18} />
                        SIGN IN
                    </>
                )}
            </button>

            <div className="login-actions">
                <button type="button" className="login-link" onClick={() => switchView('forgotPassword')} id="forgot-password-link">
                    <ShieldQuestion size={14} />
                    Forgot Password?
                </button>
                <button type="button" className="login-link" onClick={() => switchView('changePassword')} id="change-password-link">
                    <KeyRound size={14} />
                    Change Password
                </button>
            </div>


        </form>
    );



    const renderChangePasswordForm = () => (
        <form onSubmit={handleChangePassword} className="login-form" id="change-password-form">
            <div className="login-input-group">
                <label htmlFor="change-userid">User ID</label>
                <div className="login-input-wrapper">
                    <User size={18} className="login-input-icon" />
                    <input
                        id="change-userid"
                        type="text"
                        placeholder="Enter your User ID"
                        value={userId}
                        onChange={(e) => setUserId(e.target.value)}
                        required
                        autoFocus
                    />
                </div>
            </div>

            <div className="login-input-group">
                <label htmlFor="change-current-password">Current Password</label>
                <div className="login-input-wrapper">
                    <Lock size={18} className="login-input-icon" />
                    <input
                        id="change-current-password"
                        type={showCurrentPassword ? 'text' : 'password'}
                        placeholder="Enter current password"
                        value={currentPassword}
                        onChange={(e) => setCurrentPassword(e.target.value)}
                        required
                    />
                    <button
                        type="button"
                        className="login-toggle-password"
                        onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                        tabIndex={-1}
                    >
                        {showCurrentPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                </div>
            </div>

            <div className="login-input-group">
                <label htmlFor="change-new-password">New Password</label>
                <div className="login-input-wrapper">
                    <Lock size={18} className="login-input-icon" />
                    <input
                        id="change-new-password"
                        type={showNewPassword ? 'text' : 'password'}
                        placeholder="Enter new password (min 4 chars)"
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        required
                    />
                    <button
                        type="button"
                        className="login-toggle-password"
                        onClick={() => setShowNewPassword(!showNewPassword)}
                        tabIndex={-1}
                    >
                        {showNewPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                </div>
            </div>

            <button type="submit" className="login-btn login-btn-primary" id="change-password-submit" disabled={isSubmitting}>
                {isSubmitting ? (
                    <span className="login-spinner"></span>
                ) : (
                    <>
                        <KeyRound size={18} />
                        CHANGE PASSWORD
                    </>
                )}
            </button>

            <button type="button" className="login-btn login-btn-back" onClick={() => switchView('login')}>
                <ArrowLeft size={18} />
                BACK TO SIGN IN
            </button>
        </form>
    );

    const renderForgotPasswordForm = () => (
        <form onSubmit={handleForgotPassword} className="login-form" id="forgot-password-form">
            <p className="login-info-text">
                Enter your User ID below. Your password will be reset to your User ID.
            </p>

            <div className="login-input-group">
                <label htmlFor="forgot-userid">User ID</label>
                <div className="login-input-wrapper">
                    <User size={18} className="login-input-icon" />
                    <input
                        id="forgot-userid"
                        type="text"
                        placeholder="Enter your User ID"
                        value={userId}
                        onChange={(e) => setUserId(e.target.value)}
                        required
                        autoFocus
                    />
                </div>
            </div>

            <button type="submit" className="login-btn login-btn-primary" id="forgot-password-submit" disabled={isSubmitting}>
                {isSubmitting ? (
                    <span className="login-spinner"></span>
                ) : (
                    <>
                        <ShieldQuestion size={18} />
                        RESET PASSWORD
                    </>
                )}
            </button>

            <button type="button" className="login-btn login-btn-back" onClick={() => switchView('login')}>
                <ArrowLeft size={18} />
                BACK TO SIGN IN
            </button>
        </form>
    );

    const viewConfig = {
        login: { title: 'SIGN IN', subtitle: 'Access your Command Center', render: renderLoginForm },
        changePassword: { title: 'CHANGE PASSWORD', subtitle: 'Update your credentials', render: renderChangePasswordForm },
        forgotPassword: { title: 'FORGOT PASSWORD', subtitle: 'Reset your access', render: renderForgotPasswordForm },
    };

    const current = viewConfig[view];

    return (
        <div className="login-page">
            <div className="login-bg-pattern" style={{ backgroundImage: `url(${tvkLogo})` }}></div>
            <div className="login-atmospheric-glow"></div>
            <div className="login-atmospheric-glow login-glow-2"></div>

            <div className="login-container animated">
                {/* Left Panel - Branding */}
                <div className="login-brand-panel">
                    <div className="login-brand-content">
                        <img src={tvkLogo} alt="TVK" className="login-logo" />
                        <h1 className="login-brand-title">TVK <span>KAVNDAMPALAYAM</span></h1>
                        <p className="login-brand-subtitle">Command Center Dashboard</p>
                        <div className="login-brand-features">
                            <div className="login-feature-item">
                                <CheckCircle size={16} />
                                <span>Real-time Voter Analytics</span>
                            </div>
                            <div className="login-feature-item">
                                <CheckCircle size={16} />
                                <span>Grievance Management</span>
                            </div>
                            <div className="login-feature-item">
                                <CheckCircle size={16} />
                                <span>Booth Intelligence</span>
                            </div>
                        </div>
                    </div>
                    <div className="login-brand-footer">
                        <p>&copy; 2026 TVK Kavndampalayam. All rights reserved.</p>
                    </div>
                </div>

                {/* Right Panel - Forms */}
                <div className="login-form-panel">
                    <div className="login-form-content">
                        <div className="login-form-header">
                            <div className="login-header-dot"></div>
                            <h2 className="login-form-title">{current.title}</h2>
                            <p className="login-form-subtitle">{current.subtitle}</p>
                        </div>

                        {error && (
                            <div className="login-alert login-alert-error animated">
                                <AlertCircle size={16} />
                                <span>{error}</span>
                            </div>
                        )}

                        {success && (
                            <div className="login-alert login-alert-success animated">
                                <CheckCircle size={16} />
                                <span>{success}</span>
                            </div>
                        )}

                        {current.render()}
                    </div>
                </div>
            </div>
        </div>
    );
}
