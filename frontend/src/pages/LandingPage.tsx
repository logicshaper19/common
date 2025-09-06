/**
 * Landing Page - Marketing site for Common Supply Chain Platform
 */
import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  PlayIcon,
  CheckIcon,
  ArrowRightIcon,
  DocumentTextIcon,
  ShieldCheckIcon,
  ChartBarIcon,
  GlobeAltIcon,
  UserGroupIcon,
  CogIcon,
} from '@heroicons/react/24/outline';
import Button from '../components/ui/Button';
import { Card, CardBody } from '../components/ui/Card';

const LandingPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'brands' | 'suppliers' | 'consultants'>('brands');

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="bg-white border-b border-neutral-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <div className="flex items-center">
              <span className="text-2xl font-bold text-black lowercase">common</span>
            </div>

            {/* Navigation Links */}
            <div className="hidden md:flex items-center space-x-8">
              <a href="#product" className="text-neutral-600 hover:text-neutral-900 transition-colors">
                Product
              </a>
              <a href="#solutions" className="text-neutral-600 hover:text-neutral-900 transition-colors">
                Solutions
              </a>
              <Link
                to="/login"
                className="text-neutral-600 hover:text-neutral-900 transition-colors"
              >
                Login
              </Link>
              <Button variant="primary" size="sm">
                Request Demo
              </Button>
            </div>

            {/* Mobile menu button */}
            <div className="md:hidden">
              <Link to="/login">
                <Button variant="ghost" size="sm">
                  Login
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="bg-gradient-to-b from-neutral-50 to-white py-20 lg:py-32">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-4xl mx-auto">
            <h1 className="text-4xl md:text-6xl font-bold text-neutral-900 mb-6 leading-tight">
              Supply Chain Transparency, Built on{' '}
              <span className="text-primary-600">Collaboration</span>—Not Complexity.
            </h1>
            <p className="text-xl text-neutral-600 mb-8 leading-relaxed">
              The single platform for a trusted, auditable supply chain. Prove compliance for EUDR & UFLPA, 
              de-risk operations, and unlock innovation through collaboration.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button variant="primary" size="lg" className="text-lg px-8 py-4">
                Request a Demo
              </Button>
              <Button 
                variant="secondary" 
                size="lg" 
                leftIcon={<PlayIcon className="h-5 w-5" />}
                className="text-lg px-8 py-4"
              >
                Watch the Video (2 min)
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Problem Section */}
      <section className="py-20 bg-neutral-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-neutral-900 mb-6">
              Lost in Spreadsheets. Buried in Data Chaos.
            </h2>
            <p className="text-xl text-neutral-600 max-w-3xl mx-auto mb-12">
              Full traceability feels impossible when your data is trapped in emails and conflicting files. 
              You're left fighting fires, verifying claims manually, and dreading compliance deadlines.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <Card className="text-center">
              <CardBody>
                <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <DocumentTextIcon className="h-8 w-8 text-red-600" />
                </div>
                <h3 className="text-xl font-semibold text-neutral-900 mb-3">For Brands</h3>
                <p className="text-neutral-600">
                  Can't prove your products are compliant or ethically sourced.
                </p>
              </CardBody>
            </Card>

            <Card className="text-center">
              <CardBody>
                <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <UserGroupIcon className="h-8 w-8 text-orange-600" />
                </div>
                <h3 className="text-xl font-semibold text-neutral-900 mb-3">For Suppliers</h3>
                <p className="text-neutral-600">
                  Drowning in different data requests, in different formats, from every customer.
                </p>
              </CardBody>
            </Card>

            <Card className="text-center">
              <CardBody>
                <div className="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <ChartBarIcon className="h-8 w-8 text-yellow-600" />
                </div>
                <h3 className="text-xl font-semibold text-neutral-900 mb-3">For Consultants</h3>
                <p className="text-neutral-600">
                  Buried in manual data collection instead of providing strategic value.
                </p>
              </CardBody>
            </Card>
          </div>
        </div>
      </section>

      {/* Solution Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-neutral-900 mb-6">
              A Single Source of Truth for Your Supply Chain.
            </h2>
            <p className="text-xl text-neutral-600 max-w-3xl mx-auto">
              Common creates clarity from chaos. We turn the universal purchase order into a living, 
              verifiable record of your product's journey—creating common ground for you and your suppliers.
            </p>
          </div>

          {/* How it Works */}
          <div className="grid md:grid-cols-3 gap-8 mb-16">
            <div className="text-center">
              <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-primary-600">1</span>
              </div>
              <h3 className="text-xl font-semibold text-neutral-900 mb-3">Create & Connect</h3>
              <p className="text-neutral-600">
                Brands create POs and invite suppliers to build the chain together.
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-primary-600">2</span>
              </div>
              <h3 className="text-xl font-semibold text-neutral-900 mb-3">Confirm & Comply</h3>
              <p className="text-neutral-600">
                Suppliers confirm orders and link materials in a simple, standardized way.
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-primary-600">3</span>
              </div>
              <h3 className="text-xl font-semibold text-neutral-900 mb-3">See & Secure</h3>
              <p className="text-neutral-600">
                Visualize your entire network and generate one-click compliance reports.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Benefits by Role Section */}
      <section id="solutions" className="py-20 bg-neutral-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-neutral-900 mb-6">
              Built for Every Role in Your Supply Chain
            </h2>
          </div>

          {/* Tab Navigation */}
          <div className="flex justify-center mb-12">
            <div className="bg-white rounded-lg p-1 shadow-sm border border-neutral-200">
              <button
                onClick={() => setActiveTab('brands')}
                className={`px-6 py-3 rounded-md font-medium transition-colors ${
                  activeTab === 'brands'
                    ? 'bg-primary-600 text-white'
                    : 'text-neutral-600 hover:text-neutral-900'
                }`}
              >
                For Brands
              </button>
              <button
                onClick={() => setActiveTab('suppliers')}
                className={`px-6 py-3 rounded-md font-medium transition-colors ${
                  activeTab === 'suppliers'
                    ? 'bg-primary-600 text-white'
                    : 'text-neutral-600 hover:text-neutral-900'
                }`}
              >
                For Suppliers
              </button>
              <button
                onClick={() => setActiveTab('consultants')}
                className={`px-6 py-3 rounded-md font-medium transition-colors ${
                  activeTab === 'consultants'
                    ? 'bg-primary-600 text-white'
                    : 'text-neutral-600 hover:text-neutral-900'
                }`}
              >
                For Consultants
              </button>
            </div>
          </div>

          {/* Tab Content */}
          <div className="max-w-4xl mx-auto">
            {activeTab === 'brands' && (
              <Card>
                <CardBody>
                  <h3 className="text-2xl font-bold text-neutral-900 mb-6 text-center">
                    For Sustainability & Procurement Leaders
                  </h3>
                  <div className="grid md:grid-cols-3 gap-6">
                    <div className="text-center">
                      <ShieldCheckIcon className="h-12 w-12 text-primary-600 mx-auto mb-4" />
                      <h4 className="font-semibold text-neutral-900 mb-2">Achieve Compliance, Effortlessly</h4>
                      <p className="text-neutral-600 text-sm">Generate auditable EUDR and UFLPA reports in minutes.</p>
                    </div>
                    <div className="text-center">
                      <ChartBarIcon className="h-12 w-12 text-primary-600 mx-auto mb-4" />
                      <h4 className="font-semibold text-neutral-900 mb-2">De-risk Your Supply Chain</h4>
                      <p className="text-neutral-600 text-sm">Identify and address risks before they become crises.</p>
                    </div>
                    <div className="text-center">
                      <CheckIcon className="h-12 w-12 text-primary-600 mx-auto mb-4" />
                      <h4 className="font-semibold text-neutral-900 mb-2">Power Marketing with Verified Data</h4>
                      <p className="text-neutral-600 text-sm">Prove your sustainability claims with confidence.</p>
                    </div>
                  </div>
                </CardBody>
              </Card>
            )}

            {activeTab === 'suppliers' && (
              <Card>
                <CardBody>
                  <h3 className="text-2xl font-bold text-neutral-900 mb-6 text-center">
                    For Suppliers & Processors
                  </h3>
                  <div className="grid md:grid-cols-3 gap-6">
                    <div className="text-center">
                      <GlobeAltIcon className="h-12 w-12 text-primary-600 mx-auto mb-4" />
                      <h4 className="font-semibold text-neutral-900 mb-2">One Platform, All Customers</h4>
                      <p className="text-neutral-600 text-sm">Manage all transparency requests in one place, one format.</p>
                    </div>
                    <div className="text-center">
                      <UserGroupIcon className="h-12 w-12 text-primary-600 mx-auto mb-4" />
                      <h4 className="font-semibold text-neutral-900 mb-2">Become a Preferred Partner</h4>
                      <p className="text-neutral-600 text-sm">Win more business with proven sustainability.</p>
                    </div>
                    <div className="text-center">
                      <ShieldCheckIcon className="h-12 w-12 text-primary-600 mx-auto mb-4" />
                      <h4 className="font-semibold text-neutral-900 mb-2">Own Your Data</h4>
                      <p className="text-neutral-600 text-sm">Build a verifiable profile to share with any customer.</p>
                    </div>
                  </div>
                </CardBody>
              </Card>
            )}

            {activeTab === 'consultants' && (
              <Card>
                <CardBody>
                  <h3 className="text-2xl font-bold text-neutral-900 mb-6 text-center">
                    For Sustainability Consultants
                  </h3>
                  <div className="grid md:grid-cols-3 gap-6">
                    <div className="text-center">
                      <ArrowRightIcon className="h-12 w-12 text-primary-600 mx-auto mb-4" />
                      <h4 className="font-semibold text-neutral-900 mb-2">Shift from Detective to Strategist</h4>
                      <p className="text-neutral-600 text-sm">Stop chasing data; start delivering high-value advice.</p>
                    </div>
                    <div className="text-center">
                      <ChartBarIcon className="h-12 w-12 text-primary-600 mx-auto mb-4" />
                      <h4 className="font-semibold text-neutral-900 mb-2">Manage All Clients on One Dashboard</h4>
                      <p className="text-neutral-600 text-sm">Identify gaps and opportunities at a glance.</p>
                    </div>
                    <div className="text-center">
                      <DocumentTextIcon className="h-12 w-12 text-primary-600 mx-auto mb-4" />
                      <h4 className="font-semibold text-neutral-900 mb-2">Show Clear Progress with Instant Reports</h4>
                      <p className="text-neutral-600 text-sm">Deliver tangible, measurable value to your clients.</p>
                    </div>
                  </div>
                </CardBody>
              </Card>
            )}
          </div>
        </div>
      </section>

      {/* Technical Edge Section */}
      <section id="product" className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-neutral-900 mb-6">
              Built for Real-World Complexity.
            </h2>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            <Card className="text-center">
              <CardBody>
                <DocumentTextIcon className="h-12 w-12 text-primary-600 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-neutral-900 mb-3">Unified PO System</h3>
                <p className="text-neutral-600 text-sm">
                  Creates a shared, immutable audit trail from a single document.
                </p>
              </CardBody>
            </Card>

            <Card className="text-center">
              <CardBody>
                <ShieldCheckIcon className="h-12 w-12 text-primary-600 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-neutral-900 mb-3">Granular Permissions</h3>
                <p className="text-neutral-600 text-sm">
                  Share proof of provenance while protecting sensitive commercial data.
                </p>
              </CardBody>
            </Card>

            <Card className="text-center">
              <CardBody>
                <GlobeAltIcon className="h-12 w-12 text-primary-600 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-neutral-900 mb-3">Flexible Traceability</h3>
                <p className="text-neutral-600 text-sm">
                  Adapts to any sourcing model, from mega-mills to smallholders.
                </p>
              </CardBody>
            </Card>

            <Card className="text-center">
              <CardBody>
                <CogIcon className="h-12 w-12 text-primary-600 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-neutral-900 mb-3">API-Ready</h3>
                <p className="text-neutral-600 text-sm">
                  Integrates with your existing ERP and procurement systems.
                </p>
              </CardBody>
            </Card>
          </div>
        </div>
      </section>

      {/* Social Proof Section */}
      <section className="py-20 bg-neutral-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-neutral-900 mb-12">
              Trusted by Leading Brands and Their Suppliers.
            </h2>

            {/* Logo Wall Placeholder */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-16 opacity-60">
              <div className="bg-neutral-200 h-16 rounded-lg flex items-center justify-center">
                <span className="text-neutral-500 font-medium">Brand 1</span>
              </div>
              <div className="bg-neutral-200 h-16 rounded-lg flex items-center justify-center">
                <span className="text-neutral-500 font-medium">Brand 2</span>
              </div>
              <div className="bg-neutral-200 h-16 rounded-lg flex items-center justify-center">
                <span className="text-neutral-500 font-medium">Supplier 1</span>
              </div>
              <div className="bg-neutral-200 h-16 rounded-lg flex items-center justify-center">
                <span className="text-neutral-500 font-medium">Supplier 2</span>
              </div>
            </div>

            {/* Testimonial */}
            <Card className="max-w-4xl mx-auto">
              <CardBody>
                <div className="text-center">
                  <div className="w-16 h-16 bg-neutral-200 rounded-full mx-auto mb-6"></div>
                  <blockquote className="text-xl text-neutral-700 mb-6 italic">
                    "Common finally gave us a way to get accurate data from our suppliers without the endless back-and-forth.
                    Our first EUDR report took 60 seconds, not 6 weeks."
                  </blockquote>
                  <cite className="text-neutral-600 font-medium">
                    — Chief Sustainability Officer, Leading Apparel Brand
                  </cite>
                </div>
              </CardBody>
            </Card>
          </div>
        </div>
      </section>

      {/* Final CTA Section */}
      <section className="py-20 bg-primary-600">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
            Ready for Supply Chain Clarity?
          </h2>
          <p className="text-xl text-primary-100 mb-8 max-w-2xl mx-auto">
            Turn supply chain risk into your competitive advantage. Schedule a demo to see how.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button variant="secondary" size="lg" className="text-lg px-8 py-4">
              Get Your Personalized Demo
            </Button>
            <Button variant="ghost" size="lg" className="text-lg px-8 py-4 text-white border-white hover:bg-white hover:text-primary-600">
              Download EUDR Compliance Guide
            </Button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer id="company" className="bg-neutral-900 text-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div>
              <span className="text-2xl font-bold lowercase">common</span>
              <p className="text-neutral-400 mt-4">
                Supply chain transparency, built on collaboration—not complexity.
              </p>
            </div>

            <div>
              <h3 className="font-semibold mb-4">Product</h3>
              <ul className="space-y-2 text-neutral-400">
                <li><a href="#" className="hover:text-white transition-colors">Platform</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Integrations</a></li>
                <li><a href="#" className="hover:text-white transition-colors">API</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Security</a></li>
              </ul>
            </div>

            <div>
              <h3 className="font-semibold mb-4">Solutions</h3>
              <ul className="space-y-2 text-neutral-400">
                <li><a href="#" className="hover:text-white transition-colors">EUDR Compliance</a></li>
                <li><a href="#" className="hover:text-white transition-colors">UFLPA Compliance</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Supply Chain Mapping</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Risk Management</a></li>
              </ul>
            </div>

            <div>
              <h3 className="font-semibold mb-4">Resources</h3>
              <ul className="space-y-2 text-neutral-400">
                <li><a href="#" className="hover:text-white transition-colors">Documentation</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Blog</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Case Studies</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Support</a></li>
              </ul>
            </div>
          </div>

          <div className="border-t border-neutral-800 pt-8 flex flex-col md:flex-row justify-between items-center">
            <p className="text-neutral-400 text-sm">
              © 2025 Common, Inc. All rights reserved.
            </p>
            <div className="flex space-x-6 mt-4 md:mt-0">
              <a href="#" className="text-neutral-400 hover:text-white text-sm transition-colors">
                Privacy Policy
              </a>
              <a href="#" className="text-neutral-400 hover:text-white text-sm transition-colors">
                Terms of Service
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
