import { useEffect } from 'react';
import { HashRouter, Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import { LangProvider } from './lang/LangContext';
import { getServiceById } from './data/services';
import HomePage from './pages/HomePage';
import ServicePage from './pages/ServicePage';
import LinkIndexPage from './pages/LinkIndexPage';

/**
 * Query-param alias: `?service=<id>` anywhere in the URL (e.g. a RAG pipeline
 * appending the param) redirects to the matching hash route `/#/<id>`.
 */
function QueryParamAlias() {
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const id = new URLSearchParams(window.location.search).get('service');
    if (id && getServiceById(id)) {
      window.history.replaceState(null, '', window.location.pathname);
      navigate(`/${id}`, { replace: true });
    }
  }, [location.key, navigate]);

  return null;
}

/**
 * Deep-link contract (for the RAG pipeline):
 *   /#/                 → home grid
 *   /#/<service-id>     → that service's detail page
 *   /#/service/<id>     → alias of the above
 *   /?service=<id>      → query-param alias of the above
 *   /#/links            → list of all deep links
 * Unknown ids redirect to home.
 */
export default function App() {
  return (
    <LangProvider>
      <HashRouter>
        <QueryParamAlias />
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/links" element={<LinkIndexPage />} />
          <Route path="/service/:id" element={<ServicePage />} />
          <Route path="/:id" element={<ServicePage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </HashRouter>
    </LangProvider>
  );
}
