import { Badge, Card, Group, Text } from "@mantine/core";
import { Link } from "react-router";
import type { Package } from "~/types";
import classes from "./PackageCard.module.css";
import { IconDownload } from "@tabler/icons-react";
// import { MantineLogo } from "@mantinex/mantine-logo";

export function PackageCard({
	pkg,
	onClick,
}: {
	pkg: Package;
	onClick?: (pkg: Package) => void;
}) {
	return (
		<Card
			withBorder
			padding="lg"
			radius="md"
			// component={Link}
			onClick={onClick ? () => onClick(pkg) : undefined}
			className={classes.root}
			// to={`/actions/${action.id}`}
		>
			<Group justify="space-between">
				{/* <MantineLogo type="mark" size={32} /> */}
				<Badge size="sm" color="gray" variant="outline">
					{pkg.version || "-"}
				</Badge>
				<Badge
					size="sm"
					leftSection={<IconDownload size={14} />}
					variant="filled"
					color="dark"
				>
					{pkg.downloads}
				</Badge>
			</Group>

			<Text fz="md" fw={500} mt="md">
				{pkg.title}
			</Text>
			<Text fz="sm" c="gray.7" mt={5} lineClamp={3}>
				{pkg.description}
			</Text>
		</Card>
	);
}
