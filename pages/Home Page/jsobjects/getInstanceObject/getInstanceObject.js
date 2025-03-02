export default {
	async queryAutoRefresh() {
		try {
			const response = await ServiceListGet.run();  // Run API request
			if(appsmith.store.JWTToken === "" || response.status === 401){
				navigateTo("Login Page")
			}
			if (response) {
				storeValue("services", response);
			} else {
				storeValue("services", []);
				showAlert("Error: Invalid response received", "error");
			}
		} catch (e) {

		}
		return true;
	}
}