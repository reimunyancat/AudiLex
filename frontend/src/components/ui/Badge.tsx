import React from 'react';

interface BadgeProps {
	children: React.ReactNode;
	variant?: 'default' | 'success' | 'warning' | 'error' | 'neutral';
	className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ children, variant = 'default', className = '' }) => {
	const variants = {
		default: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
		success: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
		warning: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
		error: 'bg-red-500/10 text-red-400 border-red-500/20',
		neutral: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
	};

	return (
		<span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${variants[variant]} ${className}`}>
			{children}
		</span>
	);
};
