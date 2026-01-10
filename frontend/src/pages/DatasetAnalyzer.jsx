import React, { useState } from 'react';
import { Upload, AlertCircle, CheckCircle, TrendingUp, Zap, Brain, BarChart3, Download, Code, FileText, Database, Cpu, Copy, Search, Filter, Play, Leaf, Trees, Flower, Sprout, BotIcon } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const DatasetAnalyzer = () => {
  const [file, setFile] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [taskType, setTaskType] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [filter, setFilter] = useState('all');
  const navigate = useNavigate();

  const API_BASE_URL = 'http://localhost:5000/api';

  const categories = [
    { value: 'all', label: 'All Models', icon: Flower },
    { value: 'regression', label: 'Growth Regression', icon: Sprout },
    { value: 'classification', label: 'Species Classification', icon: Trees },
    { value: 'clustering', label: 'Habitat Clustering', icon: Flower },
    { value: 'ensemble', label: 'Forest Ensembles', icon: Trees },
    { value: 'neural', label: 'Neural Roots', icon: Leaf },
  ];

  const handleFileUpload = async (event) => {
    const uploadedFile = event.target.files[0];
    if (!uploadedFile) return;

    setFile(uploadedFile);
    setLoading(true);
    setError(null);
    setAnalysis(null);

    const formData = new FormData();
    formData.append('file', uploadedFile);
    if (taskType) {
      formData.append('task_type', taskType);
    }

    try {
      const response = await fetch(`${API_BASE_URL}/analyze`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const result = await response.json();
      
      if (result.success === false) {
        throw new Error(result.error || 'Analysis failed');
      }

      setAnalysis(result);
    } catch (err) {
      setError(err.message || 'Error analyzing dataset. Please check the file format and try again.');
      console.error('Analysis error:', err);
    } finally {
      setLoading(false);
    }
  };

  const downloadPipeline = async () => {
    if (!analysis) return;

    try {
      const response = await fetch(`${API_BASE_URL}/generate_pipeline`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          filename: file.name,
          task_type: analysis.task.task_type || 'classification',
          target_column: analysis.task.target_column || analysis.task.targetColumn,
          features: analysis.features,
          models: analysis.models,
          dataset_info: analysis.dataset_info
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to generate pipeline');
      }

      const result = await response.json();
      
      const blob = new Blob([result.code], { type: 'text/x-python' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'ml_pipeline.py';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      setError('Failed to download pipeline: ' + err.message);
    }
  };

  const formatBytes = (bytes, decimals = 2) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i))) + ' ' + sizes[i];
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(() => {
      // You could add a toast notification here
      console.log('Code copied to clipboard!');
    });
  };

  const getModelSlug = (modelName) => {
    return modelName.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
  };

  const handleModelClick = (model) => {
    const slug = getModelSlug(model.name);
    navigate(`/models/${slug}`);
  };

  const getCategoryColor = (category) => {
    const colors = {
      regression: "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-900/20 dark:text-emerald-300 dark:border-emerald-800/30",
      classification: "bg-violet-50 text-violet-700 border-violet-200 dark:bg-violet-900/20 dark:text-violet-300 dark:border-violet-800/30",
      clustering: "bg-fuchsia-50 text-fuchsia-700 border-fuchsia-200 dark:bg-fuchsia-900/20 dark:text-fuchsia-300 dark:border-fuchsia-800/30",
      ensemble: "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-900/20 dark:text-amber-300 dark:border-amber-800/30",
      neural: "bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-900/20 dark:text-rose-300 dark:border-rose-800/30",
    };
    return colors[category] || "bg-gray-50 text-gray-700 border-gray-200 dark:bg-gray-800 dark:text-gray-300";
  };

  const getIconColor = (category) => {
    const colors = {
      regression: "from-emerald-400 to-green-500",
      classification: "from-violet-400 to-purple-500",
      clustering: "from-fuchsia-400 to-pink-500",
      ensemble: "from-amber-400 to-orange-500",
      neural: "from-rose-400 to-red-500",
    };
    return colors[category] || "from-blue-400 to-purple-500";
  };

  return (
    <div className="min-h-screen bg-white dark:bg-zinc-950">
      {/* Header */}
      <div className="border-b border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900">
        <div className="px-6 py-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Dataset Analyzer
            </h1>
            <p className="text-gray-600 dark:text-zinc-400 mt-1">
              Upload your dataset for AI-powered analysis and model recommendations
            </p>
          </div>

          {/* Search and Filter */}
          <div className="flex items-center gap-4 mt-6">
            <div className="flex-1 relative max-w-md">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Search models..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-9 pr-4 py-2.5 border border-rose-200 dark:border-zinc-700 rounded-xl bg-white/50 dark:bg-zinc-800/50 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-zinc-400 focus:ring-2 focus:ring-emerald-400 focus:border-transparent text-sm transition-all duration-200 backdrop-blur-sm"
              />
            </div>
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-rose-500 dark:text-rose-400" />
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="border border-rose-200 dark:border-zinc-700 rounded-xl px-3 py-2.5 bg-white/50 dark:bg-zinc-800/50 text-gray-900 dark:text-white focus:ring-2 focus:ring-emerald-400 focus:border-transparent text-sm backdrop-blur-sm"
              >
                {categories.map((category) => (
                  <option key={category.value} value={category.value}>
                    {category.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="p-6">
        {/* Upload Section */}
        <div className="bg-white/70 dark:bg-zinc-900/70 backdrop-blur-sm rounded-2xl border border-rose-100 dark:border-zinc-800 p-6 mb-6">
          <div className="mb-6">
            <label className="block text-gray-700 dark:text-zinc-300 mb-2 text-sm font-medium">
              Task Type (Optional)
            </label>
            <div className="flex gap-2 flex-wrap">
              <button
                onClick={() => setTaskType('classification')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                  taskType === 'classification'
                    ? 'bg-violet-500 text-white shadow-sm'
                    : 'bg-violet-50 text-violet-700 border border-violet-200 dark:bg-violet-900/20 dark:text-violet-300 dark:border-violet-800/30'
                }`}
              >
                Classification
              </button>
              <button
                onClick={() => setTaskType('regression')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                  taskType === 'regression'
                    ? 'bg-emerald-500 text-white shadow-sm'
                    : 'bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-900/20 dark:text-emerald-300 dark:border-emerald-800/30'
                }`}
              >
                Regression
              </button>
              <button
                onClick={() => setTaskType('')}
                className="px-4 py-2 rounded-lg text-sm font-medium bg-gray-50 text-gray-700 border border-gray-200 dark:bg-zinc-800/50 dark:text-gray-300 dark:border-zinc-700"
              >
                Auto-detect
              </button>
            </div>
            {taskType && (
              <p className="text-xs text-emerald-600 dark:text-emerald-400 mt-2">
                Task type set to: <span className="font-semibold">{taskType}</span>
              </p>
            )}
          </div>

          <label className="flex flex-col items-center justify-center border-2 border-dashed border-emerald-300 dark:border-emerald-600 rounded-xl p-8 cursor-pointer hover:border-emerald-400 dark:hover:border-emerald-500 hover:bg-emerald-50/50 dark:hover:bg-emerald-900/20 transition-all duration-200">
            <Upload className="w-12 h-12 text-emerald-500 dark:text-emerald-400 mb-4" />
            <span className="text-lg font-medium text-gray-900 dark:text-white mb-2 text-center">
              Upload Dataset (CSV, XLSX, XLS)
            </span>
            <span className="text-sm text-gray-600 dark:text-zinc-400 text-center px-4">
              AI agents will analyze quality, detect task type, suggest features & recommend models
            </span>
            <input 
              type="file" 
              accept=".csv,.xlsx,.xls" 
              onChange={handleFileUpload} 
              className="hidden" 
            />
          </label>
          
          {file && (
            <div className="mt-4 flex items-center justify-between bg-emerald-50 dark:bg-emerald-900/20 rounded-lg p-4 border border-emerald-200 dark:border-emerald-800/30">
              <div className="flex items-center gap-3">
                <FileText className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                <div>
                  <p className="text-gray-900 dark:text-white text-sm font-medium">📄 {file.name}</p>
                  <p className="text-xs text-gray-600 dark:text-zinc-400">
                    {formatBytes(file.size)} • {file.type || 'Unknown type'}
                  </p>
                </div>
              </div>
              {analysis && (
                <button
                  onClick={downloadPipeline}
                  className="flex items-center gap-2 bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-600 hover:to-green-700 text-white px-4 py-2 rounded-lg transition-all duration-200 text-sm font-semibold shadow-sm hover:shadow"
                >
                  <Download className="w-4 h-4" />
                  Download Pipeline
                </button>
              )}
            </div>
          )}
        </div>

        {/* Loading */}
        {loading && (
          <div className="text-center py-12 bg-white/50 dark:bg-zinc-900/50 backdrop-blur-sm rounded-2xl border border-rose-100 dark:border-zinc-800">
            <div className="inline-flex items-center justify-center mb-4">
              <div className="animate-spin rounded-full h-12 w-12 border-4 border-emerald-400 border-t-transparent"></div>
              <Cpu className="w-6 h-6 text-emerald-400 ml-[-30px]" />
            </div>
            <p className="text-gray-700 dark:text-zinc-300 text-sm font-medium">
              🤖 AI Agents processing your dataset...
            </p>
            <p className="text-gray-600 dark:text-zinc-400 text-xs mt-2">
              Analyzing quality → Detecting task → Engineering features → Recommending models
            </p>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="bg-rose-50 dark:bg-rose-900/20 border border-rose-200 dark:border-rose-800/30 rounded-xl p-4 mb-6">
            <div className="flex items-center gap-2 mb-2">
              <AlertCircle className="w-5 h-5 text-rose-500 dark:text-rose-400" />
              <p className="text-rose-700 dark:text-rose-300 font-medium text-sm">Analysis Error</p>
            </div>
            <p className="text-rose-600 dark:text-rose-400 text-sm">{error}</p>
          </div>
        )}

        {/* Analysis Results */}
        {analysis && (
          <div className="space-y-6">
            {/* Dataset Overview */}
            <div className="bg-white/70 dark:bg-zinc-900/70 backdrop-blur-sm rounded-2xl border border-rose-100 dark:border-zinc-800 p-6">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <Database className="w-5 h-5 text-emerald-500 dark:text-emerald-400" />
                Dataset Overview
              </h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                  { label: 'Rows', value: analysis.dataset_info.rows.toLocaleString(), color: 'emerald' },
                  { label: 'Columns', value: analysis.dataset_info.columns, color: 'violet' },
                  { label: 'Task Type', value: analysis.task.task_type?.toUpperCase() || 'UNKNOWN', color: 'amber' },
                  { label: 'Quality Score', value: `${analysis.quality?.quality_score || 'N/A'}/100`, color: 'rose' },
                ].map((item, idx) => (
                  <div key={idx} className="bg-gradient-to-br from-white to-gray-50 dark:from-zinc-800 dark:to-zinc-900 rounded-xl p-4 border border-gray-200 dark:border-zinc-700">
                    <p className="text-xs text-gray-500 dark:text-zinc-400 mb-1">{item.label}</p>
                    <p className={`text-2xl font-bold text-${item.color}-600 dark:text-${item.color}-400`}>
                      {item.value}
                    </p>
                  </div>
                ))}
              </div>
              
              {analysis.dataset_info.memory_usage_mb && (
                <div className="mt-4 text-sm text-emerald-600 dark:text-emerald-400">
                  Estimated memory usage: {analysis.dataset_info.memory_usage_mb} MB
                </div>
              )}
            </div>

            {/* Task Detection */}
            {analysis.task && (
              <div className="bg-white/70 dark:bg-zinc-900/70 backdrop-blur-sm rounded-2xl border border-emerald-200 dark:border-emerald-800/30 p-6">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  <Brain className="w-5 h-5 text-emerald-500 dark:text-emerald-400" />
                  Agent: Task Detection
                </h2>
                
                {analysis.task.task_type ? (
                  <div className="space-y-4">
                    <div className="bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800/30 rounded-xl p-4">
                      <div className="flex items-center justify-between flex-wrap gap-2">
                        <div>
                          <p className="text-xl font-bold text-emerald-600 dark:text-emerald-400 uppercase">
                            {analysis.task.task_type}
                          </p>
                          <p className="text-sm text-emerald-700 dark:text-emerald-300">
                            Target: {analysis.task.target_column || analysis.task.targetColumn || 'Not specified'}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-sm text-emerald-700 dark:text-emerald-300">Confidence</p>
                          <p className="text-xl font-bold text-emerald-600 dark:text-emerald-400">
                            {((analysis.task.confidence || 0) * 100)}%
                          </p>
                        </div>
                      </div>
                    </div>
                    
                    {analysis.task.reasoning && analysis.task.reasoning.length > 0 && (
                      <div className="bg-gray-50 dark:bg-zinc-800/50 rounded-xl p-4">
                        <p className="text-sm font-medium text-gray-700 dark:text-zinc-300 mb-2">Reasoning:</p>
                        <ul className="space-y-1 text-sm text-gray-600 dark:text-zinc-400">
                          {analysis.task.reasoning.map((r, i) => (
                            <li key={i}>• {r}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    
                    {analysis.task.balance_ratio && (
                      <div className="flex items-center gap-4 text-sm">
                        <span className="text-gray-700 dark:text-zinc-300">
                          Balance Ratio: <span className="font-semibold">{analysis.task.balance_ratio}</span>
                        </span>
                        {analysis.task.is_imbalanced && (
                          <span className="px-2 py-1 bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-300 rounded text-xs border border-amber-200 dark:border-amber-800/30">
                            Imbalanced Dataset
                          </span>
                        )}
                      </div>
                    )}
                    
                    {analysis.task.potential_targets && analysis.task.potential_targets.length > 0 && (
                      <div className="mt-4">
                        <p className="text-sm font-medium text-gray-700 dark:text-zinc-300 mb-2">Other Potential Targets:</p>
                        <div className="flex flex-wrap gap-2">
                          {analysis.task.potential_targets.map((target, i) => (
                            <div key={i} className="bg-violet-50 dark:bg-violet-900/20 rounded-lg px-3 py-2 border border-violet-200 dark:border-violet-800/30">
                              <p className="text-xs text-violet-700 dark:text-violet-300 font-medium">{target.column}</p>
                              <p className="text-xs text-violet-600 dark:text-violet-400">Score: {target.score}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-amber-600 dark:text-amber-400">⚠️ Could not automatically detect task type. Please specify manually.</p>
                )}
              </div>
            )}

            {/* Data Quality Agent */}
            {analysis.quality && (
              <div className="bg-white/70 dark:bg-zinc-900/70 backdrop-blur-sm rounded-2xl border border-rose-100 dark:border-zinc-800 p-6">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  <AlertCircle className="w-5 h-5 text-rose-500 dark:text-rose-400" />
                  Agent 1: Data Quality Analysis
                </h2>

                {/* Quality Score */}
                {analysis.quality.quality_score && (
                  <div className="mb-6">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-gray-700 dark:text-zinc-300 text-sm font-medium">Overall Quality Score</span>
                      <span className="text-xl font-bold text-emerald-600 dark:text-emerald-400">{analysis.quality.quality_score}/100</span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-zinc-700 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${
                          analysis.quality.quality_score >= 80 ? 'bg-emerald-500' :
                          analysis.quality.quality_score >= 60 ? 'bg-amber-500' : 'bg-rose-500'
                        }`}
                        style={{ width: `${analysis.quality.quality_score}%` }}
                      ></div>
                    </div>
                  </div>
                )}

                {/* Issues */}
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
                    Quality Issues ({analysis.quality.issues?.length || 0})
                  </h3>
                  {!analysis.quality.issues || analysis.quality.issues.length === 0 ? (
                    <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/20 rounded-xl p-4 border border-emerald-200 dark:border-emerald-800/30">
                      <CheckCircle className="w-5 h-5" />
                      <span className="text-sm font-medium">Excellent! No critical issues detected</span>
                    </div>
                  ) : (
                    <div className="space-y-2 max-h-60 overflow-y-auto pr-2">
                      {analysis.quality.issues.map((issue, idx) => (
                        <div key={idx} className={`p-4 rounded-xl text-sm border ${
                          issue.severity === 'high' ? 'bg-rose-50 dark:bg-rose-900/20 border-rose-200 dark:border-rose-800/30' :
                          issue.severity === 'medium' ? 'bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800/30' : 
                          'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800/30'
                        }`}>
                          <div className="flex items-start justify-between gap-2 flex-wrap">
                            <div className="flex-1 min-w-0">
                              <span className={`font-semibold text-sm ${
                                issue.severity === 'high' ? 'text-rose-700 dark:text-rose-300' :
                                issue.severity === 'medium' ? 'text-amber-700 dark:text-amber-300' : 'text-blue-700 dark:text-blue-300'
                              }`}>
                                {issue.column}
                              </span>
                              <p className="text-gray-900 dark:text-white text-sm mt-1">{issue.message}</p>
                              <p className="text-emerald-600 dark:text-emerald-400 text-xs mt-1">💡 {issue.recommendation}</p>
                            </div>
                            <span className={`text-xs px-2 py-1 rounded font-medium ${
                              issue.severity === 'high' ? 'bg-rose-100 dark:bg-rose-800 text-rose-700 dark:text-rose-300' :
                              issue.severity === 'medium' ? 'bg-amber-100 dark:bg-amber-800 text-amber-700 dark:text-amber-300' : 
                              'bg-blue-100 dark:bg-blue-800 text-blue-700 dark:text-blue-300'
                            }`}>
                              {issue.severity}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Column Statistics */}
                {analysis.quality.stats && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Column Statistics</h3>
                    <div className="overflow-x-auto rounded-xl border border-gray-200 dark:border-zinc-700">
                      <table className="w-full text-sm">
                        <thead className="bg-gray-50 dark:bg-zinc-800">
                          <tr>
                            <th className="text-left py-3 px-4 text-gray-700 dark:text-zinc-300 font-medium">Column</th>
                            <th className="text-left py-3 px-4 text-gray-700 dark:text-zinc-300 font-medium">Type</th>
                            <th className="text-left py-3 px-4 text-gray-700 dark:text-zinc-300 font-medium">Missing</th>
                            <th className="text-left py-3 px-4 text-gray-700 dark:text-zinc-300 font-medium">Unique</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200 dark:divide-zinc-700">
                          {Object.entries(analysis.quality.stats).map(([col, stat]) => (
                            <tr key={col} className="hover:bg-gray-50 dark:hover:bg-zinc-800/50">
                              <td className="py-3 px-4 text-gray-900 dark:text-white font-medium">{col}</td>
                              <td className="py-3 px-4">
                                <span className={`px-2 py-1 rounded text-xs font-medium ${
                                  stat.type === 'continuous' || stat.type === 'numeric' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300' :
                                  stat.type === 'categorical' || stat.type === 'binary' ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300' :
                                  stat.type === 'datetime' ? 'bg-violet-100 dark:bg-violet-900/30 text-violet-700 dark:text-violet-300' :
                                  stat.type === 'identifier' ? 'bg-rose-100 dark:bg-rose-900/30 text-rose-700 dark:text-rose-300' : 
                                  'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300'
                                }`}>
                                  {stat.type}
                                </span>
                              </td>
                              <td className="py-3 px-4 text-gray-900 dark:text-white">{stat.null_percentage || stat.nullPercentage}%</td>
                              <td className="py-3 px-4 text-gray-900 dark:text-white">{stat.unique}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Feature Engineering Agent */}
            {analysis.features && analysis.features.length > 0 && (
              <div className="bg-white/70 dark:bg-zinc-900/70 backdrop-blur-sm rounded-2xl border border-rose-100 dark:border-zinc-800 p-6">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  <Zap className="w-5 h-5 text-amber-500 dark:text-amber-400" />
                  Agent 2: Feature Engineering
                </h2>
                <p className="text-gray-600 dark:text-zinc-400 text-sm mb-4">
                  Top {Math.min(8, analysis.features.length)} recommendations based on data characteristics
                </p>
                <div className="space-y-4">
                  {analysis.features.slice(0, 8).map((feature, idx) => (
                    <div key={idx} className={`rounded-xl p-4 border ${
                      feature.priority === 'high' ? 'bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800/30' :
                      feature.priority === 'medium' ? 'bg-violet-50 dark:bg-violet-900/20 border-violet-200 dark:border-violet-800/30' :
                      'bg-gray-50 dark:bg-zinc-800/50 border-gray-200 dark:border-zinc-700'
                    }`}>
                      <div className="flex items-start justify-between mb-3 gap-2 flex-wrap">
                        <div className="flex-1 min-w-0">
                          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{feature.technique}</h3>
                          <p className="text-sm text-gray-600 dark:text-zinc-400">
                            Column: <span className="font-mono text-emerald-600 dark:text-emerald-400">{feature.column}</span>
                          </p>
                        </div>
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => copyToClipboard(feature.code)}
                            className="p-1.5 hover:bg-gray-100 dark:hover:bg-zinc-700 rounded-lg transition-colors"
                            title="Copy code"
                          >
                            <Copy className="w-4 h-4 text-gray-500 dark:text-zinc-400" />
                          </button>
                          <span className={`text-xs px-2 py-1 rounded font-medium ${
                            feature.priority === 'high' ? 'bg-amber-100 dark:bg-amber-800 text-amber-700 dark:text-amber-300' :
                            feature.priority === 'medium' ? 'bg-violet-100 dark:bg-violet-800 text-violet-700 dark:text-violet-300' :
                            'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300'
                          }`}>
                            {feature.priority}
                          </span>
                        </div>
                      </div>
                      <p className="text-gray-700 dark:text-zinc-300 mb-3 text-sm">💡 {feature.reason}</p>
                      <div className="relative bg-gray-900 rounded-lg p-3 overflow-x-auto">
                        <button
                          onClick={() => copyToClipboard(feature.code)}
                          className="absolute top-2 right-2 p-1.5 bg-gray-800 hover:bg-gray-700 rounded text-xs text-gray-300 hover:text-white transition-colors"
                        >
                          <Copy className="w-3 h-3" />
                        </button>
                        <pre className="text-xs text-emerald-400 whitespace-pre overflow-x-auto">
{`${feature.code}`}
                        </pre>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Model Recommendations */}
            {analysis.models && analysis.models.length > 0 && (
              <div className="bg-white/70 dark:bg-zinc-900/70 backdrop-blur-sm rounded-2xl border border-rose-100 dark:border-zinc-800 p-6">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-emerald-500 dark:text-emerald-400" />
                  Agent 3: Model Recommendations
                </h2>
                <p className="text-gray-600 dark:text-zinc-400 text-sm mb-4">
                  Ranked by suitability score for your dataset
                </p>

                <div className="space-y-4">
                  {analysis.models.map((model, idx) => {
                    const modelCategory = model.category?.toLowerCase() || 'neural';
                    return (
                      <div 
                        key={idx} 
                        onClick={() => handleModelClick(model)}
                        className={`rounded-xl p-5 border cursor-pointer transition-all duration-200 hover:-translate-y-1 hover:shadow-lg dark:hover:shadow-emerald-900/20 group ${
                          idx === 0 ? 'bg-gradient-to-r from-emerald-50 to-white dark:from-emerald-900/20 dark:to-zinc-900 border-2 border-emerald-300 dark:border-emerald-600' :
                          model.priority === 'high' ? 'bg-gradient-to-r from-violet-50/50 to-white dark:from-violet-900/10 dark:to-zinc-900 border border-violet-200 dark:border-violet-800/30' :
                          'bg-white dark:bg-zinc-900 border border-rose-100 dark:border-zinc-800'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
                          <div className="flex items-center gap-3">
                            <div className={`w-10 h-10 bg-gradient-to-br ${getIconColor(modelCategory)} rounded-xl flex items-center justify-center flex-shrink-0 shadow-sm`}>
                              <BotIcon className="w-5 h-5 text-white" />
                            </div>
                            <div>
                              <h3 className="text-lg font-bold text-gray-900 dark:text-white group-hover:text-emerald-600 dark:group-hover:text-emerald-400 flex items-center gap-2">
                                {idx === 0 && <span className="text-amber-500">⭐</span>}
                                {model.name}
                              </h3>
                              <p className="text-xs text-gray-500 dark:text-zinc-400">{model.library || 'Scikit-learn'}</p>
                            </div>
                          </div>
                          <div className="flex gap-2">
                            <span className={`text-xs px-3 py-1 rounded-full font-semibold ${
                              idx === 0 ? 'bg-emerald-100 dark:bg-emerald-800 text-emerald-700 dark:text-emerald-300' :
                              model.priority === 'high' ? 'bg-violet-100 dark:bg-violet-800 text-violet-700 dark:text-violet-300' :
                              'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300'
                            }`}>
                              {idx === 0 ? 'RECOMMENDED' : model.priority?.toUpperCase() || 'HIGH'}
                            </span>
                            <span className="text-xs px-3 py-1 rounded-full bg-blue-100 dark:bg-blue-800 text-blue-700 dark:text-blue-300 font-semibold">
                              Score: {model.score}
                            </span>
                          </div>
                        </div>

                        <p className="text-gray-700 dark:text-zinc-300 mb-4 text-sm">📋 {model.reason}</p>

                        <div className="grid md:grid-cols-2 gap-3 mb-4">
                          <div className="bg-emerald-50 dark:bg-emerald-900/20 rounded-xl p-3 border border-emerald-200 dark:border-emerald-800/30">
                            <p className="text-xs font-semibold text-emerald-700 dark:text-emerald-300 mb-2">✅ Best For:</p>
                            <ul className="text-xs text-emerald-600 dark:text-emerald-400 space-y-1">
                              {model.best_for?.map((item, i) => <li key={i}>• {item}</li>)}
                              {model.bestFor?.map((item, i) => <li key={i}>• {item}</li>)}
                            </ul>
                          </div>
                          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-3 border border-blue-200 dark:border-blue-800/30">
                            <p className="text-xs font-semibold text-blue-700 dark:text-blue-300 mb-2">📌 Requirements:</p>
                            <ul className="text-xs text-blue-600 dark:text-blue-400 space-y-1">
                              {model.requirements?.map((item, i) => <li key={i}>• {item}</li>)}
                            </ul>
                          </div>
                        </div>

                        <div className="grid md:grid-cols-2 gap-3 mb-4">
                          <div>
                            <p className="text-xs font-semibold text-emerald-700 dark:text-emerald-300 mb-1">Pros:</p>
                            <ul className="text-xs text-gray-600 dark:text-zinc-400 space-y-1">
                              {model.pros?.map((pro, i) => <li key={i}>• {pro}</li>)}
                            </ul>
                          </div>
                          <div>
                            <p className="text-xs font-semibold text-rose-700 dark:text-rose-300 mb-1">Cons:</p>
                            <ul className="text-xs text-gray-600 dark:text-zinc-400 space-y-1">
                              {model.cons?.map((con, i) => <li key={i}>• {con}</li>)}
                            </ul>
                          </div>
                        </div>

                        <details className="mb-3">
                          <summary className="text-xs text-violet-600 dark:text-violet-400 cursor-pointer hover:text-violet-700 dark:hover:text-violet-300 flex items-center gap-1">
                            🔧 View Hyperparameters
                          </summary>
                          <div className="mt-2 bg-gray-900 rounded-lg p-3 relative">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                copyToClipboard(JSON.stringify(model.hyperparameters, null, 2));
                              }}
                              className="absolute top-2 right-2 p-1.5 bg-gray-800 hover:bg-gray-700 rounded text-xs text-gray-300 hover:text-white transition-colors"
                            >
                              <Copy className="w-3 h-3" />
                            </button>
                            <pre className="text-xs text-cyan-400 whitespace-pre overflow-x-auto">
                              {JSON.stringify(model.hyperparameters, null, 2)}
                            </pre>
                          </div>
                        </details>

                        <div className="relative bg-gray-900 rounded-lg p-3 overflow-x-auto">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-xs text-gray-400">Implementation Code:</span>
                            <div className="flex items-center gap-2">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  copyToClipboard(model.code);
                                }}
                                className="p-1.5 bg-gray-800 hover:bg-gray-700 rounded text-xs text-gray-300 hover:text-white transition-colors flex items-center gap-1"
                              >
                                <Copy className="w-3 h-3" />
                                <span className="text-xs">Copy</span>
                              </button>
                              <Code className="w-4 h-4 text-purple-400" />
                            </div>
                          </div>
                          <pre className="text-xs text-emerald-400 whitespace-pre overflow-x-auto">
{`${model.code}`}
                          </pre>
                        </div>

                        <div className="mt-4 flex items-center justify-center group-hover:gap-2 transition-all duration-300 pt-4 border-t border-gray-200 dark:border-zinc-800">
                          <span className="flex items-center gap-1.5 text-emerald-600 hover:text-emerald-700 dark:text-emerald-400 text-xs font-medium transition-colors">
                            <Play className="w-3 h-3" />
                            Cultivate This Model
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Complete Pipeline */}
            <div className="bg-gradient-to-r from-emerald-50/50 to-violet-50/50 dark:from-emerald-900/10 dark:to-violet-900/10 backdrop-blur-sm rounded-2xl border-2 border-emerald-300 dark:border-emerald-600 p-6">
              <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                  <Code className="w-5 h-5 text-emerald-500 dark:text-emerald-400" />
                  Complete ML Pipeline
                </h2>
                <div className="flex gap-2">
                  <button
                    onClick={downloadPipeline}
                    className="flex items-center gap-2 bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-600 hover:to-green-700 text-white px-4 py-2 rounded-lg transition-all duration-200 text-sm font-semibold shadow-sm hover:shadow"
                  >
                    <Download className="w-4 h-4" />
                    Download .py
                  </button>
                </div>
              </div>
              <p className="text-gray-600 dark:text-zinc-400 text-sm mb-4">
                Production-ready code with all recommendations applied
              </p>
              <div className="relative bg-gray-900 rounded-lg p-4 overflow-x-auto max-h-96">
                <button
                  onClick={() => copyToClipboard(`# ===== Intelligent ML Pipeline =====
# Dataset: ${file.name}
# Task: ${analysis.task?.task_type?.toUpperCase() || 'UNKNOWN'}
# Target: ${analysis.task?.target_column || analysis.task?.targetColumn || 'N/A'}
# Generated by AI Agents

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import ${analysis.task?.task_type === 'classification' ? 'accuracy_score, classification_report' : 'r2_score, mean_squared_error'}

# Load dataset
df = pd.read_csv('${file.name}')
print(f"Shape: {df.shape}")

# TODO: Add your feature engineering code here based on recommendations above

print("✅ Pipeline template ready!")`)}
                  className="absolute top-3 right-3 p-2 bg-gray-800 hover:bg-gray-700 rounded text-sm text-gray-300 hover:text-white transition-colors flex items-center gap-1"
                >
                  <Copy className="w-4 h-4" />
                  <span className="text-xs">Copy</span>
                </button>
                <pre className="text-xs text-emerald-400 whitespace-pre">
{`# ===== Intelligent ML Pipeline =====
# Dataset: ${file.name}
# Task: ${analysis.task?.task_type?.toUpperCase() || 'UNKNOWN'}
# Target: ${analysis.task?.target_column || analysis.task?.targetColumn || 'N/A'}
# Generated by AI Agents

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import ${analysis.task?.task_type === 'classification' ? 'accuracy_score, classification_report' : 'r2_score, mean_squared_error'}

# Load dataset
df = pd.read_csv('${file.name}')
print(f"Shape: {df.shape}")

# TODO: Add your feature engineering code here based on recommendations above

print("✅ Pipeline template ready!")`}
                </pre>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DatasetAnalyzer;