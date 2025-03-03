export default {
	async queryAutoRefresh(){
		const containerSummary = [
			{ x: "Running", y: 0 },
			{ x: "Stopped", y: 0 },
			{ x: "Errors", y: 0 }
		];
		try{
			const response = await getInstanceDetails.run();  // Run API request
			if(appsmith.store.JWTToken === "" || response.status === 401){
				navigateTo("Login Page")
			}
			if (response) {
				// Extract necessary details
				const cpuUsage = response.cpu_usage_percent;  // CPU usage in percentage
				const memoryUsage = response.memory_usage.percent;  // Memory usage in percentage
				response.running_docker_containers.forEach(container => {
					if (container.Status === "running") {
						containerSummary.find(item => item.x === "Running").y++;
					} else if (container.Status === "exited") {
						containerSummary.find(item => item.x === "Stopped").y++;
					} else {
						containerSummary.find(item => item.x === "Errors").y++;
					}
				});
				const servicesCount = containerSummary.reduce((sum, item) => sum + item.y, 0);
				// Store values in Appsmith
				storeValue("CPU_USAGE", cpuUsage);
				storeValue("MEMORY_USAGE", memoryUsage);
				storeValue("SERVICE_COUNT", servicesCount);
				storeValue("SERVICE_LIST", response.running_docker_containers);
				storeValue("SERVICE_STATS", containerSummary)

			} else {
				showAlert("Error: Invalid response received", "error");
			}
		} catch (e) {
			showAlert(e.message, "error");
			storeValue("CPU_USAGE", "N/A");
			storeValue("MEMORY_USAGE", "N/A");
			storeValue("SERVICE_COUNT", "N/A");
			storeValue("SERVICE_LIST", [{"x": "Can't gather Service List", "y": 0}]);
			storeValue("SERVICE_STATS", "N/A")
		}
		return true;
	},

	intervalId: null,  // Store the interval ID for clearing

	async startAutoRefresh() {
		if (AutoRefreshInstance.isSwitchedOn) {
			if (!this.intervalId) {  // Prevent multiple intervals
				this.intervalId = setInterval(async () => {
					await this.queryAutoRefresh();
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