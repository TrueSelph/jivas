import {
	type RouteConfig,
	layout,
	route,
	index,
} from "@react-router/dev/routes";

export default [
	route("/", "routes/home.tsx"),
	route("/login", "routes/login.tsx"),
	route("/logout", "routes/logout.tsx"),
	route("/graph", "routes/graph.tsx"),
	layout("routes/layout.tsx", [
		route("/chat", "routes/chat.tsx"),
		route("/dashboard", "routes/dashboard.tsx"),
		route("/actions", "routes/actions.tsx"),
		route("/actions/:actionId", "routes/action-details.tsx"),
		route("/new-agent", "routes/new-agent.tsx"),
	]),
] satisfies RouteConfig;
