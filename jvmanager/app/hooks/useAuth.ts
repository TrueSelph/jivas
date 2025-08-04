import { useEffect } from "react";
import { redirect, useLocation } from "react-router";

const useAuth = () => {
	const location = useLocation();

	useEffect(() => {
		const token = localStorage.getItem("jivas-token");
		const tokenExp = localStorage.getItem("jivas-token-exp");

		if (!token) {
			if (location.pathname !== "/login") {
				throw redirect("/login");
			}
			return;
		}

		if (tokenExp) {
			if (Date.now() > parseInt(tokenExp, 10)) {
				localStorage.removeItem("jivas-token");
				localStorage.removeItem("jivas-token-exp");
				if (location.pathname !== "/login") {
					throw redirect("/login");
				}
			}
		}
	}, [location]);
};

export default useAuth;
