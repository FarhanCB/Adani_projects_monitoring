import React, { useState } from 'react';
import { Lock, Mail, ArrowRight, AlertCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { AdaniLogo } from '../components/AdaniLogo';

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login({ email, password });
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please check credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col justify-center py-12 sm:px-6 lg:px-8 bg-slate-50 relative overflow-hidden">
      {/* Background Decorative Gradient Blobs with Adani Colors */}
      <div className="absolute top-0 right-0 -mt-20 -mr-20 w-96 h-96 rounded-full bg-gradient-to-br from-blue-200/40 via-purple-200/40 to-pink-200/40 blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 left-0 -mb-20 -ml-20 w-96 h-96 rounded-full bg-gradient-to-tr from-sky-100/50 via-indigo-100/50 to-pink-100/50 blur-3xl pointer-events-none" />

      <div className="sm:mx-auto sm:w-full sm:max-w-md relative z-10 text-center">
        {/* Official Adani Logo */}
        <div className="flex justify-center mb-3">
          <AdaniLogo size="xl" />
        </div>
        <h2 className="text-center text-xl font-black text-slate-900 tracking-tight mt-2">
          Enterprise Infrastructure Monitoring
        </h2>
        <p className="text-center text-xs font-bold uppercase tracking-widest text-[#583896] mt-0.5">
          Internal Services & Uptime Analytics Suite
        </p>
      </div>

      <div className="mt-7 sm:mx-auto sm:w-full sm:max-w-md relative z-10">
        <div className="bg-white py-8 px-6 shadow-card sm:rounded-2xl sm:px-10 border border-slate-200/80">
          <form className="space-y-5" onSubmit={handleSubmit}>
            {error && (
              <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm flex items-start space-x-2">
                <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">
                Corporate Email Address
              </label>
              <div className="relative rounded-lg shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                  <Mail className="w-4 h-4" />
                </div>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@adani.com"
                  className="block w-full pl-10 pr-3 py-2.5 sm:text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#583896] focus:border-transparent transition-all"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">
                Password
              </label>
              <div className="relative rounded-lg shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="block w-full pl-10 pr-3 py-2.5 sm:text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#583896] focus:border-transparent transition-all"
                />
              </div>
            </div>

            {/* Signature Adani Tri-Color Gradient Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center items-center space-x-2 py-3 px-4 rounded-lg shadow-adani text-sm font-bold text-white bg-gradient-to-r from-[#0078BD] via-[#583896] to-[#BE185D] hover:opacity-95 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#583896] transition-all disabled:opacity-50"
            >
              <span>{loading ? 'Authenticating...' : 'Sign In to Portal'}</span>
              {!loading && <ArrowRight className="w-4 h-4" />}
            </button>
          </form>

        </div>

        <div className="text-center mt-6 text-xs text-slate-400">
          Adani Group • Enterprise Infrastructure Monitoring Node
        </div>
      </div>
    </div>
  );
};
