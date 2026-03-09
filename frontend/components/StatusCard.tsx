type Color = "blue" | "yellow" | "purple" | "orange" | "green" | "red" | "emerald";

const colorMap: Record<Color, { bg: string; text: string; dot: string; border: string }> = {
  blue:    { bg: "bg-blue-950/40",    text: "text-blue-300",    dot: "bg-blue-400",    border: "border-blue-900/50"   },
  yellow:  { bg: "bg-yellow-950/40",  text: "text-yellow-300",  dot: "bg-yellow-400",  border: "border-yellow-900/50" },
  purple:  { bg: "bg-purple-950/40",  text: "text-purple-300",  dot: "bg-purple-400",  border: "border-purple-900/50" },
  orange:  { bg: "bg-orange-950/40",  text: "text-orange-300",  dot: "bg-orange-400",  border: "border-orange-900/50" },
  green:   { bg: "bg-green-950/40",   text: "text-green-300",   dot: "bg-green-400",   border: "border-green-900/50"  },
  red:     { bg: "bg-red-950/40",     text: "text-red-300",     dot: "bg-red-400",     border: "border-red-900/50"    },
  emerald: { bg: "bg-emerald-950/40", text: "text-emerald-300", dot: "bg-emerald-400", border: "border-emerald-900/50"},
};

interface StatusCardProps {
  label: string;
  value: string;
  color: Color;
}

export default function StatusCard({ label, value, color }: StatusCardProps) {
  const c = colorMap[color];
  return (
    <div className={`${c.bg} border ${c.border} rounded-xl p-4 flex flex-col gap-2 animate-fade-in`}>
      <div className="flex items-center gap-1.5">
        <span className={`w-1.5 h-1.5 rounded-full ${c.dot}`} />
        <span className="text-xs text-slate-400 font-medium">{label}</span>
      </div>
      <span className={`text-3xl font-bold ${c.text} font-mono`}>{value}</span>
    </div>
  );
}
