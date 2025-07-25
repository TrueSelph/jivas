import { useState } from "react";
import { Radio, Group, Stack, Text } from "@mantine/core";
import classes from "./AgentSelect.module.css";
import type { Agent } from "~/types";
import { useFetcher } from "react-router";

const data = [
	{
		name: "@mantine/core",
		description: "Core components library: inputs, buttons, overlays, etc.",
	},
	{
		name: "@mantine/hooks",
		description: "Collection of reusable hooks for React applications.",
	},
	{ name: "@mantine/notifications", description: "Notifications system" },
];

export function AgentSelect({ agents }: { agents: Agent[] }) {
	const [value, setValue] = useState<string | null>(
		localStorage.getItem("jivas-agent"),
	);

	const fetcher = useFetcher();

	const cards = data.map((item) => (
		<Radio.Card
			className={classes.root}
			radius="md"
			value={item.name}
			key={item.name}
		>
			<Group wrap="nowrap" align="flex-start">
				<Radio.Indicator />
				<div>
					<Text className={classes.label}>{item.name}</Text>
				</div>
			</Group>
		</Radio.Card>
	));

	return (
		<>
			<Radio.Group
				value={value}
				onChange={(val) => {
					setValue(val);
					fetcher.submit(
						{ agentId: val },
						{ method: "POST", action: "/actions" },
					);
				}}
				label="Select an agent"
				description="Which agent would you like to use?"
			>
				<Stack pt="md" gap="xs">
					{agents?.map((agent) => (
						<Radio.Card
							className={classes.root}
							radius="md"
							value={agent.id}
							key={agent.id}
						>
							<Group wrap="nowrap" align="flex-start">
								<Radio.Indicator />
								<div>
									<Text className={classes.label}>{agent.name}</Text>
								</div>
							</Group>
						</Radio.Card>
					))}
				</Stack>
			</Radio.Group>
		</>
	);
}
