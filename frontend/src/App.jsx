import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Layout from "./pages/Layout";
import DatasetAnalyzer from "./pages/DatasetAnalyzer";
import Home from "./pages/Home";
import SelfHealingPlatform from "./pages/SelfHealingPlatform";

// import HomePage from "./pages/Home";


function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route path="/" element={<SelfHealingPlatform />} />
        <Route path="/analyze" element={<DatasetAnalyzer />} />
      </Route>
    </Routes>
  );
}

export default App;
