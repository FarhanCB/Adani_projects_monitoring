import React, { useState } from 'react';
import { HeatmapBlock } from '../types';

interface UptimeHeatmapProps {
  blocks: HeatmapBlock[];
  rangeLabel: string;
  uptimePct: number;
}

export const UptimeHeatmap: React.FC<UptimeHeatmapProps> = ({
  blocks,
  rangeLabel,
  uptimePct,
}) => {
  const [activeTooltip, setActiveTooltip] = useState<HeatmapBlock | null>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  const getBlockColor = (status: string) => {
    switch (status) {
      case 'UP':
        return 'bg-emerald-500 hover:bg-emerald-600';
      case 'DOWN':
        return 'bg-rose-500 hover:bg-rose-600';
      case 'WARNING':
        return 'bg-amber-500 hover:bg-amber-600';
      case 'NO_DATA':
      default:
        return 'bg-slate-200 hover:bg-slate-300';
    }
  };

  const handleMouseEnter = (block: HeatmapBlock, e: React.MouseEvent) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setTooltipPos({ x: rect.left + rect.width / 2, y: rect.top - 10 });
    setActiveTooltip(block);
  };

  return (
    <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-subtle relative">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h4 className="text-sm font-bold text-slate-900">Uptime Timeline & Heatmap</h4>
          <p className="text-xs text-slate-500">{rangeLabel} • Chronological status blocks</p>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-xs text-slate-500">Overall:</span>
          <span className="text-sm font-black text-slate-900 px-2 py-0.5 rounded bg-slate-100 border border-slate-200">
            {uptimePct.toFixed(2)}%
          </span>
        </div>
      </div>

      {/* Heatmap Blocks Grid */}
      <div className="flex items-center gap-1 w-full overflow-x-auto py-2">
        {blocks.map((block, idx) => (
          <div
            key={idx}
            onMouseEnter={(e) => handleMouseEnter(block, e)}
            onMouseLeave={() => setActiveTooltip(null)}
            className={`flex-1 min-w-[8px] h-9 rounded-sm cursor-pointer transition-all transform hover:scale-110 ${getBlockColor(
              block.status
            )}`}
          />
        ))}
      </div>

      {/* Range Start and End Labels */}
      <div className="flex items-center justify-between text-[11px] text-slate-400 mt-2 font-mono">
        <span>{blocks[0]?.label || 'Start'}</span>
        <span>Today / Latest</span>
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center space-x-6 mt-4 pt-3 border-t border-slate-100 text-xs">
        <div className="flex items-center space-x-1.5">
          <span className="w-3 h-3 rounded-sm bg-emerald-500" />
          <span className="text-slate-600 font-medium">UP (Operational)</span>
        </div>
        <div className="flex items-center space-x-1.5">
          <span className="w-3 h-3 rounded-sm bg-rose-500" />
          <span className="text-slate-600 font-medium">DOWN (Outage)</span>
        </div>
        <div className="flex items-center space-x-1.5">
          <span className="w-3 h-3 rounded-sm bg-amber-500" />
          <span className="text-slate-600 font-medium">WARNING (Slow/SSL)</span>
        </div>
        <div className="flex items-center space-x-1.5">
          <span className="w-3 h-3 rounded-sm bg-slate-200" />
          <span className="text-slate-600 font-medium">NO DATA</span>
        </div>
      </div>

      {/* Floating Tooltip */}
      {activeTooltip && (
        <div
          className="fixed z-50 transform -translate-x-1/2 -translate-y-full pointer-events-none bg-slate-900 text-white text-xs rounded-lg p-2.5 shadow-xl border border-slate-700 min-w-[160px]"
          style={{ left: `${tooltipPos.x}px`, top: `${tooltipPos.y}px` }}
        >
          <div className="font-bold border-b border-slate-700 pb-1 mb-1.5 text-slate-200">
            {activeTooltip.label}
          </div>
          <div className="flex justify-between items-center mb-1">
            <span className="text-slate-400">Status:</span>
            <span
              className={`font-bold ${
                activeTooltip.status === 'UP'
                  ? 'text-emerald-400'
                  : activeTooltip.status === 'DOWN'
                  ? 'text-rose-400'
                  : activeTooltip.status === 'WARNING'
                  ? 'text-amber-400'
                  : 'text-slate-400'
              }`}
            >
              {activeTooltip.status}
            </span>
          </div>
          {activeTooltip.http_status && (
            <div className="flex justify-between items-center mb-1">
              <span className="text-slate-400">HTTP Code:</span>
              <span className="font-mono text-slate-200">{activeTooltip.http_status}</span>
            </div>
          )}
          {activeTooltip.response_time_ms && (
            <div className="flex justify-between items-center mb-1">
              <span className="text-slate-400">Latency:</span>
              <span className="font-mono text-slate-200">{activeTooltip.response_time_ms} ms</span>
            </div>
          )}
          {activeTooltip.error_type && (
            <div className="text-rose-300 font-medium text-[11px] mt-1">
              {activeTooltip.error_type}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
