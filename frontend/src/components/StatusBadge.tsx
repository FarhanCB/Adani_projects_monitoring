import React from 'react';

interface StatusBadgeProps {
  status: 'UP' | 'DOWN' | 'WARNING' | 'PAUSED' | 'PENDING' | string;
  size?: 'sm' | 'md' | 'lg';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  size = 'md',
}) => {
  const norm = (status || '').toUpperCase();

  let bgClass = 'bg-slate-100 text-slate-700 border-slate-200';
  let dotClass = 'bg-slate-400';
  let label = norm || 'PENDING';

  if (norm === 'UP') {
    bgClass = 'bg-emerald-50 text-emerald-700 border-emerald-200';
    dotClass = 'bg-emerald-500';
    label = 'UP';
  } else if (norm === 'DOWN') {
    bgClass = 'bg-rose-50 text-rose-700 border-rose-200';
    dotClass = 'bg-rose-500';
    label = 'DOWN';
  } else if (norm === 'WARNING') {
    bgClass = 'bg-amber-50 text-amber-700 border-amber-200';
    dotClass = 'bg-amber-500';
    label = 'WARNING';
  } else if (norm === 'PAUSED') {
    bgClass = 'bg-slate-100 text-slate-600 border-slate-200';
    dotClass = 'bg-slate-400';
    label = 'PAUSED';
  }

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5 space-x-1.5',
    md: 'text-xs px-2.5 py-1 space-x-2 font-semibold',
    lg: 'text-sm px-3.5 py-1.5 space-x-2.5 font-bold',
  };

  const dotSizes = {
    sm: 'w-1.5 h-1.5',
    md: 'w-2 h-2',
    lg: 'w-2.5 h-2.5',
  };

  return (
    <span
      className={`inline-flex items-center rounded-full border shadow-sm ${bgClass} ${sizeClasses[size]}`}
    >
      <span className={`rounded-full ${dotClass} ${dotSizes[size]}`} />
      <span>{label}</span>
    </span>
  );
};
