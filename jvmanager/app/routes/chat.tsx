import { Box, Button, Card, Divider, Group, Title } from "@mantine/core";
import type { Route } from "./+types/chat";
import type { Agent } from "~/types";
import { useFetcher, useOutletContext } from "react-router";
import { IconEraser } from "@tabler/icons-react";
import { useCallback } from "react";
import { v4 as uuidv4 } from "uuid";

export async function clientLoader() {
	try {
		const token = localStorage.getItem("jivas-token") || "";
		const host = localStorage.getItem("jivas-host") || "";
		const agentId = localStorage.getItem("jivas-agent") || "";

		const existingSessionId = document.cookie.match(/tsSessionId=([^;]+)/)?.[1];
		const sessionId =
			existingSessionId && existingSessionId !== "undefined"
				? existingSessionId
				: uuidv4();

		try {
			// ensure session id is valid
			await fetch(`${host}/walker/add_frame`, {
				method: "POST",
				headers: {
					Authorization: `Bearer ${token}`,
					"Content-Type": "application/json",
				},
				body: JSON.stringify({
					agent_id: agentId,
					session_id: sessionId,
				}),
			}).catch((error) => {
				console.error("Error creating session:", error);
			});
		} catch (err) {
			console.log("unable to create session");
		}

		return {
			sessionId,
			host: localStorage.getItem("jivas-host") || "",
			agentId: localStorage.getItem("jivas-agent") || "",
		};
	} catch (err) {
		console.log(err);
		return {
			sessionId: "jvmanager",
			host: localStorage.getItem("jivas-host") || "",
			agentId: localStorage.getItem("jivas-agent") || "",
		};
	}
}

export async function clientAction({
	context,
	request,
}: Route.ClientActionArgs) {
	const reqFormData = await request.formData();
	const _action = reqFormData.get("_action");

	const formData = new FormData();
	const agentId = reqFormData.get("agentId") || "";
	const token = localStorage.getItem("jivas-token") || "";
	const host = localStorage.getItem("jivas-host") || "";
	const sessionId = reqFormData.get("sessionId");

	if (_action === "wipeAgentMemory") {
		formData.append("args", JSON.stringify({ session_id: sessionId }));

		formData.append("module_root", "actions.jivas.agent_utils_action");
		formData.append("agent_id", agentId);
		formData.append("walker", "purge_frame_memory");

		return await fetch(`${host}/action/walker`, {
			method: "POST",
			headers: {
				Authorization: `Bearer ${token}`,
			},
			body: formData,
		}).then(async (res) => await res.json());
	}
}

export function meta() {
	return [{ title: "Chat | JIVAS Manager" }];
}

export default function ChatRoute({ loaderData }: Route.ComponentProps) {
	const { selectedAgentInfo } = useOutletContext<{
		selectedAgentInfo: Agent & { thumbnail: string };
	}>();

	const clearMessagesFetcher = useFetcher();

	const clearMessages = useCallback(() => {
		const event = new CustomEvent("tsmclearmessages");
		clearMessagesFetcher.submit(
			{
				_action: "wipeAgentMemory",
				agentId: loaderData.agentId || "",
				sessionId: loaderData.sessionId || "",
			},
			{ method: "POST" },
		);

		window.dispatchEvent(event);
	}, []);

	return (
		<Box py="xl" px="xl">
			<Group justify="space-between">
				<Title order={3}>Chat</Title>
				<Button
					color="dark"
					leftSection={<IconEraser className="h-5 w-5" />}
					size="xs"
					onClick={clearMessages}
					loading={clearMessagesFetcher.state !== "idle"}
				>
					Clear Chat Memory
				</Button>
			</Group>

			<Divider mt="xs" mb="xl" />
			<Card px="xl" h="80vh" withBorder>
				<ts-messenger
					// streaming="true"
					// agent-id="n:Agent:6874f6d57a46111b8c140df4"
					// instance-id="ins_AjEscatXrpvh34pAQZxRG"
					// host="https://f45e-190-108-207-91.ngrok-free.app"
					host={loaderData.host}
					agent-id={loaderData.agentId}
					agent-name={selectedAgentInfo?.name}
					theme={JSON.stringify({
						"--ts-chat-bg": "white",
						"--ts-chat-fg": "black",
						"--ts-chat-popup-bg": "white",
						"--ts-icon-btn-bg": "transparent",
						"--ts-icon-btn-hover-bg": "#E4E4E7",
						"--ts-input-btn-color": "black",
						"--ts-input-bg": "#dbdbdb42",
						"--ts-input-bd": "#D4D4D8",
						"--ts-chat-bd": "#D4D4D8",
						"--chakra-colors-border": "#D4D4D8",
						"--ts-input-color": "black",
						"--ts-input-placeholder-color": "#000000eb",
						"--ts-response-msg-color": "black",
					})}
					streaming="true"
					with-debug="true"
					layout="standard"
					session-id={loaderData.sessionId || ""}
					// host="https://app.trueselph.com"
					use-local-storage-cache="true"
					style={{ height: "100%" }}
				></ts-messenger>
			</Card>
		</Box>
	);
}
