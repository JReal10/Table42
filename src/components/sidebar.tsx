"use client";

import { useState } from 'react';
import Link from 'next/link';

export default function Sidebar() {
  const [isMinimized, setIsMinimized] = useState(false);

  return (
    <aside
      className={`h-screen bg-gray-800 text-white p-4 transition-all duration-300 ${
        isMinimized ? 'w-16' : 'w-64'
      }`}
    >
      <header className="flex items-center justify-between mb-6">
        {!isMinimized && <h1 className="text-xl font-bold">LOGO</h1>}
        <button
          onClick={() => setIsMinimized((prev) => !prev)}
          className="text-white hover:text-gray-400 text-sm"
        >
          {isMinimized ? 'Expand' : 'Minimize'}
        </button>
      </header>
      <nav>
        <ul className="space-y-4">
          <li>
            <Link href="/dashboard" className="hover:underline flex items-center">
              {isMinimized ? 'D' : 'Dashboard'}
            </Link>
          </li>
          <li>
            <Link href="/conversation-history" className="hover:underline flex items-center">
              {isMinimized ? 'CH' : 'Conversation History'}
            </Link>
          </li>
          <li>
            <Link href="/personalized-agent" className="hover:underline flex items-center">
              {isMinimized ? 'PA' : 'Personalized Agent'}
            </Link>
          </li>
          <li>
            <Link href="/data-input" className="hover:underline flex items-center">
              {isMinimized ? 'DI' : 'Data Input'}
            </Link>
          </li>
          <li>
            <Link href="/settings" className="hover:underline flex items-center">
              {isMinimized ? 'S' : 'Settings'}
            </Link>
          </li>
        </ul>
      </nav>
    </aside>
  );
}
