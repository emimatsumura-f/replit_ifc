document.addEventListener('DOMContentLoaded', function() {
    // Initialize Feather icons
    feather.replace();

    // Handle file upload form submission
    const uploadForm = document.getElementById('uploadForm');
    const uploadBtn = document.getElementById('uploadBtn');
    const spinner = uploadBtn.querySelector('.spinner-border');

    if (uploadForm) {
        uploadForm.addEventListener('submit', function() {
            // Disable button and show spinner
            uploadBtn.disabled = true;
            spinner.classList.remove('d-none');
            uploadBtn.textContent = ' Processing...';
            spinner.parentNode.insertBefore(spinner, uploadBtn.firstChild);
        });
    }

    // File input validation
    const fileInput = document.getElementById('file');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                if (!file.name.toLowerCase().endsWith('.ifc')) {
                    alert('Please select an IFC file');
                    this.value = '';
                } else if (file.size > 16 * 1024 * 1024) { // 16MB
                    alert('File size must be less than 16MB');
                    this.value = '';
                }
            }
        });
    }
});
