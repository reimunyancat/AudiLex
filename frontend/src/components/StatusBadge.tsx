import React from 'react';
import { Badge } from './ui/Badge';

interface StatusBadgeProps {
	label: string;
	status: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ label, status }) => {
	let variant: 'default' | 'success' | 'warning' | 'error' | 'neutral' = 'neutral';

	switch (status) {
		case 'Finished':
			variant = 'success';
			break;
		case 'Processing':
			variant = 'warning';
			break;
		case 'Failed':
			variant = 'error';
			break;
		case 'Pending':
		case 'None':
		default:
			variant = 'neutral';
			break;
	}

	return (
		<div className="flex items-center gap-2">
			<span className="text-xs text-slate-400">{label}</span>
			<Badge variant={variant}>{status}</Badge>
		</div>
	);
};
