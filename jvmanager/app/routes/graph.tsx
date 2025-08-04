import { ActionIcon, Box, Card, Divider, Group, Title } from "@mantine/core";
import { IconArrowLeft } from "@tabler/icons-react";
import { Link, redirect } from "react-router";
import { UserButton } from "~/components/UserButton";
import { fetchWithAuth } from "~/lib/api";
import type { Route } from "./+types/graph";
import type { Agent } from "~/types";

export function meta() {
	return [{ title: "Actions | JIVAS Manager" }];
}

export async function clientLoader({ request }: Route.ClientLoaderArgs) {
	const host = localStorage.getItem("jivas-host");
	const selectedAgent = localStorage.getItem("jivas-agent");

	const selectedAgentInfo = selectedAgent
		? ((await fetchWithAuth(`${host}/walker/get_agent`, {
				method: "POST",
				body: JSON.stringify({ agent_id: selectedAgent }),
				headers: {
					"Content-Type": "application/json",
				},
			})
				.then((res) => {
					if (res.ok) {
						return res.json();
					} else {
						localStorage.removeItem("jivas-agent");
						throw redirect("/login");
					}
				})
				.catch((err) => {
					console.log({ err });
					localStorage.removeItem("jivas-agent");
					throw redirect("/login");
				})) as { reports: Agent[] })
		: null;

	const formData = new FormData();
	formData.append("args", `{"base64_prefix": false}`);
	formData.append("module_root", "actions.jivas.avatar_action");
	formData.append("agent_id", selectedAgentInfo?.reports?.[0]?.id || "");
	formData.append("walker", "get_avatar");

	const avatar = (await fetchWithAuth(`${host}/action/walker`, {
		method: "POST",
		body: formData,
	})
		.then(async (res) => await res.json())
		.catch(() => null)) as [string, string] | null;

	const result = (await fetchWithAuth(`${host}/walker/list_agents`, {
		method: "POST",
		body: JSON.stringify({}),
		headers: {
			"Content-Type": "application/json",
		},
	})
		.then((res) => res.json())
		.catch(() => {
			return { reports: [] };
		})) as { reports: Agent[] };

	return {
		selectedAgentInfo: {
			...(selectedAgentInfo?.reports?.[0] || {}),
			thumbnail:
				!avatar?.includes?.("unable") && !!avatar && typeof avatar === "string"
					? `data:image/png;base64,${avatar}`
					: "",
		},
		agents: result?.reports,
	};
}

export default function ChatRoute({ loaderData }: Route.ComponentProps) {
	const host = localStorage.getItem("jivas-host");
	const root = localStorage.getItem("jivas-root-id");

	return (
		<Box px="xl">
			<Group justify="space-between">
				<Group>
					<ActionIcon color="dark" size="sm" component={Link} to="/dashboard">
						<IconArrowLeft />
					</ActionIcon>
					<Title order={3}>Graph</Title>
				</Group>
				<Box>
					<UserButton
						selectedAgentInfo={loaderData.selectedAgentInfo || null}
						agents={loaderData.agents}
					/>
				</Box>
			</Group>

			<Divider mt="xs" mb="sm" />

			<Card px="0" py="0" h="86vh" withBorder pos="relative">
				<jvgraph-viewer
					className="min-h-[740px]"
					key={loaderData.selectedAgentInfo.id}
					host={host}
					root_node={root}
					host={host}
					style={{
						width: "100%",
						height: "100%",
						border: "none",
						outline: "none",
					}}
					// className="w-full h-full bg-[red]"
				/>
			</Card>
		</Box>
	);
}
