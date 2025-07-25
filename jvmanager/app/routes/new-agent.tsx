import {
	Box,
	Button,
	Card,
	Divider,
	Text,
	Group,
	Input,
	Paper,
	SimpleGrid,
	Title,
	Table,
	Badge,
	Loader,
	PasswordInput,
	Stack,
} from "@mantine/core";
import {
	IconArrowLeft,
	IconPlus,
	IconSearch,
	IconSettings,
} from "@tabler/icons-react";
import type { Route } from "./+types/new-agent";
import type { Agent, ApiResponse, Package } from "~/types";
import { JIVAS_PACKAGES_ENDPOINT } from "consts";
import { PackageCard } from "~/components/PackageCard";
import { useState } from "react";
import dayjs from "dayjs";
import {
	data,
	redirect,
	useFetcher,
	useLocation,
	useNavigation,
	useSearchParams,
} from "react-router";
import type { R } from "node_modules/react-router/dist/development/route-data-D7Xbr_Ww.mjs";
import { useDebouncedCallback } from "@mantine/hooks";
import { modals } from "@mantine/modals";

export function meta() {
	return [{ title: "New Agent | JIVAS Manager" }];
}

export async function clientLoader({ request }: Route.ClientLoaderArgs) {
	const url = new URL(request.url);
	const limit = url.searchParams.get("limit") || "10";
	const offset = url.searchParams.get("offset") || "0";
	const search = url.searchParams.get("search") || "";
	const packageType = url.searchParams.get("type") || "agent";

	const apiKey = localStorage.getItem("jpr-key") || null;

	const requestUrl = new URL(`${JIVAS_PACKAGES_ENDPOINT}/packages/search`);

	// requestUrl.searchParams.set("query", "");
	requestUrl.searchParams.set("limit", limit);
	requestUrl.searchParams.set("offset", offset);
	requestUrl.searchParams.set("q", search);
	console.log({ packageType, search });
	requestUrl.searchParams.set("type", packageType === "all" ? "" : packageType);

	const headers = apiKey ? { "x-api-key": apiKey } : undefined;
	console.log({ headers });

	const result = (await fetch(requestUrl.toString(), {
		method: "GET",
		headers: { ...headers, "Content-Type": "application/json" },
	}).then((res) => res.json())) as { total: number; packages: Package[] };

	return {
		packages: result.packages,
		totalPackages: result.total,
		apiKey: apiKey || "",
	};
}

export async function clientAction({ request }: Route.ClientActionArgs) {
	const host = localStorage.getItem("jivas-host");
	const token = localStorage.getItem("jivas-token");

	const apiKey = localStorage.getItem("jpr-key");

	const formData = await request.formData();

	const _action = formData.get("_action");

	if (_action === "createAgentFromDaf") {
		const dafVersion = formData.get("version");
		const packageName = formData.get("package");

		const res = (await fetch(`${host}/walker/import_agent`, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				Authorization: `Bearer ${token}`,
			},
			body: JSON.stringify({
				reporting: true,
				daf_name: packageName,
				daf_version: dafVersion || "latest",
				jpr_api_key: apiKey || undefined,
				// descriptor: agentData
				// 	? typeof agentData === "object"
				// 		? JSON.stringify(agentData)
				// 		: agentData
				// 	: undefined,
			}),
		}).then(async (res) => await res.json())) as ApiResponse<Agent>;
		const agent = res.reports?.[0];

		if (agent) {
			localStorage.setItem("jivas-agent", agent.id);
			return redirect("/dashboard");
		}

		return res.reports;
	}

	if (_action === "updateJPRApiKey") {
		const apiKey = formData.get("apiKey") as string;

		localStorage.setItem("jpr-key", apiKey || "");

		return {};
	}
}

export default function NewAgent({ loaderData }: Route.ComponentProps) {
	const host = localStorage.getItem("jivas-host");
	const token = localStorage.getItem("jivas-token");

	const [selected, setSelected] = useState<Package | null>(null);
	const [selectedVersion, setSelectedVersion] = useState(new Set<string>([]));
	const [searchParams, setSearchParams] = useSearchParams();

	const createPackageFetcher = useFetcher();

	const handleSearch = useDebouncedCallback(async (search) => {
		searchParams.set("search", search);
		setSearchParams(searchParams);
	}, 500);

	const navigation = useNavigation();

	const location = useLocation();

	return (
		<Box py="xl" px="xl">
			<Group justify="space-between">
				<Title order={3}>New Agent</Title>
			</Group>

			<Divider mt="xs" mb="xl" />

			<Card h="80vh" px="xs" withBorder>
				<Paper p="md" radius="md" h="100%">
					<Title order={3}>Browse Agents</Title>

					{selected ? (
						<Box mt="xl">
							<Group>
								<Button
									onClick={() => setSelected(null)}
									size="xs"
									leftSection={<IconArrowLeft size={16} />}
									color="dark"
								>
									Back
								</Button>
								<Title order={4}>{selected.title}</Title>
							</Group>

							<SimpleGrid mt="lg" cols={{ base: 1, md: 2 }}>
								<Box>
									<Title order={6}>Description</Title>
									<Text size="sm" c="gray.7">
										{selected.description}
									</Text>
								</Box>

								<Box>
									<Table variant="vertical" layout="fixed" withTableBorder>
										<Table.Tbody>
											<Table.Tr>
												<Table.Th w={160}>Package</Table.Th>
												<Table.Td>{selected.package}</Table.Td>
											</Table.Tr>

											<Table.Tr>
												<Table.Th>Version</Table.Th>
												<Table.Td>{selected.version}</Table.Td>
											</Table.Tr>

											<Table.Tr>
												<Table.Th>Category</Table.Th>
												<Table.Td>
													<Badge color="dark">{selected.type}</Badge>
												</Table.Td>
											</Table.Tr>

											<Table.Tr>
												<Table.Th>Downloads</Table.Th>
												<Table.Td>{selected.downloads}</Table.Td>
											</Table.Tr>

											<Table.Tr>
												<Table.Th>Last Published</Table.Th>
												<Table.Td>
													{dayjs(selected.publishedAt).format(
														"MMMM D, YYYY h:mm:ss A",
													)}
												</Table.Td>
											</Table.Tr>
										</Table.Tbody>
									</Table>

									<Group justify="end" mt="lg">
										<Button
											onClick={() =>
												createPackageFetcher.submit(
													{
														_action: "createAgentFromDaf",
														package: selected.package,
														version: selected.version,
													},
													{ method: "POST" },
												)
											}
											leftSection={<IconPlus size={16} />}
											loading={createPackageFetcher.state !== "idle"}
											color="dark"
										>
											Create Agent
										</Button>
									</Group>
								</Box>
							</SimpleGrid>
						</Box>
					) : (
						<>
							<Group my="lg">
								<Input
									placeholder="Search Agent"
									w={400}
									rightSection={
										navigation.state === "loading" &&
										navigation.location.pathname == location.pathname ? (
											<Loader size="xs" />
										) : null
									}
									onChange={(e) => {
										handleSearch(e.target.value);
									}}
									leftSection={<IconSearch size={16} />}
								/>
								<Button
									size="sm"
									color="dark"
									onClick={() =>
										modals.open({
											title: "JPR Configuration",
											children: <JPRConfig apiKeyInit={loaderData.apiKey} />,
										})
									}
									leftSection={<IconSettings size={16} />}
								>
									Configure
								</Button>
							</Group>

							<SimpleGrid cols={{ base: 1, md: 2, lg: 4 }}>
								{loaderData.packages?.map((pkg) => (
									<PackageCard onClick={setSelected} key={pkg.id} pkg={pkg} />
								))}
							</SimpleGrid>
						</>
					)}
				</Paper>
			</Card>
		</Box>
	);
}

function JPRConfig({ apiKeyInit }: { apiKeyInit: string | null }) {
	const [apiKey, setApiKey] = useState<string | null>(apiKeyInit);
	const updateJPRAPIKeyFetcher = useFetcher();

	return (
		<Stack>
			<PasswordInput
				label="API Key"
				placeholder="API Key"
				value={apiKey || ""}
				onChange={(e) => setApiKey(e.target.value)}
			/>
			<Button
				size="sm"
				color="dark"
				mt="sm"
				loading={updateJPRAPIKeyFetcher.state !== "idle"}
				onClick={() => {
					updateJPRAPIKeyFetcher.submit(
						{ apiKey: apiKey, _action: "updateJPRApiKey" },
						{ method: "POST", action: "/new-agent" },
					);
					modals.closeAll();
				}}
			>
				Save
			</Button>
		</Stack>
	);
}
