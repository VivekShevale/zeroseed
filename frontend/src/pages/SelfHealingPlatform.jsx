import React, { useState, useEffect } from 'react';
import { Activity, AlertTriangle, CheckCircle, XCircle, Zap, TrendingUp, Shield, Database, Cpu, HardDrive, Network, Clock } from 'lucide-react';

const SelfHealingPlatform = () => {
  const [services, setServices] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [actions, setActions] = useState([]);
  const [metrics, setMetrics] = useState({});
  const [activeTab, setActiveTab] = useState('dashboard');
  const [autoHealEnabled, setAutoHealEnabled] = useState(true);
  const [learningData, setLearningData] = useState({
    totalIncidents: 0,
    autoResolved: 0,
    avgResolutionTime: 0,
    successRate: 95
  });

  // Initialize services
  useEffect(() => {
    const initialServices = [
      {
        id: 'web-app',
        name: 'Web Application',
        status: 'healthy',
        cpu: 45,
        memory: 60,
        latency: 120,
        errorRate: 0.1,
        uptime: 99.9
      },
      {
        id: 'api-gateway',
        name: 'API Gateway',
        status: 'healthy',
        cpu: 30,
        memory: 40,
        latency: 80,
        errorRate: 0.05,
        uptime: 99.95
      },
      {
        id: 'database',
        name: 'Database',
        status: 'healthy',
        cpu: 65,
        memory: 75,
        latency: 50,
        errorRate: 0,
        uptime: 99.99
      },
      {
        id: 'cache',
        name: 'Cache Layer',
        status: 'healthy',
        cpu: 20,
        memory: 35,
        latency: 10,
        errorRate: 0,
        uptime: 99.98
      }
    ];
    setServices(initialServices);
    updateMetrics(initialServices);
  }, []);

  // Autonomous monitoring and healing
  useEffect(() => {
    const interval = setInterval(() => {
      setServices(prevServices => {
        const updatedServices = prevServices.map(service => {
          // Simulate metric fluctuations
          const newCpu = Math.max(10, Math.min(100, service.cpu + (Math.random() - 0.5) * 20));
          const newMemory = Math.max(10, Math.min(100, service.memory + (Math.random() - 0.5) * 15));
          const newLatency = Math.max(10, service.latency + (Math.random() - 0.5) * 30);
          const newErrorRate = Math.max(0, service.errorRate + (Math.random() - 0.5) * 0.2);

          // Anomaly detection
          let newStatus = 'healthy';
          let issue = null;

          if (newCpu > 80) {
            newStatus = 'warning';
            issue = { type: 'high_cpu', severity: 'warning', metric: newCpu };
          }
          if (newMemory > 85) {
            newStatus = 'critical';
            issue = { type: 'memory_leak', severity: 'critical', metric: newMemory };
          }
          if (newErrorRate > 1) {
            newStatus = 'critical';
            issue = { type: 'high_error_rate', severity: 'critical', metric: newErrorRate };
          }
          if (newLatency > 300) {
            newStatus = 'warning';
            issue = { type: 'high_latency', severity: 'warning', metric: newLatency };
          }

          // Autonomous healing
          if (issue && autoHealEnabled) {
            detectAndHeal(service, issue);
          }

          return {
            ...service,
            cpu: newCpu,
            memory: newMemory,
            latency: newLatency,
            errorRate: newErrorRate,
            status: newStatus
          };
        });

        updateMetrics(updatedServices);
        return updatedServices;
      });
    }, 3000);

    return () => clearInterval(interval);
  }, [autoHealEnabled]);

  const detectAndHeal = (service, issue) => {
    const timestamp = new Date().toLocaleTimeString();
    
    // Create incident
    const incident = {
      id: `INC-${Date.now()}`,
      serviceId: service.id,
      serviceName: service.name,
      type: issue.type,
      severity: issue.severity,
      detectedAt: timestamp,
      status: 'detected',
      metric: issue.metric
    };

    setIncidents(prev => [incident, ...prev.slice(0, 19)]);

    // Decide action based on issue type
    setTimeout(() => {
      const actionPlan = decideAction(issue, service);
      executeAction(incident, actionPlan, service);
    }, 1000);
  };

  const decideAction = (issue, service) => {
    const actions = {
      high_cpu: {
        action: 'scale_horizontal',
        description: 'Scale out instances',
        confidence: 92
      },
      memory_leak: {
        action: 'restart_service',
        description: 'Restart service to clear memory',
        confidence: 88
      },
      high_error_rate: {
        action: 'rollback_deployment',
        description: 'Rollback to previous stable version',
        confidence: 85
      },
      high_latency: {
        action: 'optimize_cache',
        description: 'Clear cache and optimize queries',
        confidence: 78
      }
    };

    return actions[issue.type] || {
      action: 'alert_team',
      description: 'Notify DevOps team',
      confidence: 60
    };
  };

  const executeAction = (incident, actionPlan, service) => {
    const action = {
      id: `ACT-${Date.now()}`,
      incidentId: incident.id,
      serviceName: service.name,
      action: actionPlan.action,
      description: actionPlan.description,
      confidence: actionPlan.confidence,
      timestamp: new Date().toLocaleTimeString(),
      status: 'executing'
    };

    setActions(prev => [action, ...prev.slice(0, 19)]);

    // Simulate action execution
    setTimeout(() => {
      const success = Math.random() > 0.1; // 90% success rate
      
      setActions(prev => prev.map(a => 
        a.id === action.id 
          ? { ...a, status: success ? 'completed' : 'failed' }
          : a
      ));

      setIncidents(prev => prev.map(inc =>
        inc.id === incident.id
          ? { ...inc, status: success ? 'resolved' : 'escalated' }
          : inc
      ));

      // Heal the service
      if (success) {
        setServices(prev => prev.map(s =>
          s.id === service.id
            ? {
                ...s,
                cpu: Math.min(s.cpu, 60),
                memory: Math.min(s.memory, 70),
                latency: Math.min(s.latency, 150),
                errorRate: Math.min(s.errorRate, 0.1),
                status: 'healthy'
              }
            : s
        ));

        // Update learning data
        setLearningData(prev => ({
          totalIncidents: prev.totalIncidents + 1,
          autoResolved: prev.autoResolved + 1,
          avgResolutionTime: Math.round((prev.avgResolutionTime * prev.totalIncidents + 2.5) / (prev.totalIncidents + 1) * 10) / 10,
          successRate: Math.round(((prev.autoResolved + 1) / (prev.totalIncidents + 1)) * 100)
        }));
      }
    }, 2000);
  };

  const updateMetrics = (servicesList) => {
    const avgCpu = servicesList.reduce((sum, s) => sum + s.cpu, 0) / servicesList.length;
    const avgMemory = servicesList.reduce((sum, s) => sum + s.memory, 0) / servicesList.length;
    const avgLatency = servicesList.reduce((sum, s) => sum + s.latency, 0) / servicesList.length;
    const totalErrors = servicesList.reduce((sum, s) => sum + s.errorRate, 0);

    setMetrics({
      avgCpu: Math.round(avgCpu),
      avgMemory: Math.round(avgMemory),
      avgLatency: Math.round(avgLatency),
      totalErrors: Math.round(totalErrors * 100) / 100,
      healthyServices: servicesList.filter(s => s.status === 'healthy').length,
      totalServices: servicesList.length
    });
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return 'text-green-500';
      case 'warning': return 'text-yellow-500';
      case 'critical': return 'text-red-500';
      default: return 'text-gray-500';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy': return <CheckCircle className="w-5 h-5" />;
      case 'warning': return <AlertTriangle className="w-5 h-5" />;
      case 'critical': return <XCircle className="w-5 h-5" />;
      default: return <Activity className="w-5 h-5" />;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white p-6">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-8">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-3">
            <div className="bg-gradient-to-r from-blue-500 to-purple-500 p-3 rounded-xl">
              <Zap className="w-8 h-8" />
            </div>
            <div>
              <h1 className="text-3xl font-bold">HealOps AI</h1>
              <p className="text-slate-400">Autonomous Infrastructure Management</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <div className="text-sm text-slate-400">Auto-Healing</div>
              <div className={`text-lg font-semibold ${autoHealEnabled ? 'text-green-400' : 'text-red-400'}`}>
                {autoHealEnabled ? 'ENABLED' : 'DISABLED'}
              </div>
            </div>
            <button
              onClick={() => setAutoHealEnabled(!autoHealEnabled)}
              className={`px-6 py-3 rounded-lg font-semibold transition-all ${
                autoHealEnabled 
                  ? 'bg-green-500 hover:bg-green-600' 
                  : 'bg-red-500 hover:bg-red-600'
              }`}
            >
              {autoHealEnabled ? 'Disable' : 'Enable'}
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto">
        {/* Navigation */}
        <div className="flex gap-4 mb-6 border-b border-slate-700">
          {['dashboard', 'services', 'incidents', 'actions', 'learning'].map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-6 py-3 font-semibold capitalize transition-all ${
                activeTab === tab
                  ? 'text-blue-400 border-b-2 border-blue-400'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* Dashboard Tab */}
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            {/* Key Metrics */}
            <div className="grid grid-cols-4 gap-4">
              <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
                <div className="flex items-center justify-between mb-2">
                  <Cpu className="w-8 h-8 text-blue-400" />
                  <span className="text-2xl font-bold">{metrics.avgCpu}%</span>
                </div>
                <div className="text-slate-400">Avg CPU Usage</div>
              </div>
              <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
                <div className="flex items-center justify-between mb-2">
                  <HardDrive className="w-8 h-8 text-purple-400" />
                  <span className="text-2xl font-bold">{metrics.avgMemory}%</span>
                </div>
                <div className="text-slate-400">Avg Memory</div>
              </div>
              <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
                <div className="flex items-center justify-between mb-2">
                  <Network className="w-8 h-8 text-green-400" />
                  <span className="text-2xl font-bold">{metrics.avgLatency}ms</span>
                </div>
                <div className="text-slate-400">Avg Latency</div>
              </div>
              <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
                <div className="flex items-center justify-between mb-2">
                  <Shield className="w-8 h-8 text-yellow-400" />
                  <span className="text-2xl font-bold">{metrics.healthyServices}/{metrics.totalServices}</span>
                </div>
                <div className="text-slate-400">Healthy Services</div>
              </div>
            </div>

            {/* Services Overview */}
            <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
              <h2 className="text-xl font-bold mb-4">Services Status</h2>
              <div className="space-y-3">
                {services.map(service => (
                  <div key={service.id} className="bg-slate-700 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div className={getStatusColor(service.status)}>
                          {getStatusIcon(service.status)}
                        </div>
                        <div>
                          <div className="font-semibold">{service.name}</div>
                          <div className="text-sm text-slate-400">{service.id}</div>
                        </div>
                      </div>
                      <div className={`px-3 py-1 rounded-full text-sm font-semibold ${
                        service.status === 'healthy' ? 'bg-green-500/20 text-green-400' :
                        service.status === 'warning' ? 'bg-yellow-500/20 text-yellow-400' :
                        'bg-red-500/20 text-red-400'
                      }`}>
                        {service.status.toUpperCase()}
                      </div>
                    </div>
                    <div className="grid grid-cols-4 gap-4 text-sm">
                      <div>
                        <div className="text-slate-400">CPU</div>
                        <div className="font-semibold">{Math.round(service.cpu)}%</div>
                      </div>
                      <div>
                        <div className="text-slate-400">Memory</div>
                        <div className="font-semibold">{Math.round(service.memory)}%</div>
                      </div>
                      <div>
                        <div className="text-slate-400">Latency</div>
                        <div className="font-semibold">{Math.round(service.latency)}ms</div>
                      </div>
                      <div>
                        <div className="text-slate-400">Uptime</div>
                        <div className="font-semibold">{service.uptime}%</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Incidents Tab */}
        {activeTab === 'incidents' && (
          <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
            <h2 className="text-xl font-bold mb-4">Recent Incidents</h2>
            <div className="space-y-2">
              {incidents.length === 0 ? (
                <div className="text-center py-12 text-slate-400">
                  <CheckCircle className="w-12 h-12 mx-auto mb-2 text-green-500" />
                  <p>No incidents detected. All systems healthy!</p>
                </div>
              ) : (
                incidents.map(incident => (
                  <div key={incident.id} className="bg-slate-700 rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-semibold">{incident.id}</span>
                          <span className={`px-2 py-1 rounded text-xs font-semibold ${
                            incident.severity === 'critical' ? 'bg-red-500/20 text-red-400' :
                            'bg-yellow-500/20 text-yellow-400'
                          }`}>
                            {incident.severity}
                          </span>
                        </div>
                        <div className="text-sm text-slate-400">{incident.serviceName}</div>
                        <div className="text-sm mt-1">{incident.type.replace(/_/g, ' ').toUpperCase()}</div>
                      </div>
                      <div className="text-right">
                        <div className={`px-3 py-1 rounded-full text-sm font-semibold ${
                          incident.status === 'resolved' ? 'bg-green-500/20 text-green-400' :
                          incident.status === 'escalated' ? 'bg-red-500/20 text-red-400' :
                          'bg-blue-500/20 text-blue-400'
                        }`}>
                          {incident.status}
                        </div>
                        <div className="text-xs text-slate-400 mt-1">{incident.detectedAt}</div>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* Actions Tab */}
        {activeTab === 'actions' && (
          <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
            <h2 className="text-xl font-bold mb-4">Autonomous Actions</h2>
            <div className="space-y-2">
              {actions.length === 0 ? (
                <div className="text-center py-12 text-slate-400">
                  <Activity className="w-12 h-12 mx-auto mb-2" />
                  <p>No actions taken yet</p>
                </div>
              ) : (
                actions.map(action => (
                  <div key={action.id} className="bg-slate-700 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex-1">
                        <div className="font-semibold">{action.description}</div>
                        <div className="text-sm text-slate-400">{action.serviceName}</div>
                      </div>
                      <div className="text-right">
                        <div className={`px-3 py-1 rounded-full text-sm font-semibold ${
                          action.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                          action.status === 'failed' ? 'bg-red-500/20 text-red-400' :
                          'bg-blue-500/20 text-blue-400'
                        }`}>
                          {action.status}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <div className="text-slate-400">Confidence: {action.confidence}%</div>
                      <div className="text-slate-400">{action.timestamp}</div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* Learning Tab */}
        {activeTab === 'learning' && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-6">
              <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
                <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                  <TrendingUp className="w-6 h-6 text-blue-400" />
                  Learning Metrics
                </h2>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between mb-2">
                      <span className="text-slate-400">Total Incidents</span>
                      <span className="font-bold text-2xl">{learningData.totalIncidents}</span>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between mb-2">
                      <span className="text-slate-400">Auto-Resolved</span>
                      <span className="font-bold text-2xl text-green-400">{learningData.autoResolved}</span>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between mb-2">
                      <span className="text-slate-400">Success Rate</span>
                      <span className="font-bold text-2xl text-blue-400">{learningData.successRate}%</span>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between mb-2">
                      <span className="text-slate-400">Avg Resolution Time</span>
                      <span className="font-bold text-2xl">{learningData.avgResolutionTime}s</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
                <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                  <Database className="w-6 h-6 text-purple-400" />
                  Knowledge Base
                </h2>
                <div className="space-y-3">
                  <div className="bg-slate-700 rounded-lg p-3">
                    <div className="font-semibold mb-1">High CPU → Scale Horizontal</div>
                    <div className="text-sm text-slate-400">Confidence: 92% | Used 12 times</div>
                  </div>
                  <div className="bg-slate-700 rounded-lg p-3">
                    <div className="font-semibold mb-1">Memory Leak → Restart Service</div>
                    <div className="text-sm text-slate-400">Confidence: 88% | Used 8 times</div>
                  </div>
                  <div className="bg-slate-700 rounded-lg p-3">
                    <div className="font-semibold mb-1">High Errors → Rollback</div>
                    <div className="text-sm text-slate-400">Confidence: 85% | Used 5 times</div>
                  </div>
                  <div className="bg-slate-700 rounded-lg p-3">
                    <div className="font-semibold mb-1">High Latency → Optimize Cache</div>
                    <div className="text-sm text-slate-400">Confidence: 78% | Used 3 times</div>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/20 rounded-xl p-6">
              <h3 className="text-lg font-bold mb-2">🧠 AI Learning Engine</h3>
              <p className="text-slate-300">
                The system continuously learns from every incident and action. Success patterns are reinforced, 
                and failures are avoided. Over time, the platform becomes more accurate in diagnosis and more 
                confident in autonomous decision-making, reducing mean time to recovery (MTTR) and improving 
                overall system reliability.
              </p>
            </div>
          </div>
        )}

        {/* Services Tab */}
        {activeTab === 'services' && (
          <div className="grid grid-cols-2 gap-6">
            {services.map(service => (
              <div key={service.id} className="bg-slate-800 rounded-xl p-6 border border-slate-700">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-xl font-bold">{service.name}</h3>
                  <div className={getStatusColor(service.status)}>
                    {getStatusIcon(service.status)}
                  </div>
                </div>
                <div className="space-y-3">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-slate-400">CPU Usage</span>
                      <span className="font-semibold">{Math.round(service.cpu)}%</span>
                    </div>
                    <div className="w-full bg-slate-700 rounded-full h-2">
                      <div 
                        className="bg-blue-500 h-2 rounded-full transition-all"
                        style={{ width: `${service.cpu}%` }}
                      />
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-slate-400">Memory</span>
                      <span className="font-semibold">{Math.round(service.memory)}%</span>
                    </div>
                    <div className="w-full bg-slate-700 rounded-full h-2">
                      <div 
                        className="bg-purple-500 h-2 rounded-full transition-all"
                        style={{ width: `${service.memory}%` }}
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4 pt-2">
                    <div>
                      <div className="text-slate-400 text-sm">Latency</div>
                      <div className="font-semibold">{Math.round(service.latency)}ms</div>
                    </div>
                    <div>
                      <div className="text-slate-400 text-sm">Error Rate</div>
                      <div className="font-semibold">{service.errorRate.toFixed(2)}%</div>
                    </div>
                    <div>
                      <div className="text-slate-400 text-sm">Uptime</div>
                      <div className="font-semibold text-green-400">{service.uptime}%</div>
                    </div>
                    <div>
                      <div className="text-slate-400 text-sm">Status</div>
                      <div className={`font-semibold ${getStatusColor(service.status)}`}>
                        {service.status.toUpperCase()}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default SelfHealingPlatform;