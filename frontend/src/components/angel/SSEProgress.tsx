import { motion } from 'framer-motion';

type Phase = 'ghost' | 'real' | 'enriched' | 'realtime' | 'complete';

const labels: Record<Phase, string> = {
  ghost: 'Instant Ghost Results',
  real: 'Real Results',
  enriched: 'AI Enrichment',
  realtime: 'Real-time Context',
  complete: 'Complete',
};

const order: Phase[] = ['ghost', 'real', 'enriched', 'realtime', 'complete'];

export function SSEProgress({ phase }: { phase: Phase }) {
  const currentIndex = order.indexOf(phase);
  return (
    <div className="w-full max-w-3xl mx-auto">
      <div className="flex items-center justify-between gap-2">
        {order.map((p, idx) => {
          const active = idx <= currentIndex;
          return (
            <div key={p} className="flex-1 flex items-center">
              <div className="flex flex-col items-center gap-1 w-full">
                <motion.div
                  className={`h-2 w-full rounded-full ${active ? 'bg-gradient-to-r from-fuchsia-500 to-sky-500' : 'bg-zinc-200 dark:bg-zinc-800'}`}
                  layout
                />
                <span className={`text-[10px] tracking-wide ${active ? 'text-fuchsia-400' : 'text-muted-foreground'}`}>{labels[p]}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default SSEProgress;
