import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
	label?: string;
	error?: string;
}

export const Input: React.FC<InputProps> = ({ label, error, className = '', ...props }) => {
	return (
		<div className="w-full">
			{label && <label className="block text-sm font-medium text-slate-300 mb-1">{label}</label>}
			<input
				className={`w-full px-4 py-2 bg-gray-500/10 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all ${error ? 'border-red-500 focus:ring-red-500' : ''} ${className}`}
				{...props}
			/>
			{error && <p className="mt-1 text-sm text-red-500">{error}</p>}
		</div>
	);
};
