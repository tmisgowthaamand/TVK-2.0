import React, { useState, useEffect } from 'react';
import {
    LayoutDashboard,
    Users,
    AlertTriangle,
    MessageSquare,
    Activity,
    CheckCircle,
    Clock,
    Shield
} from 'lucide-react';
import axios from 'axios';

export default function Dashboard() {
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
            <div className="sidebar">
                <div className="brand">
                    <div className="brand-dot"></div>
                    TVK Connect
                </div>
                <div className="nav-menu">
                    {navItems.map(item => (
                        <div
                            key={item}
                            className={`nav-item ${activeTab === item ? 'active' : ''}`}
                            onClick={() => setActiveTab(item)}
                        >
                            {item === 'Overview' && <LayoutDashboard size={20} />}
                            {item === 'Grievances' && <AlertTriangle size={20} />}
                            {item === 'Suggestions' && <MessageSquare size={20} />}
                            {item === 'Volunteers' && <Shield size={20} />}
                            {item === 'Voters' && <Users size={20} />}
                            {item === 'Booth Analytics' && <Activity size={20} />}
                            {item}
                        </div>
                    ))}
                </div>
            </div>

            <div className="main-content">
                <div className="header animated">
                    <h1>{activeTab}</h1>
                    <div className="user-profile" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <img src="https://ui-avatars.com/api/?name=Admin&background=e50914&color=fff" alt="Admin" style={{ borderRadius: '50%', width: '40px' }} />
                        <div>
                            <div style={{ fontWeight: 600 }}>Venkatraman Admin</div>
                            <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Ward Coordinator</div>
                        </div>
                    </div>
                </div>

                {activeTab === 'Overview' && (
                    <div className="animated">
                        <div className="stats-grid">
                            {stats.map(stat => (
                                <div key={stat.id} className="stat-card">
                                    <div className="stat-header">
                                        {stat.icon}
                                        <span style={{ fontSize: '14px' }}>{stat.title}</span>
                                    </div>
                                    <div className="stat-value">{stat.value}</div>
                                    <div className="stat-label">{stat.trend}</div>
                                </div>
                            ))}
                        </div>

                        <div className="table-container">
                            <div className="table-header">Recent Grievances</div>
                            <table>
                                <thead>
                                    <tr>
                                        <th>Ref ID</th>
                                        <th>Voter Name</th>
                                        <th>Booth</th>
                                        <th>Category</th>
                                        <th>Status</th>
                                        <th>Date</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {grievances.map(issue => (
                                        <tr key={issue.id}>
                                            <td style={{ fontWeight: 500, color: '#fff' }}>{issue.id}</td>
                                            <td>{issue.name}</td>
                                            <td>{issue.booth}</td>
                                            <td>{issue.category}</td>
                                            <td>
                                                <span className={`status-badge ${issue.status === 'Open' ? 'status-open' : 'status-resolved'}`}>
                                                    {issue.status === 'Open' ? <Clock size={12} style={{ marginRight: 4, display: 'inline-block', verticalAlign: 'middle' }} /> : <CheckCircle size={12} style={{ marginRight: 4, display: 'inline-block', verticalAlign: 'middle' }} />}
                                                    {issue.status}
                                                </span>
                                            </td>
                                            <td>{issue.date}</td>
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
                            <div className="table-header">All Grievances</div>
                            <table>
                                <thead>
                                    <tr>
                                        <th>Ref ID</th>
                                        <th>Voter Name</th>
                                        <th>Booth</th>
                                        <th>Category</th>
                                        <th>Description</th>
                                        <th>Status</th>
                                        <th>Date</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {allGrievances.map(issue => (
                                        <tr key={issue.id}>
                                            <td style={{ fontWeight: 500, color: '#fff' }}>{issue.id}</td>
                                            <td>{issue.name}</td>
                                            <td>{issue.booth}</td>
                                            <td>{issue.category}</td>
                                            <td>{issue.description || '-'}</td>
                                            <td>
                                                <select
                                                    className="status-select"
                                                    value={issue.status}
                                                    onClick={(e) => e.stopPropagation()}
                                                    onChange={(e) => handleStatusChange(issue.id, e.target.value)}
                                                >
                                                    <option value="Open">Open</option>
                                                    <option value="In Progress">In Progress</option>
                                                    <option value="Resolved">Resolved</option>
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
                            <div className="table-header">Suggestions from Voters</div>
                            <table>
                                <thead>
                                    <tr>
                                        <th>Ref ID</th>
                                        <th>Voter Name</th>
                                        <th>Booth</th>
                                        <th>Suggestion</th>
                                        <th>Status</th>
                                        <th>Date</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {suggestions.map(s => (
                                        <tr key={s.id}>
                                            <td style={{ fontWeight: 500, color: '#fff' }}>{s.id}</td>
                                            <td>{s.name}</td>
                                            <td>{s.booth}</td>
                                            <td>{s.suggestion}</td>
                                            <td>
                                                <select
                                                    className="status-select"
                                                    value={s.status}
                                                    onClick={(e) => e.stopPropagation()}
                                                    onChange={(e) => handleStatusChange(s.id, e.target.value)}
                                                >
                                                    <option value="Pending">Pending</option>
                                                    <option value="Reviewing">Reviewing</option>
                                                    <option value="Approved">Approved</option>
                                                    <option value="Rejected">Rejected</option>
                                                </select>
                                            </td>
                                            <td>{s.date}</td>
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
                            <div className="table-header">Registered Volunteers</div>
                            <table>
                                <thead>
                                    <tr>
                                        <th>Ref ID</th>
                                        <th>Voter Name</th>
                                        <th>Booth</th>
                                        <th>Preferred Role</th>
                                        <th>Status</th>
                                        <th>Date</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {volunteers.map(v => (
                                        <tr key={v.id}>
                                            <td style={{ fontWeight: 500, color: '#fff' }}>{v.id}</td>
                                            <td>{v.name}</td>
                                            <td>{v.booth}</td>
                                            <td>{v.role}</td>
                                            <td>
                                                <select
                                                    className="status-select"
                                                    value={v.status}
                                                    onClick={(e) => e.stopPropagation()}
                                                    onChange={(e) => handleStatusChange(v.id, e.target.value)}
                                                >
                                                    <option value="Registered">Registered</option>
                                                    <option value="In Review">In Review</option>
                                                    <option value="Active">Active</option>
                                                    <option value="Completed">Completed</option>
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
                            <div className="table-header">Verified Voters List</div>
                            <table>
                                <thead>
                                    <tr>
                                        <th>Voter ID</th>
                                        <th>Name</th>
                                        <th>Booth Number</th>
                                        <th>District</th>
                                        <th>Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {voters.map(v => (
                                        <tr key={v.id}>
                                            <td style={{ fontWeight: 500, color: '#fff' }}>{v.id}</td>
                                            <td>{v.name}</td>
                                            <td>Booth {v.booth}</td>
                                            <td>{v.district}</td>
                                            <td>
                                                <span className="status-badge status-resolved">
                                                    <CheckCircle size={12} style={{ marginRight: 4, display: 'inline-block', verticalAlign: 'middle' }} />
                                                    {v.status}
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
                        <div className="table-container" style={{ maxWidth: '600px', margin: '0 auto' }}>
                            <div className="table-header">Top Booths by Grievances</div>
                            <table>
                                <thead>
                                    <tr>
                                        <th>Booth Number</th>
                                        <th>Number of Issues</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {analytics.map((a, i) => (
                                        <tr key={i}>
                                            <td style={{ fontWeight: 500, color: '#fff', fontSize: '16px' }}>Booth {a.booth}</td>
                                            <td style={{ color: '#ffb800', fontWeight: 'bold' }}>{a.issues} Issues</td>
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
