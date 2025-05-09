/**
 * plugins/vuetify.js
 *
 * Framework documentation: https://vuetifyjs.com`
 */

// Styles
import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import {
  VAutocomplete,
  VTextField,
  VDatePicker,
  VChip,
} from 'vuetify/components'

export default createVuetify({
  components: {
    VAutocomplete,
    VTextField,
    VDatePicker,
    VChip,
  },
})