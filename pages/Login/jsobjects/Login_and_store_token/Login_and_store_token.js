export default {
	Button1onClick() {
		LoginQuery.run()
			.then((response) => {  // Run after the query is successful
			if (response && response.access_token) {
				storeValue("JWT_TOKEN", response.access_token, persist=True); // Save the token
				showAlert("Login Successful", "success");
				navigateTo("Home Page")
			} else {
				showAlert("Login failed: No token received", "error");
			}
		})
			.catch(() => showAlert("Unsuccessful login", "error")); // Run if the query encounters any errors
		return true;
	}
}