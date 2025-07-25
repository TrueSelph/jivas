import type { Action } from "~/types";
import type { Route } from "./+types/action-details";
import { ActionIcon, Box, Divider, Group, Title } from "@mantine/core";
import { IconArrowLeft } from "@tabler/icons-react";
import { Link } from "react-router";

export async function clientAction({ request }: Route.ClientLoaderArgs) {
	const data = await request.formData();
	const agentId = data.get("agentId") as string;

	localStorage.setItem("jivas-agent", agentId);

	return {
		// agents: result?.reports,
	};
}

function escapeForJS(code: string): string {
	return code
		.replace(/\\/g, "\\\\") // escape backslashes
		.replace(/`/g, "\\`") // escape backticks
		.replace(/\${/g, "\\${"); // escape JS template variables
}

export async function clientLoader({
	serverLoader,
	params,
}: Route.ClientLoaderArgs) {
	const host = localStorage.getItem("jivas-host");
	const rootId = localStorage.getItem("jivas-root-id");
	const token = localStorage.getItem("jivas-token");
	const tokenExp = localStorage.getItem("jivas-token-exp");
	const agentId = localStorage.getItem("jivas-agent");

	const action = (await fetch(`${host}/walker/get_action`, {
		method: "POST",
		body: JSON.stringify({
			agent_id: agentId,
			action_id: params.actionId,
			reporting: true,
		}),
		headers: {
			"Content-Type": "application/json",
			Authorization: `Bearer ${token}`,
		},
	}).then((res) => res.json())) as { reports: Action[] };

	const code = await fetch(`${host}/walker/get_action_app`, {
		method: "POST",
		body: JSON.stringify({
			agent_id: agentId,
			action: action.reports[0].label,
			reporting: true,
		}),
		headers: {
			"Content-Type": "application/json",
			Authorization: `Bearer ${token}`,
		},
	})
		.then((res) => res.json())
		.then((res) => res.reports?.[0] || "");

	const files = {
		"streamlit_app.py": `
import os
import streamlit as st
import json
from streamlit_router import StreamlitRouter

${escapeForJS(code.replaceAll("jvcli.client", "jvclient").replaceAll("`", "'"))}


root_id = "${rootId || ""}"
print("ROOT ID:", root_id)
st.session_state.ROOT_ID = root_id or "000000000000000000000000"
st.session_state.TOKEN = "${token}"
st.session_state.EXPIRATION = ${tokenExp || 253387602857692}


if __name__ == "__main__":
    router = StreamlitRouter()
    os.environ["JIVAS_BASE_URL"] = "${host || "http://localhost:8000"}";


    agent_id = "${agentId}"
    action_id = "${params.actionId}"

    info = json.loads('${JSON.stringify(action.reports[0]["_package"])}')

    render(router, agent_id, action_id, info)
    `,
	};
	const body = `
  <!DOCTYPE html>
  <html>
  <head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <title>Serverless Image Processing App</title>
    <meta name="description" content="A Serverless Streamlit application with OpenCV image processing that completely works on your browser">
      <link
        rel="stylesheet"
        href="https://cdn.jsdelivr.net/npm/@stlite/browser@0.83.0/build/stlite.css"
      />
  </head>
  <body>
    <div id="root"></div>
    <script type="module">
    	import { mount } from "https://cdn.jsdelivr.net/npm/@stlite/browser@0.83.0/build/stlite.js";
      mount({
        requirements: [
                  "PyYAML",
                  "requests",
                  "https://pub-62dafe7bf3a84354ad20209ffaed5137.r2.dev/streamlit_router-0.1.8-py3-none-any.whl",
                  "jvclient",
                  "matplotlib",
                  "opencv-python",
                ],
        entrypoint: "streamlit_app.py",
        files: {
          "streamlit_app.py": \`${files["streamlit_app.py"]}\`,
        },
      },
      document.getElementById("root"))
    </script>
  </body>
  </html>
				`;

	// const result = (await fetch(`${host}/walker/list_actions`, {
	// 	method: "POST",
	// 	body: JSON.stringify({ agent_id: localStorage.getItem("jivas-agent") }),
	// 	headers: {
	// 		"Content-Type": "application/json",
	// 		Authorization: `Bearer ${token}`,
	// 	},
	// }).then((res) => res.json())) as { reports: [Action[]] };

	return {
		// loginResult,
		code: body,
	};
}

export default function ChatRoute({ loaderData }: Route.ComponentProps) {
	return (
		<Box px="xl" py="xl">
			<Group>
				<ActionIcon color="dark" size="sm" component={Link} to="./..">
					<IconArrowLeft />
				</ActionIcon>
				<Title order={3}>Manage Action</Title>
			</Group>
			<Divider mt="xs" mb="xl" />

			<Box px="xl" py="xl" h="90vh">
				<iframe
					style={{
						outline: "none",
						border: "none",
					}}
					title={"Action Config"}
					width={"100%"}
					height={"100%"}
					srcDoc={loaderData.code}
				/>
			</Box>
		</Box>
	);
}
