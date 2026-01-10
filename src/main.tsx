import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import 'github-markdown-css/github-markdown-light.css'
import './styles/markdown.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
