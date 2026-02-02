import React, { useState, useEffect } from 'react';
import './App.css';
import Login from './components/Login';
import Chat from './components/Chat';

function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  // Check if user is already logged in
  useEffect(() => {
    const storedToken = localStorage.getItem('token');
    const storedUser = localStorage.getItem('user');
    
    if (storedToken && storedUser) {
      try {
        setToken(storedToken);
        setCurrentUser(JSON.parse(storedUser));
      } catch (e) {
        // Invalid stored data, clear it
        localStorage.removeItem('token');
        localStorage.removeItem('user');
      }
    }
    
    setLoading(false);
  }, []);

  const handleLoginSuccess = (user, token) => {
    setCurrentUser(user);
    setToken(token);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setCurrentUser(null);
    setToken(null);
  };

  const openAdminDashboard = () => {
    // Open the new admin dashboard in a new tab
    window.open('http://localhost:3001', '_blank');
  };

  if (loading) {
    return (
      <div className="App">
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  // Show login page if not authenticated
  if (!currentUser || !token) {
    return (
      <div className="App">
        <Login onLoginSuccess={handleLoginSuccess} />
      </div>
    );
  }

  return (
    <div className="App">
      <header className="App-header">
        <div className="header-content">
          <h1>🎫 IT Support System</h1>
          <div className="user-info">
            <span className="username">👤 {currentUser.username || currentUser.name}</span>
            <span className={`role-badge ${currentUser.role}`}>
              {currentUser.role}
            </span>
            {currentUser.role === 'admin' && (
              <button className="admin-dashboard-button" onClick={openAdminDashboard}>
                🎛️ Admin Dashboard
              </button>
            )}
            <button className="logout-button" onClick={handleLogout}>
              🚪 Logout
            </button>
          </div>
        </div>
      </header>

      <main className="App-main">
        <Chat user={currentUser} token={token} />
      </main>

      <footer className="App-footer">
        <p>Powered by Google ADK Multi-Agent System</p>
      </footer>
    </div>
  );
}

export default App;