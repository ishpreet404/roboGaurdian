import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout.jsx';
import HomePage from './pages/HomePage.jsx';
import ControlPage from './pages/ControlPage.jsx';
import AlertsPage from './pages/AlertsPage.jsx';
import AssistantPage from './pages/AssistantPage.jsx';
import LandingPage from './pages/LandingPage.jsx';
import { RobotProvider } from './context/RobotContext.jsx';

const App = () => {
  return (
    <RobotProvider>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route element={<Layout />}>
          <Route path="/dashboard" element={<HomePage />} />
          <Route path="/control" element={<ControlPage />} />
          <Route path="/assistant" element={<AssistantPage />} />
          <Route path="/alerts" element={<AlertsPage />} />
        </Route>
      </Routes>
    </RobotProvider>
  );
};

export default App;
