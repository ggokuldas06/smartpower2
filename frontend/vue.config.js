const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  transpileDependencies: true,
  lintOnSave: false, // Disable linting on save if you prefer
  devServer: {
    port: 8080, // You can change this port if needed
    open: true  // Automatically open browser when serving
  }
})