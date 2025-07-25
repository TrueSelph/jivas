import type { Agent } from "~/types";

interface ApiResponse<T> {
	status: number;
	reports: T[];
}

export function getInstanceToken() {
	const host = localStorage.getItem("jivas-host");
	const token = localStorage.getItem("jivas-token");
	return { instance: { url: host }, tokenResult: { token } };
}

export async function getChannelsByDate({
	agentId,
	endDate,
	startDate,
	timezone,
}: {
	agentId: string;
	startDate: string;
	endDate: string;
	timezone: string;
}) {
	const { instance, tokenResult } = getInstanceToken();
	const res = (await fetch(`${instance.url}/walker/get_channels_by_date`, {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
			Authorization: `Bearer ${tokenResult.token}`,
		},
		body: JSON.stringify({
			reporting: true,
			start_date: startDate,
			end_date: endDate,
			timezone,
			agent_id: agentId,
		}),
	}).then(async (res) => await res.json())) as ApiResponse<Agent>;

	return res?.reports?.[0] ?? {};
}

export async function getInteractionsByDate({
	agentId,
	endDate,
	startDate,
	timezone,
}: {
	agentId: string;
	startDate: string;
	endDate: string;
	timezone: string;
}) {
	const { instance, tokenResult } = getInstanceToken();
	const res = (await fetch(`${instance.url}/walker/get_interactions_by_date`, {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
			Authorization: `Bearer ${tokenResult.token}`,
		},
		body: JSON.stringify({
			reporting: true,
			start_date: startDate,
			end_date: endDate,
			timezone,
			agent_id: agentId,
		}),
	})
		.then(async (res) => await res.json())
		.catch(() => {
			return { reports: [{ total: 0, interactions: [] }] };
		})) as ApiResponse<Agent>;
	console.log({ timezone, startDate, endDate });

	console.log(JSON.stringify(res));

	return res?.reports?.[0] ?? {};
}

export async function getUsersByDate({
	agentId,
	endDate,
	startDate,
	timezone,
}: {
	agentId: string;
	startDate: string;
	endDate: string;
	timezone: string;
}) {
	const { instance, tokenResult } = getInstanceToken();
	const res = (await fetch(`${instance.url}/walker/get_users_by_date`, {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
			Authorization: `Bearer ${tokenResult.token}`,
		},
		body: JSON.stringify({
			reporting: true,
			start_date: startDate,
			end_date: endDate,
			agent_id: agentId,
			timezone,
		}),
	}).then(async (res) => await res.json())) as ApiResponse<Agent>;

	return res?.reports?.[0] ?? {};
}
