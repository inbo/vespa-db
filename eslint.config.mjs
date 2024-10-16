import globals from "globals";
import pluginVue from "eslint-plugin-vue";

export default [
  { languageOptions: { globals: globals.browser }},
  ...pluginVue.configs["flat/essential"],
  {
    rules: {
      'vue/no-parsing-error': 'error',
    }
  }
];
