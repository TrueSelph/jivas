import type { Action } from "~/types";
import type { Route } from "./+types/actions";
import { Box, Divider, SimpleGrid, Title } from "@mantine/core";
import { ActionCard } from "~/components/ActionCard";

// export async function loader() {
// 	return {
// 		user: {
// 			host: process.env.JIVAS_HOST,
// 			email: process.env.JIVAS_USER,
// 			password: process.env.JIVAS_PASSWORD,
// 		},
// 	};
// }
//
//

export function meta() {
	return [{ title: "Actions | JIVAS Manager" }];
}

export async function clientAction({ request }: Route.ClientLoaderArgs) {
	const data = await request.formData();
	const agentId = data.get("agentId") as string;

	localStorage.setItem("jivas-agent", agentId);

	// const result = (await fetch(`${host}/walker/list_agents`, {
	// 	method: "POST",
	// 	body: JSON.stringify({}),
	// 	headers: {
	// 		"Content-Type": "application/json",
	// 		Authorization: `Bearer ${token}`,
	// 	},
	// }).then((res) => res.json())) as { reports: Agent[] };

	return {
		// agents: result?.reports,
	};
}

export async function clientLoader({ serverLoader }: Route.ClientLoaderArgs) {
	const host = localStorage.getItem("jivas-host");
	const token = localStorage.getItem("jivas-token");

	try {
		const result = (await fetch(`${host}/walker/list_actions`, {
			method: "POST",
			body: JSON.stringify({ agent_id: localStorage.getItem("jivas-agent") }),
			headers: {
				"Content-Type": "application/json",
				Authorization: `Bearer ${token}`,
			},
		}).then((res) => res.json())) as { reports: [Action[]] };

		return {
			// loginResult,
			actions: result.reports[0],
		};
	} catch (err) {
		return { actions: [] };
	}
}

export default function ChatRoute({ loaderData }: Route.ComponentProps) {
	return (
		<Box px="xl" py="xl">
			<Title order={3}>Actions</Title>
			<Divider mt="xs" mb="xl" />

			<SimpleGrid cols={{ base: 1, md: 2, lg: 4 }}>
				{loaderData.actions
					.sort((a, b) =>
						(a._package?.meta?.title || a.label).localeCompare(
							b._package?.meta?.title || b.label,
						),
					)
					.map((action) => (
						<ActionCard key={action.id} action={action} />
					))}
			</SimpleGrid>
		</Box>
	);
}
