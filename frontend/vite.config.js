// Plugins
import Vue from '@vitejs/plugin-vue'
import ViteFonts from 'unplugin-fonts/vite'
import Components from 'unplugin-vue-components/vite'
import Vuetify, { transformAssetUrls } from 'vite-plugin-vuetify'

// Utilities
import { fileURLToPath, URL } from 'node:url'
import { defineConfig, loadEnv } from 'vite'

// Log statement to ensure the config file is being executed

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // Determine the root path
  const env = loadEnv(mode, process.cwd())

  return {
    base: '/',
    plugins: [
      Vue({
        template: { transformAssetUrls }
      }),
      // https://github.com/vuetifyjs/vuetify-loader/tree/master/packages/vite-plugin#readme
      Vuetify(),
      Components(),
      ViteFonts({
        google: {
          families: [{
            name: 'Roboto',
            styles: 'wght@100;300;400;500;700;900',
          }],
        },
        custom: {
          families: [
            {
              name: 'MaterialDesignIcons',
              local: 'MaterialDesignIcons',
              src: './src/assets/materialdesignicons-webfont.woff2',
            },
          ],
          preload: true,
        }
      }),
    ],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url))
      },
      extensions: [
        '.js',
        '.json',
        '.jsx',
        '.mjs',
        '.ts',
        '.tsx',
        '.vue',
      ],
    },
    server: {
      port: 3000,
    },
    define: {
      'process.env': env
    }
  }
})
