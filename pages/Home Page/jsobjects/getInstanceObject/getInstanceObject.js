export default {
	async queryAutoRefresh() {
		try {
			showAlert("{{JWT_TOKEN}}","success")
			const response = await getInstanceDetails.run();  // Run API request

			if (response) {
				// Extract necessary details
				const cpuUsage = response.cpu_usage_percent;  // CPU usage in percentage
				const memoryUsage = response.memory_usage.percent;  // Memory usage in percentage
				const runningServices = response.running_docker_containers.map(container => container.Name); // List of running services
				const servicesCount = runningServices.length;  // Number of running services

				// Store values in Appsmith
				storeValue("CPU_USAGE", cpuUsage);
				storeValue("MEMORY_USAGE", memoryUsage);
				storeValue("SERVICE_COUNT", servicesCount);
				storeValue("SERVICE_LIST", runningServices);

				showAlert("System stats updated successfully", "success");
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