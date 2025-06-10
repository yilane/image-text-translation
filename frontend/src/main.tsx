import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import ImageTranslator from './components/ImageTranslator.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ImageTranslator />
  </StrictMode>,
)
