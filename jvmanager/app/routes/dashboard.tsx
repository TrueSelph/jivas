import {
	Paper,
	SimpleGrid,
	Text,
	Box,
	Divider,
	Group,
	Title,
	Card,
	Button,
	Table,
	rem,
} from "@mantine/core";
import { DatePickerInput } from "@mantine/dates";
import type { Route } from "./+types/dashboard";
import type { Agent } from "~/types";
import {
	useFetcher,
	useLocation,
	useNavigate,
	useOutletContext,
	useSearchParams,
} from "react-router";
import { useCallback, useState } from "react";
import {
	IconArrowDownRight,
	IconArrowUpRight,
	IconCalendar,
	IconChartFunnel,
	IconMessage,
	IconNotes,
	IconReceipt2,
	IconUserPlus,
} from "@tabler/icons-react";
import classes from "./StatsGrid.module.css";
import { LineChart, Sparkline } from "@mantine/charts";
import {
	getChannelsByDate,
	getInstanceToken,
	getInteractionsByDate,
	getUsersByDate,
} from "~/lib/analytics";
import dayjs from "dayjs";
import utc from "dayjs/plugin/utc";
import timezone from "dayjs/plugin/timezone";
import { modals } from "@mantine/modals";

dayjs.extend(utc);
dayjs.extend(timezone);

export async function clientLoader({ request }: Route.ClientActionArgs) {
	const agentId = localStorage.getItem("jivas-agent") || "";
	const userTimeZone = dayjs.tz.guess();
	const { instance, tokenResult } = getInstanceToken();

	const defaultDateRange = [
		dayjs().subtract(30, "days").toISOString(),
		dayjs().toISOString(),
	] as [string, string];

	const url = new URL(request.url);

	let startDate = url.searchParams.get("startDate") || defaultDateRange[0];
	let endDate = url.searchParams.get("endDate") || defaultDateRange[1];

	if (!dayjs(startDate).isValid()) {
		startDate = defaultDateRange[0];
	}

	if (!dayjs(endDate).isValid()) {
		endDate = defaultDateRange[1];
	}

	startDate = dayjs(startDate).format("YYYY-MM-DD");
	endDate = dayjs(endDate).format("YYYY-MM-DD");

	const usersByDate = await getUsersByDate({
		agentId,
		startDate,
		endDate,
		timezone: userTimeZone,
	});

	const interactionsByDate = await getInteractionsByDate({
		agentId,
		startDate,
		endDate,
		timezone: userTimeZone,
	});

	const channelsByDate = await getChannelsByDate({
		agentId,
		startDate,
		endDate,
		timezone: userTimeZone,
	});

	const logs = await fetch(`${instance.url}/walker/get_interaction_logs`, {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
			Authorization: `Bearer ${tokenResult.token}`,
		},
		body: JSON.stringify({
			agent_id: agentId,
			reporting: true,
			start_date: startDate,
			end_date: endDate,
			timezone: userTimeZone,
		}),
	})
		.then(async (res) => await res.json())
		.then((res) => res.reports?.[0]);

	return {
		defaultDateRange: [startDate, endDate],
		usersByDate,
		interactionsByDate,
		channelsByDate,
		logs,
	};
}

export function meta() {
	return [{ title: "Dashboard | JIVAS Manager" }];
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

export default function ChatRoute({ loaderData }: Route.ComponentProps) {
	const { selectedAgentInfo } = useOutletContext<{
		selectedAgentInfo: Agent & { thumbnail: string };
	}>();

	const navigate = useNavigate();
	const location = useLocation();

	if (!selectedAgentInfo) {
		if (!location.pathname.includes("new-agent")) {
			return navigate("/new-agent");
		}
	}

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

	const [value, setValue] = useState<[string | null, string | null]>(
		loaderData.defaultDateRange,
	);

	const [searchParams, setSearchParams] = useSearchParams();

	return (
		<Box py="xl" px="xl">
			{/* {JSON.stringify(loaderData.logs)} */}
			<Group justify="space-between">
				<Title order={3}>Dashboard</Title>
			</Group>

			<Divider mt="xs" mb="xl" />

			<Group justify="end" mb="sm">
				<DatePickerInput
					type="range"
					w={300}
					leftSection={<IconCalendar size={16} />}
					label="Date Range"
					placeholder="Pick dates range"
					value={value}
					presets={[
						{
							value: [
								dayjs().subtract(1, "day").format("YYYY-MM-DD"),
								dayjs().format("YYYY-MM-DD"),
							],
							label: "Past Day",
						},
						{
							value: [
								dayjs().subtract(7, "day").format("YYYY-MM-DD"),
								dayjs().format("YYYY-MM-DD"),
							],
							label: "Past 7 Days",
						},
						{
							value: [
								dayjs().subtract(14, "day").format("YYYY-MM-DD"),
								dayjs().format("YYYY-MM-DD"),
							],
							label: "Past 14 Days",
						},
						{
							value: [
								dayjs().subtract(1, "month").format("YYYY-MM-DD"),
								dayjs().format("YYYY-MM-DD"),
							],
							label: "Past Month",
						},
						{
							value: [
								dayjs().subtract(3, "month").format("YYYY-MM-DD"),
								dayjs().format("YYYY-MM-DD"),
							],
							label: "Past 3 Months",
						},
						{
							value: [
								dayjs().subtract(6, "month").format("YYYY-MM-DD"),
								dayjs().format("YYYY-MM-DD"),
							],
							label: "Past 6 Months",
						},
						{
							value: [
								dayjs().subtract(1, "year").format("YYYY-MM-DD"),
								dayjs().format("YYYY-MM-DD"),
							],
							label: "Past Year",
						},
						// { value: dayjs().format("YYYY-MM-DD"), label: "Today" },
						// {
						// 	value: dayjs().add(1, "day").format("YYYY-MM-DD"),
						// 	label: "Tomorrow",
						// },
						// {
						// 	value: dayjs().add(1, "month").format("YYYY-MM-DD"),
						// 	label: "Next month",
						// },
						// {
						// 	value: dayjs().add(1, "year").format("YYYY-MM-DD"),
						// 	label: "Next year",
						// },
						// {
						// 	value: dayjs().subtract(1, "month").format("YYYY-MM-DD"),
						// 	label: "Last month",
						// },
						// {
						// 	value: dayjs().subtract(1, "year").format("YYYY-MM-DD"),
						// 	label: "Last year",
						// },
					]}
					onChange={(v) => {
						const startDate = dayjs(v[0]).format("YYYY-MM-DD");
						const endDate = dayjs(v[1]).format("YYYY-MM-DD");

						searchParams.set("startDate", startDate);
						searchParams.set("endDate", endDate);

						setSearchParams(searchParams);

						setValue(v);
					}}
				/>
			</Group>

			<StatsGrid
				analytics={{
					interactionsByDate: loaderData.interactionsByDate,
					usersByDate: loaderData.usersByDate,
					channelsByDate: loaderData.channelsByDate,
				}}
			/>

			<Box mt="xl">
				<Group justify="end" mb="sm">
					<Button
						leftSection={
							<IconNotes style={{ width: rem(16), height: rem(16) }} />
						}
						color="dark"
						onClick={() => {
							modals.open({
								size: "90vw",
								title: "Logs",
								children: (
									<Box>
										<Table.ScrollContainer
											minWidth={500}
											maxHeight={"80vh"}
											// type="native"
										>
											<Table striped highlightOnHover stickyHeader>
												<Table.Thead>
													<Table.Tr>
														<Table.Th>Time</Table.Th>
														<Table.Th>Input</Table.Th>
														<Table.Th>Message</Table.Th>
														<Table.Th>Channel</Table.Th>
														<Table.Th>Session ID</Table.Th>
													</Table.Tr>
												</Table.Thead>

												<Table.Tbody>
													{loaderData.logs.data?.map((log) => (
														<Table.Tr key={log.id}>
															<Table.Td width={"180px"}>
																{dayjs(log.time_stamp).format(
																	"YYYY-MM-DD HH:mm",
																)}
															</Table.Td>
															<Table.Td width={"280px"}>
																{log.utterance}
															</Table.Td>
															<Table.Td>
																{typeof log?.response?.message?.content ===
																"string"
																	? log?.response?.message?.content
																	: JSON.stringify(
																			log?.response?.message?.content,
																		)}
															</Table.Td>
															<Table.Td>{log.channel}</Table.Td>
															<Table.Td width={"180px"}>
																{log.response.session_id}
															</Table.Td>
														</Table.Tr>
													))}
												</Table.Tbody>
											</Table>
										</Table.ScrollContainer>
									</Box>
								),
							});
						}}
					>
						View Logs
					</Button>
				</Group>

				<InteractionsChart
					analytics={{
						interactionsByDate: loaderData.interactionsByDate,
						usersByDate: loaderData.usersByDate,
						channelsByDate: loaderData.channelsByDate,
					}}
				/>
			</Box>
		</Box>
	);
}

const icons = {
	user: IconUserPlus,
	interaction: IconMessage,
	receipt: IconReceipt2,
	channel: IconChartFunnel,
};

export function StatsGrid({
	analytics,
}: {
	analytics: {
		interactionsByDate: Route.ComponentProps["loaderData"]["interactionsByDate"];
		usersByDate: Route.ComponentProps["loaderData"]["usersByDate"];
		channelsByDate: Route.ComponentProps["loaderData"]["channelsByDate"];
	};
}) {
	const data = [
		{
			title: "Total Interactions",
			icon: "interaction",
			value: analytics.interactionsByDate.total || 0,
			points:
				analytics.interactionsByDate.data?.map((point) => point.count) || [],
		},
		{
			title: "Unique Users",
			icon: "user",
			value: analytics.usersByDate.total || 0,
			points: analytics.usersByDate.data?.map((point) => point.count) || [],
		},
		{
			title: "Unique Channels",
			icon: "channel",
			value: analytics.channelsByDate.total || 0,
			points: analytics.channelsByDate.data?.map((point) => point.count) || [],
		},
	] as const;

	const stats = data?.map((stat) => {
		const Icon = icons[stat.icon];
		const DiffIcon = stat.diff > 0 ? IconArrowUpRight : IconArrowDownRight;

		return (
			<Paper withBorder p="md" radius="md" key={stat.title}>
				<Group align="flex-end" gap="xs" mt={"xs"} justify="space-between">
					<Text className={classes.value}>{stat.value}</Text>
					<Icon className={classes.icon} size={22} stroke={1.5} />
					{/* <Text
						c={stat.diff > 0 ? "teal" : "red"}
						fz="sm"
						fw={500}
						className={classes.diff}
					>
						<span>{stat.diff}%</span>
						<DiffIcon size={16} stroke={1.5} />
					</Text> */}
				</Group>

				<Group justify="space-between" mt={4}>
					<Text size="xs" c="dimmed" className={classes.title}>
						{stat.title}
					</Text>
				</Group>

				<Sparkline
					w={"100%"}
					h={60}
					data={stat.points}
					curveType="bump"
					color="dark.2"
					fillOpacity={0.2}
					strokeWidth={2}
				/>
			</Paper>
		);
	});
	return (
		<div className={classes.root}>
			<SimpleGrid cols={{ base: 1, xs: 2, md: 3 }}>{stats}</SimpleGrid>
		</div>
	);
}

// const barData = [
// 	{
// 		date: "Mar 22",
// 		Apples: 2890,
// 		Oranges: 2338,
// 		Tomatoes: 2452,
// 	},
// 	{
// 		date: "Mar 23",
// 		Apples: 2756,
// 		Oranges: 2103,
// 		Tomatoes: 2402,
// 	},
// 	{
// 		date: "Mar 24",
// 		Apples: 3322,
// 		Oranges: 986,
// 		Tomatoes: 1821,
// 	},
// 	{
// 		date: "Mar 25",
// 		Apples: 3470,
// 		Oranges: 2108,
// 		Tomatoes: 2809,
// 	},
// 	{
// 		date: "Mar 26",
// 		Apples: 3129,
// 		Oranges: 1726,
// 		Tomatoes: 2290,
// 	},
// ];

function InteractionsChart({
	analytics,
}: {
	analytics: {
		interactionsByDate: Route.ComponentProps["loaderData"]["interactionsByDate"];
		usersByDate: Route.ComponentProps["loaderData"]["usersByDate"];
		channelsByDate: Route.ComponentProps["loaderData"]["channelsByDate"];
	};
}) {
	const data: {
		date: string;
		Interactions?: number;
		Users?: number;
		Channels?: number;
	}[] = [];

	analytics.interactionsByDate.data?.forEach((item) => {
		const datePoint = data.find((i) => item.date === i.date);

		if (!datePoint) {
			data.push({
				date: item.date,
				Interactions: item.count,
			});
		} else {
			datePoint.Interactions = item.interactions;
		}
	});

	analytics.usersByDate.data?.forEach((item) => {
		const datePoint = data.find((i) => item.date === i.date);

		if (!datePoint) {
			data.push({
				date: item.date,
				Users: item.count,
			});
		} else {
			datePoint.Users = item.count;
		}
	});

	analytics.channelsByDate.data?.forEach((item) => {
		const datePoint = data.find((i) => item.date === i.date);

		if (!datePoint) {
			data.push({
				date: item.date,
				Channels: item.count,
			});
		} else {
			datePoint.Channels = item.count;
		}
	});

	return (
		<Card withBorder>
			<Title mb="xl" order={5}>
				Interactions
			</Title>
			<LineChart
				h={300}
				data={
					data?.map((item) => ({
						...item,
						date: dayjs(item.date).format("DD MMM"),
					})) || []
				}
				dataKey="date"
				withDots
				withLegend
				curveType="natural"
				series={[
					{ name: "Interactions", color: "indigo.6" },
					{ name: "Users", color: "gray.6" },
					{ name: "Channels", color: "teal.6" },
				]}
				// curveType="linear"
			/>
		</Card>
	);
}
