/**
 * Header Component - Main application header with navigation and user menu
 */
import React, { Fragment, useState } from 'react';
import { Menu, Transition } from '@headlessui/react';
import {
  Bars3Icon,
  BellIcon,
  ChevronDownIcon,
  UserCircleIcon,
  Cog6ToothIcon,
  ArrowRightOnRectangleIcon,
} from '@heroicons/react/24/outline';
import { useAuth } from '../../contexts/AuthContext';
import { SectorSelector } from '../sector/SectorSelector';
import { TierBadge } from '../sector/TierBadge';
import { useNotifications } from '../../contexts/NotificationContext';
import { cn, getInitials } from '../../lib/utils';
import Button from '../ui/Button';
import Badge from '../ui/Badge';
import NotificationCenter from '../notifications/NotificationCenter';

interface HeaderProps {
  onMenuClick: () => void;
  isMobileMenuOpen: boolean;
}

const Header: React.FC<HeaderProps> = ({ onMenuClick, isMobileMenuOpen }) => {
  const { user, logout } = useAuth();
  const { summary, isConnected } = useNotifications();
  const [showNotificationCenter, setShowNotificationCenter] = useState(false);

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  return (
    <header className="bg-white border-b-2 border-neutral-300 shadow-md relative z-40 w-full min-h-[64px]">
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Left side - Mobile menu button only */}
          <div className="flex items-center">
            {/* Mobile menu button */}
            <Button
              variant="ghost"
              size="sm"
              className="lg:hidden mr-2"
              onClick={onMenuClick}
              aria-label="Open sidebar"
            >
              <Bars3Icon className="h-6 w-6" />
            </Button>

            {/* Logo - Only show on mobile when sidebar is closed */}
            <div className="flex items-center lg:hidden">
              <div className="flex-shrink-0">
                <div className="h-8 w-8 bg-primary-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">C</span>
                </div>
              </div>
              <div className="ml-3">
                <h1 className="text-lg font-semibold text-neutral-900">
                  Common
                </h1>
              </div>
            </div>
          </div>

          {/* Center - Sector selector and tier badge */}
          <div className="hidden md:flex items-center space-x-4">
            <SectorSelector />
            <TierBadge />
          </div>

          {/* Right side - Search, notifications, and user menu */}
          <div className="flex items-center space-x-4">
            {/* Search bar - hidden on mobile */}
            <div className="hidden md:block">
              <div className="relative">
                <input
                  type="text"
                  placeholder="Search..."
                  className="w-64 pl-10 pr-4 py-2 text-sm border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <svg
                    className="h-4 w-4 text-neutral-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                    />
                  </svg>
                </div>
              </div>
            </div>

            {/* Notifications */}
            <div className="relative">
              <Button
                variant="ghost"
                size="sm"
                className="relative"
                onClick={() => setShowNotificationCenter(true)}
                aria-label="View notifications"
              >
                <BellIcon className="h-6 w-6" />
                {/* Notification badge */}
                {summary && summary.unread_count > 0 && (
                  <Badge
                    variant="error"
                    size="sm"
                    className="absolute -top-1 -right-1 min-w-[1rem] h-4 text-xs"
                  >
                    {summary.unread_count > 99 ? '99+' : summary.unread_count}
                  </Badge>
                )}
                {/* Connection indicator */}
                <div className={cn(
                  'absolute -bottom-1 -right-1 w-2 h-2 rounded-full border border-white',
                  isConnected ? 'bg-success-500' : 'bg-error-500'
                )} />
              </Button>
            </div>

            {/* User menu */}
            <Menu as="div" className="relative">
              <Menu.Button className="flex items-center space-x-3 text-sm rounded-lg p-2 hover:bg-neutral-100 focus:outline-none focus:ring-2 focus:ring-primary-500">
                {/* User avatar */}
                <div className="h-8 w-8 bg-primary-100 rounded-full flex items-center justify-center">
                  <span className="text-primary-700 font-medium text-sm">
                    {user ? getInitials(user.full_name) : 'U'}
                  </span>
                </div>
                
                {/* User info - hidden on mobile */}
                <div className="hidden md:block text-left">
                  <p className="text-neutral-900 font-medium">
                    {user?.full_name || 'User'}
                  </p>
                  <p className="text-neutral-500 text-xs">
                    {user?.company?.name || 'Company'}
                  </p>
                </div>
                
                <ChevronDownIcon className="h-4 w-4 text-neutral-400" />
              </Menu.Button>

              <Transition
                as={Fragment}
                enter="transition ease-out duration-100"
                enterFrom="transform opacity-0 scale-95"
                enterTo="transform opacity-100 scale-100"
                leave="transition ease-in duration-75"
                leaveFrom="transform opacity-100 scale-100"
                leaveTo="transform opacity-0 scale-95"
              >
                <Menu.Items className="absolute right-0 mt-2 w-56 origin-top-right bg-white rounded-lg shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
                  <div className="p-1">
                    {/* User info in mobile */}
                    <div className="md:hidden px-3 py-2 border-b border-neutral-100">
                      <p className="text-neutral-900 font-medium">
                        {user?.full_name || 'User'}
                      </p>
                      <p className="text-neutral-500 text-sm">
                        {user?.email}
                      </p>
                      <p className="text-neutral-500 text-xs">
                        {user?.company?.name || 'Company'}
                      </p>
                    </div>

                    <Menu.Item>
                      {({ active }) => (
                        <a
                          href="/profile"
                          className={cn(
                            'flex items-center px-3 py-2 text-sm rounded-md',
                            active ? 'bg-neutral-100 text-neutral-900' : 'text-neutral-700'
                          )}
                        >
                          <UserCircleIcon className="h-4 w-4 mr-3" />
                          Your Profile
                        </a>
                      )}
                    </Menu.Item>

                    <Menu.Item>
                      {({ active }) => (
                        <a
                          href="/settings"
                          className={cn(
                            'flex items-center px-3 py-2 text-sm rounded-md',
                            active ? 'bg-neutral-100 text-neutral-900' : 'text-neutral-700'
                          )}
                        >
                          <svg
                            className="h-4 w-4 mr-3"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                            />
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                            />
                          </svg>
                          Settings
                        </a>
                      )}
                    </Menu.Item>

                    <div className="border-t border-neutral-100 my-1" />

                    <Menu.Item>
                      {({ active }) => (
                        <button
                          onClick={handleLogout}
                          className={cn(
                            'flex items-center w-full px-3 py-2 text-sm rounded-md text-left',
                            active ? 'bg-neutral-100 text-neutral-900' : 'text-neutral-700'
                          )}
                        >
                          <svg
                            className="h-4 w-4 mr-3"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
                            />
                          </svg>
                          Sign out
                        </button>
                      )}
                    </Menu.Item>
                  </div>
                </Menu.Items>
              </Transition>
            </Menu>
          </div>
        </div>
      </div>

      {/* Notification Center */}
      <NotificationCenter
        isOpen={showNotificationCenter}
        onClose={() => setShowNotificationCenter(false)}
      />
    </header>
  );
};

export default Header;
