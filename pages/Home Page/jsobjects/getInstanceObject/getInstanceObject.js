export default {
	async queryAutoRefresh() {
		try {
			showAlert(appsmith.store.JWTToken, "success")
			const response = await getInstanceDetails.run();  // Run API request

			if (response) {
				// Extract necessary details
				const cpuUsage = response.cpu_usage_percent;  // CPU usage in percentage
				const memoryUsage = response.memory_usage.percent;  // Memory usage in percentage
				const containerSummary = [
					{ x: "Running", y: 0 },
					{ x: "Stopped", y: 0 },
					{ x: "Errors", y: 0 }
				];

				response.running_docker_containers.forEach(container => {
					if (container.Status === "Running") {
						containerSummary.find(item => item.x === "Running").y++;
					} else if (container.Status === "Stopped") {
						containerSummary.find(item => item.x === "Stopped").y++;
					} else {
						containerSummary.find(item => item.x === "Errors").y++;
					}
				});
				const servicesCount = containerSummary.reduce((sum, item) => sum + item.y, 0);
				console.log(containerSummary);
				console.log("Total Services Count:", servicesCount);
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
			showAlert("Failed to fetch instance details: " + e.message, "error");
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
};