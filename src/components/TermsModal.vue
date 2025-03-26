<template>
    <div class="modal fade" id="termsModal" tabindex="-1" aria-labelledby="termsModalLabel" aria-hidden="true">
      <div class="modal-dialog modal-dialog-centered modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="termsModalLabel">Gebruikersvoorwaarden</h5>
          </div>
          <div class="modal-body">
            <p>Bij het gebruik van het account van Vespa-DB geeft u aan akkoord te zijn met de 
              <a href="https://vespawatch.be/terms-of-use/" target="_blank">gebruikersvoorwaarden</a> 
              en handelt u hier ook naar. Bij het niet naleven van de gebruikersvoorwaarde zal de toegang geweigerd worden.</p>
            
            <p class="small text-muted">
              Bekijk ook onze <a href="https://vespawatch.be/privacy-policy/" target="_blank">privacy policy</a>.
            </p>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="onCancel">Annuleren</button>
            <button type="button" class="btn btn-success" @click="acceptTerms">Akkoord</button>
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  export default {
    methods: {
      acceptTerms() {
        this.$emit('accept');
      },
      onCancel() {
        this.$emit('cancel');
      }
    }
  }
  </script>