import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', '')
  const tunnelHost = env.VITE_TUNNEL_HOST
  const proxyTarget = env.VITE_PROXY_TARGET || 'http://localhost:8000'

  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      host: '0.0.0.0',
      port: 5173,
      strictPort: true,
      allowedHosts: tunnelHost ? [tunnelHost] : [],
      watch: {
        usePolling: true,
        interval: 1000,
      },
      hmr: tunnelHost
        ? { host: tunnelHost, protocol: 'wss', clientPort: 443 }
        : { host: 'localhost', protocol: 'ws' },
      proxy: {
        '/api': {
          target: proxyTarget,
          changeOrigin: false,
        },
        '/media': {
          target: proxyTarget,
          changeOrigin: false,
        },
      },
    },
  }
})
