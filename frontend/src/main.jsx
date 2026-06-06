import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import FormDesigner from './pages/FormDesigner'
import FormRenderer from './pages/FormRenderer'
import ProcessStart from './pages/ProcessStart'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<FormDesigner />} />
        <Route path="/render/:formId" element={<FormRenderer />} />
        <Route path="/process/start" element={<ProcessStart />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
)
