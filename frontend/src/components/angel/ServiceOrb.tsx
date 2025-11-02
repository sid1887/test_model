import { useServiceHealth } from '@/api/hooks';

export function ServiceOrb({ className = '' }: { className?: string }) {
  const { data } = useServiceHealth();
  const status = data?.status ?? 'degraded';
  const color = status === 'healthy' ? 'bg-emerald-400' : status === 'degraded' ? 'bg-amber-400' : 'bg-rose-500';

  return (
    <div className={`relative flex items-center gap-2 ${className}`}>
      <div className={`h-3 w-3 rounded-full ${color} shadow-md`} />
      <span className="text-xs text-muted-foreground">{status}</span>
    </div>
  );
}

export default ServiceOrb;
