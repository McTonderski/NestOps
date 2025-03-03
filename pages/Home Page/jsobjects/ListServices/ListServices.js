export default {
	async listServicesQuery() {
		try {
			const response = await ServiceListGet.run();  // Run API request
			if(appsmith.store.JWTToken === "" || response.status === 401){
				navigateTo("Login Page")
			}
			if (response) {
				storeValue("services", response);
			} else {
				storeValue("services", [{"name": "demo", "status": "stopped"}]);
				showAlert("Error: Invalid response received", "error");
			}
		} catch (e) {

		}
		return true;
	},

	intervalId: null,  // Store the interval ID for clearing

	async startAutoRefresh() {
		if (AutoRefreshInstance.isSwitchedOn) {
			if (!this.intervalId) {  // Prevent multiple intervals
				this.intervalId = setInterval(async () => {
					await this.listServicesQuery()();
				}, 5000);
			}
		} else {
			if (this.intervalId) {
				clearInterval(this.intervalId);
				this.intervalId = null;  // Reset interval ID
			}
		}
	}
}
