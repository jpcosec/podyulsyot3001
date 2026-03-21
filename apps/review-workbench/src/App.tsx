import { BrowserRouter, Route, Routes } from "react-router-dom";

import { IntelligentEditorPage } from "./sandbox/pages/IntelligentEditorPage";

function App(): JSX.Element {
  return (
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <Routes>
        <Route path="/sandbox/intelligent_editor" element={<IntelligentEditorPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
