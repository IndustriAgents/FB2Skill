import { Route, Routes } from "react-router-dom";

import Layout from "./components/Layout";
import ConvertPage from "./pages/ConvertPage";
import DiscoverPage from "./pages/DiscoverPage";
import GraphDbPage from "./pages/GraphDbPage";
import OntologyPage from "./pages/OntologyPage";
import VisualizePage from "./pages/VisualizePage";
import { GraphDbProvider } from "./state/graphdb";

export default function App() {
  return (
    <GraphDbProvider>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<ConvertPage />} />
          <Route path="discover" element={<DiscoverPage />} />
          <Route path="graphdb" element={<GraphDbPage />} />
          <Route path="ontology" element={<OntologyPage />} />
          <Route path="visualize" element={<VisualizePage />} />
        </Route>
      </Routes>
    </GraphDbProvider>
  );
}
