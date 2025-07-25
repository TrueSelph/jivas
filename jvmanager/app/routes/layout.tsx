import type { Route } from "./+types/layout";
import { AppShell, Box } from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import { NavigationProgress } from "@mantine/nprogress";
import { Outlet, redirect, useLocation, useNavigate } from "react-router";
import { Navbar } from "~/components/Navbar";
import type { Agent } from "~/types";

export function meta({}: Route.MetaArgs) {
	return [
		{ title: "New React Router App" },
		{ name: "description", content: "Welcome to React Router!" },
	];
}

export async function clientLoader({ request }: Route.ClientLoaderArgs) {
	const host = localStorage.getItem("jivas-host");
	const token = localStorage.getItem("jivas-token");
	const selectedAgent = localStorage.getItem("jivas-agent");

	const selectedAgentInfo = selectedAgent
		? ((await fetch(`${host}/walker/get_agent`, {
				method: "POST",
				body: JSON.stringify({ agent_id: selectedAgent }),
				headers: {
					"Content-Type": "application/json",
					Authorization: `Bearer ${token}`,
				},
			}).then((res) => res.json())) as { reports: Agent[] })
		: null;

	const formData = new FormData();
	formData.append("args", `{"base64_prefix": false}`);
	formData.append("module_root", "actions.jivas.avatar_action");
	formData.append("agent_id", selectedAgentInfo?.reports?.[0]?.id || "");
	formData.append("walker", "get_avatar");

	const avatar = (await fetch(`${host}/action/walker`, {
		method: "POST",
		headers: {
			Authorization: `Bearer ${token}`,
		},
		body: formData,
	})
		.then(async (res) => await res.json())
		.catch(() => null)) as [string, string] | null;

	const result = (await fetch(`${host}/walker/list_agents`, {
		method: "POST",
		body: JSON.stringify({}),
		headers: {
			"Content-Type": "application/json",
			Authorization: `Bearer ${token}`,
		},
	})
		.then((res) => res.json())
		.catch(() => {
			return { reports: [] };
		})) as { reports: Agent[] };

	if (!result?.reports?.length) {
		if (!request.url.includes("/new-agent")) {
			return redirect("/new-agent");
		}
	}

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

export default function Layout({ loaderData }: Route.ComponentProps) {
	const [opened, { toggle }] = useDisclosure();

	return (
		<>
			<NavigationProgress />
			<AppShell
				// header={{ height: 60 }}
				navbar={{
					width: 300,
					breakpoint: "sm",
					collapsed: { mobile: !opened },
				}}
				padding="0"
			>
				{/* <appshell.header>
					<burger opened={opened} onclick={toggle} hiddenfrom="sm" size="sm" />
				</appshell.header> */}

				<AppShell.Navbar>
					<Navbar
						selectedAgentInfo={loaderData.selectedAgentInfo || null}
						agents={loaderData.agents}
					/>
				</AppShell.Navbar>

				<AppShell.Main>
					<Box px="lg">
						<OutletWrapper agents={loaderData.agents}>
							<Outlet
								context={{ selectedAgentInfo: loaderData.selectedAgentInfo }}
							/>
						</OutletWrapper>
					</Box>
				</AppShell.Main>
			</AppShell>
		</>
	);
}

export function OutletWrapper({
	children,
	agents,
}: {
	children: React.ReactNode;
	agents: Agent[];
}) {
	const location = useLocation();
	const navigate = useNavigate();

	if (location.pathname !== "/new-agent" && !agents?.length) {
		navigate("/new-agent");
		return null;
	}

	return <Box px="lg">{children}</Box>;
}
