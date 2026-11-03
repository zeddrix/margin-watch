// Shapes of the files the agent writes (docs/acceptance-criteria.md, AC-34..AC-36).

export type Status = 'LOSS' | 'AT_RISK' | 'WATCH' | 'NEEDS_REVIEW' | 'ON_TRACK';
export type Provider = 'demo' | 'demo-bad' | 'local' | 'claude' | 'none';

export interface CostCentre {
	name: string;
	estimated_cost: number | null;
	actual_cost_to_date: number | null;
	forecast_at_completion: number | null;
	overrun_dollars: number | null;
	overrun_pct: number | null;
	estimated_hours: number | null;
	actual_hours: number | null;
	hourly_rate: number | null;
}

export interface Job {
	id: string;
	name: string;
	client: string;
	site: string;
	stage: string;
	project_manager: string;
	quoted_sell_ex_gst: number | null;
	percent_complete: number | null;
	status: Status;
	reason: string;
	review_code: string | null;
	main_driver: string | null;
	estimated_total: number | null;
	forecast_total: number | null;
	quoted_margin_pct: number | null;
	forecast_margin_pct: number | null;
	margin_erosion_pts: number | null;
	dollars_at_risk: number | null;
	cost_centres: CostCentre[];
}

export interface Summary {
	text: string;
	source: 'ai_verified' | 'template';
	provider: Provider;
	model: string | null;
	fallback_reason: string | null;
	rejected_tokens: string[];
}

export interface Run {
	schema_version: 1;
	as_of: string;
	generated_at: string;
	source: { kind: string; name: string; sample_data: boolean };
	thresholds: Record<string, number>;
	counts: Record<Status, number>;
	portfolio: {
		total_jobs: number;
		jobs_needing_action: number;
		jobs_to_review: number;
		total_dollars_at_risk: number;
		average_forecast_margin_pct: number | null;
	};
	jobs: Job[];
	summary: Summary;
}

export interface RunIndexEntry {
	as_of: string;
	file: string;
	generated_at: string;
	counts: Record<Status, number>;
	jobs_needing_action: number;
	total_dollars_at_risk: number;
	summary_source: 'ai_verified' | 'template';
}

export interface RunIndex {
	schema_version: 1;
	runs: RunIndexEntry[];
}
