// "What to check in Simpro" for each NEEDS_REVIEW code. Mirrors agent/margin_watch/labels.py.
export const WHAT_TO_CHECK: Record<string, string> = {
	no_cost_centres: 'Check the job has its cost centres set up in Simpro.',
	missing_sell: 'Check the quoted sell price on the job in Simpro.',
	non_positive_sell: 'Check the quoted sell price on the job in Simpro.',
	missing_cost: "Check the cost centre's estimate and actual cost in Simpro.",
	negative_cost: 'Look for a credit or reversal posted to the wrong job or cost centre in Simpro.',
	missing_percent_complete: "Ask the PM for the job's percent complete and update it in Simpro.",
	percent_out_of_range: "Correct the job's percent complete in Simpro.",
	zero_percent_with_costs: 'Check whether work has started and update the percent complete in Simpro.'
};
