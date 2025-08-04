import { redirect } from "react-router";

export function clientLoader() {
	// const host = localStorage.getItem("host");
	// localStorage.clear();
	// localStorage.setItem("host", host || "");
	return redirect("/login");
}
