import React from "react";

interface CardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
}

export const Card: React.FC<CardProps> = ({
  children,
  className = "",
  onClick,
}) => {
  return (
    <div
      className={`bg-gray-500/10 rounded-xl border border-slate-700 shadow-sm overflow-hidden ${
        onClick ? "cursor-pointer hover:border-slate-600 transition-colors" : ""
      } ${className}`}
      onClick={onClick}
    >
      {children}
    </div>
  );
};

export const CardHeader: React.FC<{
  children: React.ReactNode;
  className?: string;
}> = ({ children, className = "" }) => (
  <div className={`px-6 py-4 border-b border-slate-700 ${className}`}>
    {children}
  </div>
);

export const CardTitle: React.FC<{
  children: React.ReactNode;
  className?: string;
}> = ({ children, className = "" }) => (
  <h3 className={`text-lg font-semibold text-white ${className}`}>
    {children}
  </h3>
);

export const CardContent: React.FC<{
  children: React.ReactNode;
  className?: string;
  ref?: React.Ref<HTMLDivElement>;
}> = React.forwardRef(({ children, className = "" }, ref) => (
  <div ref={ref} className={`p-6 ${className}`}>
    {children}
  </div>
));
