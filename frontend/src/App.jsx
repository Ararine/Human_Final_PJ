import { StrictMode } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { BrowserRouter } from "react-router-dom";

import Home from "./pages/Home";
/* css */
import "./css/index.css";
import "./css/App.css";
import { URL } from "./constants";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path={URL.HOME} element={<Home />} />
        <Route path="*" element={<Navigate to={URL.HOME} />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
