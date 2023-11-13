window.onload = function() {
  //<editor-fold desc="Changeable Configuration Block">

  // the following lines will be replaced by docker/configurator, when it runs in a docker-container
  window.ui = SwaggerUIBundle({
    // Provide URL for swagger file
    url: "https://41q4upa6qj.execute-api.ap-south-1.amazonaws.com/iris-service-api/v2/railways/swagger",
    dom_id: '#swagger-ui',
    // Hide the Model Schema tab
    defaultModelsExpandDepth: -1,
    // Show request duration (in ms)
    displayRequestDuration: true,
    deepLinking: true,
    presets: [
      SwaggerUIBundle.presets.apis,
      SwaggerUIStandalonePreset
    ],
    plugins: [
      SwaggerUIBundle.plugins.DownloadUrl
    ],
    layout: "StandaloneLayout"
  });

  //</editor-fold>
};
