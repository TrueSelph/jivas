import { Badge, Card, Group, Text } from "@mantine/core";
import { Link } from "react-router";
import type { Action } from "~/types";
import classes from "./ActionCard.module.css";
// import { MantineLogo } from "@mantinex/mantine-logo";

export function ActionCard({ action }: { action: Action }) {
	return (
		<Card
			withBorder
			padding="lg"
			radius="md"
			component={Link}
			className={classes.root}
			to={`/actions/${action.id}`}
		>
			<Group justify="space-between">
				{/* <MantineLogo type="mark" size={32} /> */}
				<Badge size="sm" color="gray" variant="outline">
					{action._package?.version || "-"}
				</Badge>
				{action.enabled ? (
					<Badge size="sm" variant="dot" color="teal">
						Enabled
					</Badge>
				) : (
					<Badge size="sm" color="red" variant="dot">
						Disabled
					</Badge>
				)}
			</Group>

			<Text fz="md" fw={500} mt="md">
				{action._package?.meta?.title || action.label}
			</Text>
			<Text fz="sm" c="gray.7" mt={5} lineClamp={3}>
				{action.description}
			</Text>

			{/* <Group justify="space-between" mt="md"> */}
			{/* <Avatar.Group spacing="sm"> */}
			{/* <Avatar src={avatars[0]} radius="xl" /> */}
			{/* <Avatar src={avatars[1]} radius="xl" /> */}
			{/* <Avatar src={avatars[2]} radius="xl" /> */}
			{/* <Avatar radius="xl">+5</Avatar> */}
			{/* </Avatar.Group> */}
			{/* <ActionIcon variant="default" size="lg" radius="md"> */}
			{/* <IconUpload size={18} /> */}
			{/* </ActionIcon> */}
			{/* </Group> */}
		</Card>
	);
}
