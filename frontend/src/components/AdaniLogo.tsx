import React from 'react';

interface AdaniLogoProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  showSubtitle?: boolean;
}

export const AdaniLogo: React.FC<AdaniLogoProps> = ({
  className = '',
  size = 'md',
  showSubtitle = false,
}) => {
  const heightClasses = {
    sm: 'h-6',
    md: 'h-8',
    lg: 'h-10',
    xl: 'h-14',
  };

  return (
    <div className={`inline-flex items-center space-x-2.5 ${className}`}>
      <img
        src="/adani-logo.png"
        alt="Adani"
        className={`${heightClasses[size]} w-auto object-contain select-none`}
        onError={(e) => {
          // Fallback if image path varies
          const target = e.currentTarget;
          target.onerror = null;
          target.src = '/src/assets/adani-logo.png';
        }}
      />
      {showSubtitle && (
        <span className="text-[10px] font-bold tracking-widest uppercase text-[#583896] border-l border-slate-300 pl-2">
          Monitoring
        </span>
      )}
    </div>
  );
};
