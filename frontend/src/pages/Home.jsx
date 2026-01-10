import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import {
  TrendingUp,
  BarChart3,
  Database,
  Cpu,
  Cloud,
  Shield,
  Zap,
  Leaf,
  Trees,
  Flower,
  Sprout,
  PlayCircle,
  Upload,
  Download,
  Users,
  BarChart,
  PieChart,
  LineChart,
  Target,
  Clock,
  CheckCircle,
  ChevronRight,
  Sparkles,
  Brain,
  Server,
  Activity,
  ArrowUpRight,
  ArrowDownRight,
  Globe,
  Layers,
  Filter,
  Search,
  Bell,
  Settings,
} from "lucide-react";
import { BarChart as RechartsBarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart as RechartsPieChart, Pie, Cell, LineChart as RechartsLineChart, Line } from "recharts";

const Home = () => {
  const [activeTab, setActiveTab] = useState("overview");
  const [stats, setStats] = useState({
    totalModels: 0,
    activeTraining: 0,
    datasets: 0,
    accuracy: 0,
  });

  // Simulate data loading
  useEffect(() => {
    const timer = setTimeout(() => {
      setStats({
        totalModels: 24,
        activeTraining: 3,
        datasets: 156,
        accuracy: 94.2,
      });
    }, 300);
    return () => clearTimeout(timer);
  }, []);

  // Chart data - recent model performance
  const performanceData = [
    { name: "Mon", accuracy: 88, speed: 4.2 },
    { name: "Tue", accuracy: 92, speed: 3.8 },
    { name: "Wed", accuracy: 89, speed: 4.5 },
    { name: "Thu", accuracy: 94, speed: 3.2 },
    { name: "Fri", accuracy: 91, speed: 4.0 },
    { name: "Sat", accuracy: 95, speed: 3.5 },
    { name: "Sun", accuracy: 96, speed: 3.1 },
  ];

  // Model type distribution
  const modelDistribution = [
    { name: "Regression", value: 35, color: "#10b981" },
    { name: "Classification", value: 28, color: "#8b5cf6" },
    { name: "Clustering", value: 18, color: "#ec4899" },
    { name: "Neural", value: 12, color: "#ef4444" },
    { name: "Ensemble", value: 7, color: "#f59e0b" },
  ];

  // Top performing models
  const topModels = [
    { id: 1, name: "Random Forest", accuracy: 96.8, speed: "Fast", type: "Ensemble", icon: Trees, color: "text-emerald-500", bg: "bg-emerald-50" },
    { id: 2, name: "XGBoost", accuracy: 95.2, speed: "Very Fast", type: "Boosting", icon: Zap, color: "text-blue-500", bg: "bg-blue-50" },
    { id: 3, name: "Neural Network", accuracy: 94.7, speed: "Medium", type: "Deep Learning", icon: Brain, color: "text-purple-500", bg: "bg-purple-50" },
    { id: 4, name: "SVM", accuracy: 93.1, speed: "Slow", type: "Classification", icon: Target, color: "text-rose-500", bg: "bg-rose-50" },
  ];

  // Recent activity
  const recentActivity = [
    { id: 1, action: "Model Trained", model: "Linear Regression", user: "Alex Chen", time: "10 min ago", status: "success" },
    { id: 2, action: "Dataset Uploaded", model: "Iris Dataset", user: "Maria Garcia", time: "25 min ago", status: "success" },
    { id: 3, action: "Model Deployed", model: "Random Forest", user: "System", time: "1 hour ago", status: "deployed" },
    { id: 4, action: "Training Started", model: "Neural Network", user: "Raj Patel", time: "2 hours ago", status: "processing" },
  ];

  // Quick actions
  const quickActions = [
    { title: "Train New Model", description: "Upload data and train", icon: PlayCircle, color: "bg-gradient-to-br from-emerald-400 to-emerald-600", link: "/models" },
    { title: "Upload Dataset", description: "CSV, Excel, or JSON", icon: Upload, color: "bg-gradient-to-br from-blue-400 to-blue-600", link: "/datasets" },
    { title: "View Models", description: "Browse all algorithms", icon: Cpu, color: "bg-gradient-to-br from-purple-400 to-purple-600", link: "/models" },
    { title: "Analytics", description: "Performance insights", icon: BarChart, color: "bg-gradient-to-br from-rose-400 to-rose-600", link: "/analytics" },
  ];

  // Features
  const features = [
    {
      icon: Shield,
      title: "Enterprise Security",
      description: "Bank-level encryption and secure model deployment",
      color: "text-blue-500",
      bg: "bg-blue-50",
    },
    {
      icon: Cloud,
      title: "Cloud Native",
      description: "Scale effortlessly with cloud infrastructure",
      color: "text-emerald-500",
      bg: "bg-emerald-50",
    },
    {
      icon: Zap,
      title: "High Performance",
      description: "Optimized algorithms for fast training",
      color: "text-amber-500",
      bg: "bg-amber-50",
    },
    {
      icon: Users,
      title: "Team Collaboration",
      description: "Share models and datasets with your team",
      color: "text-purple-500",
      bg: "bg-purple-50",
    },
  ];

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white dark:bg-zinc-800 border border-gray-200 dark:border-zinc-700 rounded-lg p-3 shadow-lg">
          <p className="text-gray-900 dark:text-white font-medium">{label}</p>
          {payload.map((entry, index) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {entry.value}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-white via-emerald-50/30 to-emerald-100/20 dark:from-zinc-950 dark:via-emerald-950/10 dark:to-emerald-900/5">
      {/* Header */}
      <div className="border-b border-gray-200 dark:border-zinc-800 bg-white/80 dark:bg-zinc-900/80 backdrop-blur-sm">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                <div className="w-8 h-8 bg-gradient-to-br from-emerald-400 to-emerald-600 rounded-lg flex items-center justify-center">
                  <Leaf className="w-4 h-4 text-white" />
                </div>
                Lotus AI
              </h1>
              <p className="text-sm text-gray-600 dark:text-zinc-400 mt-1">
                Intelligent Machine Learning Platform
              </p>
            </div>
            <div className="flex items-center gap-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <input
                  type="text"
                  placeholder="Search models, datasets..."
                  className="pl-9 pr-4 py-2 border border-rose-200 dark:border-zinc-700 rounded-xl bg-white/50 dark:bg-zinc-800/50 text-sm w-64"
                />
              </div>
              <button className="p-2 rounded-lg border border-rose-200 dark:border-zinc-700 bg-white/50 dark:bg-zinc-800/50">
                <Bell className="w-4 h-4 text-gray-600 dark:text-zinc-400" />
              </button>
              <button className="p-2 rounded-lg border border-rose-200 dark:border-zinc-700 bg-white/50 dark:bg-zinc-800/50">
                <Settings className="w-4 h-4 text-gray-600 dark:text-zinc-400" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="px-6 py-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                Welcome back, Alex 👋
              </h2>
              <p className="text-gray-600 dark:text-zinc-400 mt-1">
                Here's what's happening with your models today
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500 dark:text-zinc-500">Last updated: Just now</span>
              <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></div>
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {[
            { label: "Total Models", value: stats.totalModels, icon: Cpu, change: "+12%", trend: "up", color: "bg-gradient-to-br from-blue-400 to-blue-600" },
            { label: "Active Training", value: stats.activeTraining, icon: Activity, change: "+3", trend: "up", color: "bg-gradient-to-br from-emerald-400 to-emerald-600" },
            { label: "Datasets", value: stats.datasets, icon: Database, change: "+24", trend: "up", color: "bg-gradient-to-br from-purple-400 to-purple-600" },
            { label: "Avg Accuracy", value: `${stats.accuracy}%`, icon: TrendingUp, change: "+2.4%", trend: "up", color: "bg-gradient-to-br from-rose-400 to-rose-600" },
          ].map((stat, index) => (
            <div key={index} className="bg-white/70 dark:bg-zinc-900/70 backdrop-blur-sm rounded-2xl border border-rose-100 dark:border-zinc-800 p-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-zinc-400">{stat.label}</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">{stat.value}</p>
                  <div className="flex items-center gap-1 mt-2">
                    {stat.trend === "up" ? (
                      <ArrowUpRight className="w-4 h-4 text-emerald-500" />
                    ) : (
                      <ArrowDownRight className="w-4 h-4 text-rose-500" />
                    )}
                    <span className={`text-sm ${stat.trend === "up" ? "text-emerald-600" : "text-rose-600"}`}>
                      {stat.change}
                    </span>
                    <span className="text-xs text-gray-500 dark:text-zinc-500 ml-2">from last month</span>
                  </div>
                </div>
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${stat.color}`}>
                  <stat.icon className="w-6 h-6 text-white" />
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Quick Actions & Recent Activity */}
          <div className="lg:col-span-2">
            {/* Quick Actions */}
            <div className="mb-8">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Quick Actions</h3>
                <Link to="/models" className="text-sm text-emerald-600 dark:text-emerald-400 hover:text-emerald-700 flex items-center gap-1">
                  View all <ChevronRight className="w-4 h-4" />
                </Link>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {quickActions.map((action, index) => (
                  <Link
                    key={index}
                    to={action.link}
                    className="bg-white/70 dark:bg-zinc-900/70 backdrop-blur-sm rounded-2xl border border-rose-100 dark:border-zinc-800 p-5 hover:border-emerald-300 dark:hover:border-emerald-600 transition-all duration-300 group hover:shadow-lg"
                  >
                    <div className={`w-12 h-12 rounded-xl ${action.color} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                      <action.icon className="w-6 h-6 text-white" />
                    </div>
                    <h4 className="font-semibold text-gray-900 dark:text-white group-hover:text-emerald-600 dark:group-hover:text-emerald-400">
                      {action.title}
                    </h4>
                    <p className="text-sm text-gray-600 dark:text-zinc-400 mt-1">{action.description}</p>
                  </Link>
                ))}
              </div>
            </div>

            {/* Performance Chart */}
            <div className="bg-white/70 dark:bg-zinc-900/70 backdrop-blur-sm rounded-2xl border border-rose-100 dark:border-zinc-800 p-5 mb-8">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Model Performance</h3>
                <div className="flex items-center gap-2">
                  <button className={`px-3 py-1.5 rounded-lg text-sm ${activeTab === "overview" ? "bg-emerald-500 text-white" : "text-gray-600 dark:text-zinc-400"}`} onClick={() => setActiveTab("overview")}>
                    Overview
                  </button>
                  <button className={`px-3 py-1.5 rounded-lg text-sm ${activeTab === "details" ? "bg-emerald-500 text-white" : "text-gray-600 dark:text-zinc-400"}`} onClick={() => setActiveTab("details")}>
                    Details
                  </button>
                </div>
              </div>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <RechartsLineChart data={performanceData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" className="dark:stroke-zinc-700" />
                    <XAxis dataKey="name" stroke="#6b7280" className="dark:stroke-zinc-400" />
                    <YAxis stroke="#6b7280" className="dark:stroke-zinc-400" />
                    <Tooltip content={<CustomTooltip />} />
                    <Line type="monotone" dataKey="accuracy" stroke="#10b981" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} name="Accuracy %" />
                    <Line type="monotone" dataKey="speed" stroke="#8b5cf6" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} name="Speed (s)" />
                  </RechartsLineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Recent Activity */}
            <div className="bg-white/70 dark:bg-zinc-900/70 backdrop-blur-sm rounded-2xl border border-rose-100 dark:border-zinc-800 p-5">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Recent Activity</h3>
                <button className="text-sm text-emerald-600 dark:text-emerald-400 hover:text-emerald-700">
                  View all
                </button>
              </div>
              <div className="space-y-4">
                {recentActivity.map((activity) => (
                  <div key={activity.id} className="flex items-center gap-4 p-3 rounded-lg border border-rose-50 dark:border-zinc-800 hover:bg-rose-50/50 dark:hover:bg-zinc-800/50 transition-colors">
                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                      activity.status === "success" ? "bg-emerald-50 dark:bg-emerald-900/20" :
                      activity.status === "deployed" ? "bg-blue-50 dark:bg-blue-900/20" :
                      "bg-amber-50 dark:bg-amber-900/20"
                    }`}>
                      {activity.status === "success" ? (
                        <CheckCircle className="w-5 h-5 text-emerald-500" />
                      ) : activity.status === "deployed" ? (
                        <Server className="w-5 h-5 text-blue-500" />
                      ) : (
                        <Clock className="w-5 h-5 text-amber-500" />
                      )}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <h4 className="font-medium text-gray-900 dark:text-white">{activity.action}</h4>
                        <span className="text-xs text-gray-500 dark:text-zinc-500">{activity.time}</span>
                      </div>
                      <p className="text-sm text-gray-600 dark:text-zinc-400 mt-1">
                        {activity.model} • {activity.user}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right Column - Model Distribution & Top Models */}
          <div className="space-y-8">
            {/* Model Distribution */}
            <div className="bg-white/70 dark:bg-zinc-900/70 backdrop-blur-sm rounded-2xl border border-rose-100 dark:border-zinc-800 p-5">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">Model Distribution</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <RechartsPieChart>
                    <Pie
                      data={modelDistribution}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={(entry) => `${entry.name}: ${entry.value}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {modelDistribution.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </RechartsPieChart>
                </ResponsiveContainer>
              </div>
              <div className="flex flex-wrap gap-3 mt-4">
                {modelDistribution.map((item, index) => (
                  <div key={index} className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }}></div>
                    <span className="text-sm text-gray-600 dark:text-zinc-400">{item.name}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Top Performing Models */}
            <div className="bg-white/70 dark:bg-zinc-900/70 backdrop-blur-sm rounded-2xl border border-rose-100 dark:border-zinc-800 p-5">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Top Performing Models</h3>
                <Sparkles className="w-5 h-5 text-amber-500" />
              </div>
              <div className="space-y-4">
                {topModels.map((model) => {
                  const Icon = model.icon;
                  return (
                    <div key={model.id} className="flex items-center gap-4 p-3 rounded-lg border border-rose-50 dark:border-zinc-800 hover:bg-rose-50/50 dark:hover:bg-zinc-800/50 transition-colors">
                      <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${model.bg}`}>
                        <Icon className={`w-6 h-6 ${model.color}`} />
                      </div>
                      <div className="flex-1">
                        <h4 className="font-medium text-gray-900 dark:text-white">{model.name}</h4>
                        <div className="flex items-center gap-4 mt-1">
                          <span className="text-sm text-gray-600 dark:text-zinc-400">{model.type}</span>
                          <span className="text-sm font-medium text-emerald-600 dark:text-emerald-400">
                            {model.accuracy}% accuracy
                          </span>
                        </div>
                      </div>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        model.speed === "Very Fast" ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30" :
                        model.speed === "Fast" ? "bg-blue-50 text-blue-700 dark:bg-blue-900/30" :
                        model.speed === "Medium" ? "bg-amber-50 text-amber-700 dark:bg-amber-900/30" :
                        "bg-rose-50 text-rose-700 dark:bg-rose-900/30"
                      }`}>
                        {model.speed}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Platform Features */}
            <div className="bg-white/70 dark:bg-zinc-900/70 backdrop-blur-sm rounded-2xl border border-rose-100 dark:border-zinc-800 p-5">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">Platform Features</h3>
              <div className="space-y-4">
                {features.map((feature, index) => (
                  <div key={index} className="flex items-center gap-4 p-3 rounded-lg border border-rose-50 dark:border-zinc-800">
                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${feature.bg}`}>
                      <feature.icon className={`w-5 h-5 ${feature.color}`} />
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white">{feature.title}</h4>
                      <p className="text-sm text-gray-600 dark:text-zinc-400 mt-1">{feature.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* CTA Section */}
        <div className="mt-8 bg-gradient-to-r from-emerald-400 to-emerald-600 rounded-2xl p-8 text-center">
          <div className="max-w-2xl mx-auto">
            <h3 className="text-2xl font-bold text-white mb-3">Ready to Transform Your Data?</h3>
            <p className="text-emerald-100 mb-6">
              Join thousands of data scientists building intelligent models with Arbor AI
            </p>
            <div className="flex items-center justify-center gap-4">
              <Link
                to="/models"
                className="px-6 py-3 bg-white text-emerald-600 font-medium rounded-xl hover:bg-emerald-50 transition-colors flex items-center gap-2"
              >
                <PlayCircle className="w-4 h-4" />
                Start Training
              </Link>
              <Link
                to="/demo"
                className="px-6 py-3 bg-transparent border-2 border-white text-white font-medium rounded-xl hover:bg-white/10 transition-colors"
              >
                View Demo
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Home;