import React, { useState, useEffect } from 'react';
import {
    LayoutDashboard,
    Users,
    AlertTriangle,
    MessageSquare,
    Activity,
    CheckCircle,
    Clock,
    Shield,
    LogOut,
    Camera
} from 'lucide-react';
import axios from 'axios';
import { useAuth } from './AuthContext';

export default function Dashboard() {
    const { currentUser, logout } = useAuth();
    const [activeTab, setActiveTab] = useState('Overview');

    // Live Dashboard States
    const [stats, setStats] = useState([
        { id: 1, title: 'Total Voters Reached', value: '...', icon: <Users size={24} color="#e50914" />, trend: 'Syncing...' },
        { id: 2, title: 'Open Issues', value: '...', icon: <AlertTriangle size={24} color="#ffb800" />, trend: 'Syncing...' },
        { id: 3, title: 'Suggestions Received', value: '...', icon: <MessageSquare size={24} color="#00d26a" />, trend: 'Syncing...' },
        { id: 4, title: 'Active Volunteers', value: '...', icon: <Activity size={24} color="#c0c0c0" />, trend: 'Syncing...' }
    ]);
    const [grievances, setGrievances] = useState([]);
    const [allGrievances, setAllGrievances] = useState([]);
    const [suggestions, setSuggestions] = useState([]);
    const [volunteers, setVolunteers] = useState([]);
    const [analytics, setAnalytics] = useState([]);
    const [voters, setVoters] = useState([]);

    const API_BASE = import.meta.env.VITE_API_BASE || "https://tvk-2-0-1.onrender.com";

    useEffect(() => {
        // Fetch Live Stats from Backend
        axios.get(`${API_BASE}/api/dashboard/stats`)
            .then(res => {
                const liveStats = res.data.stats;
                setStats([
                    { id: 1, title: 'Total Voters Reached', value: liveStats[0].value, icon: <Users size={24} color="#e50914" />, trend: liveStats[0].trend },
                    { id: 2, title: 'Open Issues', value: liveStats[1].value, icon: <AlertTriangle size={24} color="#ffb800" />, trend: liveStats[1].trend },
                    { id: 3, title: 'Suggestions Received', value: liveStats[2].value, icon: <MessageSquare size={24} color="#00d26a" />, trend: liveStats[2].trend },
                    { id: 4, title: 'Active Volunteers', value: liveStats[3].value, icon: <Activity size={24} color="#c0c0c0" />, trend: liveStats[3].trend }
                ]);
            })
            .catch(err => console.error("Error fetching live stats", err));

        // Fetch Data for Tables
        axios.get(`${API_BASE}/api/dashboard/grievances`).then(res => setGrievances(res.data.grievances)).catch(e => console.error(e));
        axios.get(`${API_BASE}/api/dashboard/all_grievances`).then(res => setAllGrievances(res.data.grievances)).catch(e => console.error(e));
        axios.get(`${API_BASE}/api/dashboard/suggestions`).then(res => setSuggestions(res.data.suggestions)).catch(e => console.error(e));
        axios.get(`${API_BASE}/api/dashboard/volunteers`).then(res => setVolunteers(res.data.volunteers)).catch(e => console.error(e));
        axios.get(`${API_BASE}/api/dashboard/booth_analytics`).then(res => setAnalytics(res.data.analytics)).catch(e => console.error(e));
        axios.get(`${API_BASE}/api/dashboard/voters`).then(res => setVoters(res.data.voters)).catch(e => console.error(e));
    }, []);

    const navItems = ['Overview', 'Grievances', 'Suggestions', 'Volunteers', 'Voters', 'Booth Analytics'];

    const handleStatusChange = (id, newStatus) => {
        // Optimistic UI updates
        setAllGrievances(prev => prev.map(item => item.id === id ? { ...item, status: newStatus } : item));
        setSuggestions(prev => prev.map(item => item.id === id ? { ...item, status: newStatus } : item));
        setVolunteers(prev => prev.map(item => item.id === id ? { ...item, status: newStatus } : item));

        axios.post(`${API_BASE}/api/dashboard/update_status`, { id, status: newStatus })
            .then(() => {
                // Refresh data to be sure
                axios.get(`${API_BASE}/api/dashboard/all_grievances`).then(res => setAllGrievances(res.data.grievances));
                axios.get(`${API_BASE}/api/dashboard/suggestions`).then(res => setSuggestions(res.data.suggestions));
                axios.get(`${API_BASE}/api/dashboard/volunteers`).then(res => setVolunteers(res.data.volunteers));
            })
            .catch(err => {
                console.error("Error updating status", err);
            });
    };

    return (
        <>
            <div className="atmospheric-bg"></div>
            <div className="sidebar">
                <div className="brand">
                    <div className="brand-dot"></div>
                    <span>TVK Kavndampalayam</span>
                </div>
                <div className="nav-menu">
                    {navItems.map((item, idx) => (
                        <div
                            key={item}
                            className={`nav-item ${activeTab === item ? 'active' : ''} stagger-${idx + 1}`}
                            onClick={() => setActiveTab(item)}
                        >
                            {item === 'Overview' && <LayoutDashboard size={18} />}
                            {item === 'Grievances' && <AlertTriangle size={18} />}
                            {item === 'Suggestions' && <MessageSquare size={18} />}
                            {item === 'Volunteers' && <Shield size={18} />}
                            {item === 'Voters' && <Users size={18} />}
                            {item === 'Booth Analytics' && <Activity size={18} />}
                            {item}
                        </div>
                    ))}
                </div>
            </div>

            <div className="main-content">
                <div className="header animated">
                    <div>
                        <div style={{ fontSize: '12px', fontWeight: 800, color: 'var(--brand-surge)', marginBottom: '8px', letterSpacing: '0.2em' }}>ADMIN COMMAND CENTER</div>
                        <h1>{activeTab}</h1>
                    </div>
                    <div className="user-profile">
                        <img src={`https://ui-avatars.com/api/?name=${encodeURIComponent(currentUser?.displayName || 'Admin')}&background=e63946&color=fff`} alt="User" style={{ borderRadius: '50%', width: '32px' }} />
                        <div style={{ textAlign: 'right' }}>
                            <div style={{ fontWeight: 700, fontSize: '13px' }}>{currentUser?.displayName || 'Admin'}</div>
                            <div style={{ fontSize: '10px', color: 'var(--text-dim)', fontWeight: 600 }}>{currentUser?.role || 'USER'}</div>
                        </div>
                        <button
                            onClick={logout}
                            className="logout-btn"
                            id="logout-btn"
                            title="Sign Out"
                        >
                            <LogOut size={18} />
                        </button>
                    </div>
                </div>

                {activeTab === 'Overview' && (
                    <div className="animated">
                        <div className="stats-grid">
                            {stats.map((stat, idx) => (
                                <div key={stat.id} className={`stat-card animated stagger-${idx + 1}`}>
                                    <div className="stat-header">
                                        {stat.icon}
                                        <span>{stat.title}</span>
                                    </div>
                                    <div className="stat-value">{stat.value}</div>
                                    <div className="stat-label">{stat.trend}</div>
                                </div>
                            ))}
                        </div>

                        <div className="table-container animated stagger-3">
                            <div className="table-header">Operational Registry: Recent Grievances</div>
                            <table>
                                <thead>
                                    <tr>
                                        <th>Ref ID</th>
                                        <th>Voter Name</th>
                                        <th>Booth / Part</th>
                                        <th>Type</th>
                                        <th>Category</th>
                                        <th>Issue Description</th>
                                        <th>Status</th>
                                        <th>Date Logged</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {grievances.map(issue => (
                                        <tr key={issue.id}>
                                            <td style={{ fontWeight: 800, color: 'var(--text-vivid)', fontFamily: 'var(--font-display)' }}>{issue.id}</td>
                                            <td style={{ fontWeight: 600 }}>{issue.name.toUpperCase()}</td>
                                            <td style={{ color: 'var(--text-dim)' }}>SEC. {issue.booth}</td>
                                            <td>
                                                {issue.type === 'Photo Evidence' ? (
                                                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontWeight: 700, color: '#00d26a' }}>
                                                        <Camera size={14} /> Photo
                                                    </span>
                                                ) : (
                                                    <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-dim)' }}>Grievance</span>
                                                )}
                                            </td>
                                            <td>
                                                <span style={{ fontSize: '11px', fontWeight: 700 }}>{issue.category.toUpperCase()}</span>
                                            </td>
                                            <td style={{ maxWidth: '250px', verticalAlign: 'top' }} title={issue.description}>
                                                <div style={{ fontSize: '12px', lineHeight: '1.5', color: 'var(--text-vivid)', whiteSpace: 'normal', wordWrap: 'break-word', overflow: 'hidden', textOverflow: 'ellipsis', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>
                                                    {issue.description || 'No description provided'}
                                                </div>
                                            </td>
                                            <td>
                                                <span className={`status-badge ${issue.status === 'Open' ? 'status-open' : 'status-resolved'}`}>
                                                    <div style={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: 'currentColor' }}></div>
                                                    {issue.status}
                                                </span>
                                            </td>
                                            <td style={{ fontSize: '12px', color: 'var(--text-dim)' }}>{issue.date}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                {activeTab === 'Grievances' && (
                    <div className="animated">
                        <div className="table-container">
                            <div className="table-header">Master Database: All Grievances</div>
                            <table>
                                <thead>
                                    <tr>
                                        <th>Ref ID</th>
                                        <th>Voter Name</th>
                                        <th>Booth</th>
                                        <th>EPIC / Voter ID</th>
                                        <th>Type</th>
                                        <th>Category</th>
                                        <th>Issue Description</th>
                                        <th>Status Control</th>
                                        <th>Date Logged</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {allGrievances.map(issue => (
                                        <tr key={issue.id}>
                                            <td style={{ fontWeight: 800, color: 'var(--text-vivid)', fontFamily: 'var(--font-display)' }}>{issue.id}</td>
                                            <td style={{ fontWeight: 600 }}>{issue.name.toUpperCase()}</td>
                                            <td>{issue.booth}</td>
                                            <td>
                                                {issue.epic ? (
                                                    <span style={{ fontWeight: 700, color: 'var(--text-vivid)' }}>{issue.epic}</span>
                                                ) : (
                                                    <span style={{ fontSize: '11px', fontWeight: 600, color: '#e50914' }}>GUEST / UNVERIFIED</span>
                                                )}
                                            </td>
                                            <td>
                                                {issue.type === 'Photo Evidence' ? (
                                                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontWeight: 700, color: '#00d26a' }}>
                                                        <Camera size={14} /> Photo
                                                    </span>
                                                ) : (
                                                    <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-dim)' }}>Grievance</span>
                                                )}
                                            </td>
                                            <td>{issue.category}</td>
                                            <td style={{ maxWidth: '300px', verticalAlign: 'top' }}>
                                                <div style={{ fontSize: '13px', lineHeight: '1.6', color: 'var(--text-vivid)', whiteSpace: 'normal', wordWrap: 'break-word' }}>
                                                    {issue.description || 'No description provided'}
                                                </div>
                                            </td>
                                            <td>
                                                <select
                                                    className="status-select"
                                                    value={issue.status}
                                                    onClick={(e) => e.stopPropagation()}
                                                    onChange={(e) => handleStatusChange(issue.id, e.target.value)}
                                                >
                                                    <option value="Open">OPEN</option>
                                                    <option value="In Progress">IN PROGRESS</option>
                                                    <option value="Resolved">RESOLVED</option>
                                                </select>
                                            </td>
                                            <td>{issue.date}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                {activeTab === 'Suggestions' && (
                    <div className="animated">
                        <div className="table-container">
                            <div className="table-header">Community Intelligence: Suggestions</div>
                            <table>
                                <thead>
                                    <tr>
                                        <th>Ref ID</th>
                                        <th>Voter Name</th>
                                        <th>Booth / Part</th>
                                        <th>Strategic Suggestion</th>
                                        <th>Review Status</th>
                                        <th>Logged</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {suggestions.map(s => (
                                        <tr key={s.id}>
                                            <td style={{ fontWeight: 800, color: 'var(--text-vivid)', fontFamily: 'var(--font-display)' }}>{s.id}</td>
                                            <td style={{ fontWeight: 600 }}>{s.name.toUpperCase()}</td>
                                            <td>{s.booth}</td>
                                            <td style={{ maxWidth: '350px', verticalAlign: 'top' }}>
                                                <div style={{ fontSize: '13px', lineHeight: '1.6', color: 'var(--text-vivid)', whiteSpace: 'normal', wordWrap: 'break-word' }}>
                                                    {s.suggestion || 'No suggestion provided'}
                                                </div>
                                            </td>
                                            <td>
                                                <select
                                                    className="status-select"
                                                    value={s.status}
                                                    onClick={(e) => e.stopPropagation()}
                                                    onChange={(e) => handleStatusChange(s.id, e.target.value)}
                                                >
                                                    <option value="Pending">PENDING</option>
                                                    <option value="Reviewing">REVIEWING</option>
                                                    <option value="Approved">APPROVED</option>
                                                    <option value="Rejected">REJECTED</option>
                                                </select>
                                            </td>
                                            <td style={{ whiteSpace: 'nowrap' }}>{s.date}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                {activeTab === 'Volunteers' && (
                    <div className="animated">
                        <div className="table-container">
                            <div className="table-header">Personnel Roster: Registered Volunteers</div>
                            <table>
                                <thead>
                                    <tr>
                                        <th>Ref ID</th>
                                        <th>Volunteer Name</th>
                                        <th>Assigned Booth</th>
                                        <th>Specialized Role</th>
                                        <th>Deployment Status</th>
                                        <th>Onboarded</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {volunteers.map(v => (
                                        <tr key={v.id}>
                                            <td style={{ fontWeight: 800, color: 'var(--text-vivid)', fontFamily: 'var(--font-display)' }}>{v.id}</td>
                                            <td style={{ fontWeight: 600 }}>{v.name.toUpperCase()}</td>
                                            <td>BOOTH {v.booth}</td>
                                            <td style={{ fontWeight: 700, color: 'var(--brand-surge)' }}>{v.role.toUpperCase()}</td>
                                            <td>
                                                <select
                                                    className="status-select"
                                                    value={v.status}
                                                    onClick={(e) => e.stopPropagation()}
                                                    onChange={(e) => handleStatusChange(v.id, e.target.value)}
                                                >
                                                    <option value="Registered">REGISTERED</option>
                                                    <option value="In Review">IN REVIEW</option>
                                                    <option value="Active">ACTIVE</option>
                                                    <option value="Completed">COMPLETED</option>
                                                </select>
                                            </td>
                                            <td>{v.date}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                {activeTab === 'Voters' && (
                    <div className="animated">
                        <div className="table-container">
                            <div className="table-header">Verified Electorate List</div>
                            <table>
                                <thead>
                                    <tr>
                                        <th>Voter identification No.</th>
                                        <th>Full Name</th>
                                        <th>Electoral Sector</th>
                                        <th>District</th>
                                        <th>Registry Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {voters.map(v => (
                                        <tr key={v.id}>
                                            <td style={{ fontWeight: 800, color: 'var(--text-vivid)', fontFamily: 'var(--font-display)' }}>{v.id}</td>
                                            <td style={{ fontWeight: 600 }}>{v.name.toUpperCase()}</td>
                                            <td>SECTOR {v.booth}</td>
                                            <td>{v.district}</td>
                                            <td>
                                                <span className="status-badge status-resolved">
                                                    <div style={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: 'currentColor' }}></div>
                                                    {v.status.toUpperCase()}
                                                </span>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                {activeTab === 'Booth Analytics' && (
                    <div className="animated">
                        <div className="table-container" style={{ maxWidth: '800px', margin: '0 auto' }}>
                            <div className="table-header">Intelligence Report: Regional Incident Density</div>
                            <table>
                                <thead>
                                    <tr>
                                        <th>Electoral Sector</th>
                                        <th>Analytic Incident Count</th>
                                        <th>Action Priority</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {analytics.map((a, i) => (
                                        <tr key={i}>
                                            <td style={{ fontWeight: 800, color: 'var(--text-vivid)', fontSize: '18px', fontFamily: 'var(--font-display)' }}>SECTOR {a.booth}</td>
                                            <td style={{ color: 'var(--brand-surge)', fontWeight: 800, fontSize: '24px', fontFamily: 'var(--font-display)' }}>{a.issues} EVENTS</td>
                                            <td>
                                                <div style={{ height: '4px', width: '100%', background: 'var(--glass-border)', borderRadius: '2px', overflow: 'hidden' }}>
                                                    <div style={{ height: '100%', width: `${Math.min((a.issues / 20) * 100, 100)}%`, background: 'var(--brand-surge)' }}></div>
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}
            </div>
        </>
    );

}
