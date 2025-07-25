import {
	Box,
	Button,
	Center,
	Paper,
	PasswordInput,
	Stack,
	Text,
	TextInput,
	Title,
} from "@mantine/core";
import classes from "./login.module.css";
import { isEmail, isNotEmpty, matches, useForm } from "@mantine/form";
import { useFetcher } from "react-router";
import type { Route } from "./+types/login";
import { redirect } from "react-router";
import { useEffect } from "react";

export function meta() {
	return [
		{
			title: "Login",
			description: "Login to JIVAS Manager",
		},
	];
}

const connectionMsg = "Unable to connect to server";

export async function clientAction({ request }: Route.ClientActionArgs) {
	const formData = await request.formData();
	const email = formData.get("email");
	const host = formData.get("host");
	const password = formData.get("password");

	if (!email || !host || !password) {
		return redirect("/login");
	}

	try {
		const result = await fetch(`${host}/user/login`, {
			method: "POST",
			body: JSON.stringify({ email, host, password }),
			headers: {
				"Content-Type": "application/json",
			},
		}).then(
			(res) =>
				res.json() as Promise<{
					token: string;
					user: {
						email: string;
						expiration: number;
						id: string;
						is_activated: boolean;
						root_id: string;
					};
				}>,
		);

		if (result.token) {
			localStorage.setItem("jivas-host", host as string);
			localStorage.setItem("jivas-token", result.token);
			localStorage.setItem("jivas-root-id", result.user.root_id);

			return redirect("/dashboard");
		}

		return { ...result, t: new Date().toISOString() };
	} catch (err) {
		console.log(err);
		return {
			message: connectionMsg,
			t: new Date().toISOString(),
		};
	}
}

export default function Login() {
	const loginFetcher = useFetcher();
	const form = useForm({
		mode: "uncontrolled",
		initialValues: {
			email: "",
			host: localStorage.getItem("jivas-host") || "",
			password: "",
		},

		validate: {
			email: isEmail(),
			password: isNotEmpty(),
			host: matches(
				/^https?:\/\/[a-zA-Z0-9.-]+(:\d+)?$/,
				// /^https?:\/\/[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/,
				"Please enter a valid host e.g http://localhost:8000",
			),
		},
	});

	useEffect(() => {
		if (
			loginFetcher.data?.message &&
			loginFetcher.data.message !== connectionMsg
		) {
			form.setFieldError("email", loginFetcher.data.message);
			form.setFieldError("password", loginFetcher.data.message);
		}

		if (loginFetcher.data?.message === connectionMsg) {
			form.clearErrors();
			form.setFieldError("host", loginFetcher.data.message);
		}
	}, [loginFetcher.data]);

	return (
		<form
			onSubmit={form.onSubmit((values) =>
				loginFetcher.submit({ ...values }, { method: "POST" }),
			)}
		>
			<Center h="100vh" w="100vw">
				<Stack w={420} gap="xs" mx="xs">
					<Box>
						<Title ta="center" className={classes.title}>
							JIVAS Manager
						</Title>

						<Text className={classes.subtitle}>
							Connect to your JIVAS instance
						</Text>
					</Box>
					<Paper withBorder p={22} mt={16} radius="md">
						<Stack>
							<TextInput
								label="Host"
								placeholder="http://localhost:8000"
								type="url"
								required
								radius="md"
								key={form.key("host")}
								{...form.getInputProps("host")}
							/>

							<TextInput
								label="Email"
								placeholder="you@mantine.dev"
								type="email"
								required
								radius="md"
								key={form.key("email")}
								{...form.getInputProps("email")}
							/>

							<PasswordInput
								label="Password"
								placeholder="Your password"
								required
								radius="md"
								key={form.key("password")}
								{...form.getInputProps("password")}
							/>
						</Stack>

						<Button
							loading={loginFetcher.state !== "idle"}
							color="teal"
							type="submit"
							fullWidth
							mt="xl"
							radius="md"
						>
							Connect
						</Button>
					</Paper>
				</Stack>
			</Center>
		</form>
	);
}
