import { useEffect, useRef, useState } from "react";
import { NavLink } from "react-router-dom";
import {
  HomeIcon,
  BotIcon,
  DatabaseIcon,
  RocketIcon,
  SettingsIcon,
  HelpCircleIcon,
  ChevronRightIcon,
  ChevronDownIcon,
  PlusIcon,
  LibraryIcon,
  UploadIcon,
  FolderOpenIcon,
  BookTemplateIcon,
  UserIcon,
  CreditCardIcon,
  FileTextIcon,
  Atom,
  KeyIcon,
} from "lucide-react";

const Sidebar = ({ isSidebarOpen, setIsSidebarOpen }) => {
  const [expandedSections, setExpandedSections] = useState({
    models: true,
    data: true,
    projects: true,
    settings: false,
    help: false,
  });

  const sidebarRef = useRef(null);

  // Main navigation items
  const mainMenuItems = [{ name: "Dashboard", href: "/", icon: HomeIcon }];

  // Models section items
  // In your Sidebar component, update the modelsItems to include the main models page:
  const modelsItems = [
    { name: "All Models", href: "/models/all", icon: BotIcon },
    { name: "Create New Flow", href: "/models/create-flow", icon: PlusIcon },
    { name: "Model Library", href: "/models/library", icon: LibraryIcon },
  ];

  // Data section items
  const dataItems = [
    { name: "Upload Data", href: "/data/upload", icon: UploadIcon },
    { name: "Dataset Analyzer", href: "/analyze", icon: DatabaseIcon },
    { name: "Data Sources", href: "/data/sources", icon: FolderOpenIcon },
  ];

  // Projects section items
  const projectsItems = [
    { name: "All Projects", href: "/projects", icon: FolderOpenIcon },
    { name: "Create Project", href: "/projects/create", icon: PlusIcon },
    { name: "Templates", href: "/projects/templates", icon: BookTemplateIcon },
  ];

  // Settings section items
  const settingsItems = [
    { name: "Profile", href: "/settings/profile", icon: UserIcon },
    { name: "Preferences", href: "/settings/preferences", icon: SettingsIcon },
    { name: "Billing", href: "/settings/billing", icon: CreditCardIcon },
    { name: "API Keys", href: "/settings/api-keys", icon: KeyIcon },
  ];

  // Help section items
  const helpItems = [
    { name: "Documentation", href: "/help/docs", icon: FileTextIcon },
    { name: "Support", href: "/help/support", icon: HelpCircleIcon },
  ];

  const toggleSection = (section) => {
    setExpandedSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  useEffect(() => {
    function handleClickOutside(event) {
      if (sidebarRef.current && !sidebarRef.current.contains(event.target)) {
        setIsSidebarOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [setIsSidebarOpen]);

  // Reusable section component
  const SidebarSection = ({ title, icon: Icon, items, sectionKey }) => (
    <div className="mt-4 px-3">
      <button
        onClick={() => toggleSection(sectionKey)}
        className="flex items-center justify-between w-full px-3 py-2 rounded-lg cursor-pointer hover:bg-gray-100 dark:hover:bg-zinc-800 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Icon className="w-4 h-4 text-gray-500 dark:text-zinc-400" />
          <h3 className="text-sm font-medium text-gray-700 dark:text-zinc-300">
            {title}
          </h3>
        </div>
        {expandedSections[sectionKey] ? (
          <ChevronDownIcon className="w-4 h-4 text-gray-500 dark:text-zinc-400" />
        ) : (
          <ChevronRightIcon className="w-4 h-4 text-gray-500 dark:text-zinc-400" />
        )}
      </button>

      {expandedSections[sectionKey] && (
        <div className="mt-2 space-y-1 pl-2">
          {items.map((item) => (
            <NavLink
              key={item.name}
              to={item.href}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg transition-colors duration-200 text-sm ${
                  isActive
                    ? "bg-blue-100 text-blue-600 hover:bg-blue-200 dark:bg-blue-500/10 dark:text-blue-400 dark:hover:bg-blue-500/20"
                    : "text-gray-600 dark:text-zinc-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-zinc-800"
                }`
              }
            >
              <item.icon className="w-4 h-4" />
              <span>{item.name}</span>
            </NavLink>
          ))}
        </div>
      )}
    </div>
  );

  return (
    <div
      ref={sidebarRef}
      className={`z-10 bg-white dark:bg-zinc-900 min-w-68 flex flex-col h-screen border-r border-gray-200 dark:border-zinc-800 max-sm:absolute transition-all ${
        isSidebarOpen ? "left-0" : "-left-full"
      }`}
    >
      {/* Workspace/Site Header */}
      <div className="p-4 border-b border-gray-200 dark:border-zinc-800">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
            <Atom className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="font-semibold text-gray-900 dark:text-white">
              Lotus AI
            </h2>
            <p className="text-xs text-gray-500 dark:text-zinc-400">
              Workspace
            </p>
          </div>
        </div>
      </div>

      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto no-scrollbar py-4">
        {/* Main Navigation */}
        <div className="px-3">
          {mainMenuItems.map((item) => (
            <NavLink
              key={item.name}
              to={item.href}
              className={({ isActive }) =>
                `flex items-center gap-3 py-2 px-4 rounded-lg transition-colors text-sm ${
                  isActive
                    ? "bg-gray-100 dark:bg-zinc-800 text-gray-900 dark:text-white"
                    : "text-gray-700 dark:text-zinc-300 hover:bg-gray-50 dark:hover:bg-zinc-800/60"
                }`
              }
            >
              <item.icon size={16} />
              <span>{item.name}</span>
            </NavLink>
          ))}
        </div>

        {/* Models Section */}
        <SidebarSection
          title="Models"
          icon={BotIcon}
          items={modelsItems}
          sectionKey="models"
        />

        {/* Data Section */}
        <SidebarSection
          title="Data"
          icon={DatabaseIcon}
          items={dataItems}
          sectionKey="data"
        />

        {/* Projects Section */}
        <SidebarSection
          title="Projects"
          icon={RocketIcon}
          items={projectsItems}
          sectionKey="projects"
        />

        {/* Settings Section */}
        <SidebarSection
          title="Settings"
          icon={SettingsIcon}
          items={settingsItems}
          sectionKey="settings"
        />

        {/* Help & Docs Section */}
        <SidebarSection
          title="Help & Docs"
          icon={HelpCircleIcon}
          items={helpItems}
          sectionKey="help"
        />
      </div>

      {/* User Profile Footer */}
      <div className="p-4 border-t border-gray-200 dark:border-zinc-800">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-gradient-to-br from-gray-400 to-gray-600 rounded-full flex items-center justify-center">
            <UserIcon className="w-4 h-4 text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
              John Doe
            </p>
            <p className="text-xs text-gray-500 dark:text-zinc-400 truncate">
              john@example.com
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;