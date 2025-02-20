export default {
	Button1onClick() {
		if(LoginInput.isValid && PasswordInput.isValid){
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
				.catch((e) => showAlert("Unsuccessful login" + e, "error")); // Run if the query encounters any errors
			return 1;
		}else {
			showAlert("Please provide valid login and password values")
		}
	} 

}