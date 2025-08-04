import {
	IconApps,
	IconChartDots3,
	IconDashboard,
	IconLogout,
	IconLogout2,
	IconMessages,
	IconPlus,
	IconSearch,
	IconUser,
} from "@tabler/icons-react";
import {
	ActionIcon,
	Badge,
	Box,
	Code,
	Group,
	Text,
	TextInput,
	Tooltip,
	UnstyledButton,
} from "@mantine/core";
import { UserButton } from "./UserButton";
import classes from "./Navbar.module.css";
import { Link } from "react-router";
import type { Agent } from "~/types";

const links = [
	{ icon: IconDashboard, label: "Dashboard", to: "/dashboard" },
	{ icon: IconMessages, label: "Chat", to: "/chat" },
	{ icon: IconChartDots3, label: "Graph", to: "/graph" },
	{ icon: IconApps, label: "Actions", to: "/actions" },
];

const collections = [
	{ emoji: "", label: "Persona Action" },
	{ emoji: "", label: "Agent Utils" },
	{ emoji: "", label: "DeepDoc Client Action" },
	{ emoji: "", label: "Deepgram Speech-to-Text Action" },
	{ emoji: "", label: "ElevenLabs Text-to-Speech Action" },
	{ emoji: "", label: "Introductory Interact Action" },
	{ emoji: "", label: "LangChain Model Action" },
	{ emoji: "", label: "Persona Interact Action" },
	{ emoji: "", label: "Phoneme Interact Action" },
];

export function Navbar({
	selectedAgentInfo,
	agents,
}: {
	selectedAgentInfo: Agent | null;
	agents: Agent[];
}) {
	const mainLinks = links.map((link) => (
		<UnstyledButton
			key={link.label}
			className={classes.mainLink}
			component={Link}
			to={link.to}
		>
			<div className={classes.mainLinkInner}>
				<link.icon size={20} className={classes.mainLinkIcon} stroke={1.5} />
				<span>{link.label}</span>
			</div>
			{/* {link.notifications && (
				<Badge size="sm" variant="filled" className={classes.mainLinkBadge}>
					{link.notifications}
				</Badge>
			)} */}
		</UnstyledButton>
	));

	const collectionLinks = collections.map((collection) => (
		<a
			href="#"
			onClick={(event) => event.preventDefault()}
			key={collection.label}
			className={classes.collectionLink}
		>
			<Box component="span" mr={9} fz={16}>
				{collection.emoji}
			</Box>{" "}
			{collection.label}
		</a>
	));

	return (
		<nav className={classes.navbar}>
			<div className={classes.section}>
				<UserButton
					selectedAgentInfo={selectedAgentInfo || null}
					agents={agents}
				/>
			</div>

			<div className={classes.section} style={{ borderBottom: "none" }}>
				<div className={classes.mainLinks}>{mainLinks}</div>
			</div>

			<div className={classes.section} style={{ flex: 1 }}>
				{/* <Group className={classes.collectionsHeader} justify="space-between">
					<Text size="xs" fw={500} c="dimmed">
						Actions
					</Text>

					<Tooltip label="Add Action" withArrow position="right">
						<ActionIcon variant="default" size={18}>
							<IconPlus size={12} stroke={1.5} />
						</ActionIcon>
					</Tooltip>
				</Group> */}

				{/* <Box px="sm" my="sm">
					<TextInput
						placeholder="Search"
						size="xs"
						leftSection={<IconSearch size={12} stroke={1.5} />}
						rightSectionWidth={70}
						rightSection={<Code className={classes.searchCode}>Ctrl + K</Code>}
						styles={{ section: { pointerEvents: "none" } }}
						mb="sm"
					/>
				</Box> */}

				{/* <div className={classes.collections}>{collectionLinks}</div> */}
			</div>

			<div
				className={classes.section}
				style={{ marginBottom: 0, paddingBottom: 0 }}
			>
				<div
					className={classes.mainLinks}
					style={{ marginBottom: 0, paddingBottom: 0 }}
				>
					<UnstyledButton
						className={classes.mainLink}
						component={Link}
						to={"/logout"}
					>
						<div className={classes.mainLinkInner}>
							<IconLogout2
								size={20}
								className={classes.mainLinkIcon}
								stroke={1.5}
							/>
							<span>Logout</span>
						</div>
					</UnstyledButton>
				</div>
			</div>
		</nav>
	);
}
