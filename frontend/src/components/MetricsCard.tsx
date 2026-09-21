import React from 'react';

interface MetricsCardProps {
  title: string;
  value: string | number;
  subValue?: string;
  icon: React.ReactNode;
  accentColor?: 'red' | 'green' | 'amber' | 'blue' | 'slate' | 'orange';
  badge?: string;
  onClick?: () => void;
}

export const MetricsCard: React.FC<MetricsCardProps> = ({
  title,
  value,
  subValue,
  icon,
  accentColor = 'slate',
  badge,
  onClick,
}) => {
  const borderAccents = {
    red: 'border-l-4 border-l-rose-600',
    green: 'border-l-4 border-l-emerald-600',
    amber: 'border-l-4 border-l-amber-500',
    orange: 'border-l-4 border-l-orange-500',
    blue: 'border-l-4 border-l-sky-600',
    slate: 'border-l-4 border-l-slate-400',
  };

  const iconBg = {
    red: 'bg-rose-50 text-rose-600',
    green: 'bg-emerald-50 text-emerald-600',
    amber: 'bg-amber-50 text-amber-600',
    orange: 'bg-orange-50 text-orange-600',
    blue: 'bg-sky-50 text-sky-600',
    slate: 'bg-slate-100 text-slate-600',
  };

  return (
    <div
      onClick={onClick}
      className={`bg-white rounded-xl p-5 border border-slate-200/80 shadow-card transition-all duration-200 hover:shadow-hover hover:-translate-y-0.5 ${
        borderAccents[accentColor]
      } ${onClick ? 'cursor-pointer' : ''}`}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">
            {title}
          </p>
          <div className="flex items-baseline space-x-2">
            <span className="text-2xl font-black text-slate-900 tracking-tight">
              {value}
            </span>
            {badge && (
              <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200">
                {badge}
              </span>
            )}
          </div>
          {subValue && (
            <p className="text-xs font-medium text-slate-500 mt-1.5 flex items-center">
              {subValue}
            </p>
          )}
        </div>
        <div className={`p-2.5 rounded-lg ${iconBg[accentColor]}`}>
          {icon}
        </div>
      </div>
    </div>
  );
};
