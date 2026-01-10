import { useState, useEffect } from 'react'
import Sidebar from '../components/Sidebar'
import { Outlet } from 'react-router-dom'
import { useDispatch, useSelector } from 'react-redux'
import { loadTheme } from '../features/themeSlice'
import { Loader2Icon } from 'lucide-react'

const Layout = () => {
    const [isSidebarOpen, setIsSidebarOpen] = useState(false)
    const dispatch = useDispatch()

    // Initial load of theme
    useEffect(() => {
        dispatch(loadTheme())
    }, [])

    // if (!user) {
    //     return (
    //         <div className='flex justify-center items-center h-screen bg-white dark:bg-zinc-950'>
    //             {/* <SignIn /> */}
    //         </div>
    //     )
    // }

    // if (!isLoaded) {
    //     return (
    //         <div className='flex items-center justify-center h-screen bg-white dark:bg-zinc-950'>
    //             <Loader2Icon className="size-7 text-blue-500 animate-spin" />
    //         </div>
    //     )
    // }

    return (
        <div className="flex bg-white dark:bg-zinc-950 text-gray-900 dark:text-slate-100">
            <Sidebar isSidebarOpen={isSidebarOpen} setIsSidebarOpen={setIsSidebarOpen} />
            <div className="flex-1 flex flex-col h-screen">
                {/* You'll need to create a Navbar component or adapt your existing one */}
                {/* <Navbar isSidebarOpen={isSidebarOpen} setIsSidebarOpen={setIsSidebarOpen} /> */}
                
                {/* Simple header for now */}
                <header className="border-b border-gray-200 dark:border-zinc-800 p-4">
                    <div className="flex items-center justify-between">
                        <button 
                            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-zinc-800"
                        >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                            </svg>
                        </button>
                        <h1 className="text-lg font-semibold">AI Platform</h1>
                        <div className="w-9"></div> {/* Spacer for balance */}
                    </div>
                </header>

                <div className="flex-1 h-full p-6 xl:p-10 xl:px-16 overflow-y-auto">
                    <Outlet />
                </div>
            </div>
        </div>
    )
}

export default Layout;