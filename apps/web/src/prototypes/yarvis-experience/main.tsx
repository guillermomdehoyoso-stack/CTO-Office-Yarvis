import { createRoot } from 'react-dom/client';
import { StrictMode } from 'react';
import { YarvisExperiencePrototype } from './YarvisExperiencePrototype';

createRoot(document.getElementById('root')!).render(
  <StrictMode><YarvisExperiencePrototype /></StrictMode>,
);
