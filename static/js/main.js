document.addEventListener('DOMContentLoaded', function() {
    // Featherアイコンの初期化
    feather.replace();

    // ファイルアップロードフォームの処理
    const uploadForm = document.getElementById('uploadForm');
    const uploadBtn = document.getElementById('uploadBtn');
    const spinner = uploadBtn.querySelector('.spinner-border');

    if (uploadForm) {
        uploadForm.addEventListener('submit', function() {
            // ボタンを無効化してスピナーを表示
            uploadBtn.disabled = true;
            spinner.classList.remove('d-none');
            uploadBtn.textContent = ' 処理中...';
            spinner.parentNode.insertBefore(spinner, uploadBtn.firstChild);
        });
    }

    // ファイル入力のバリデーション
    const fileInput = document.getElementById('file');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                if (!file.name.toLowerCase().endsWith('.ifc')) {
                    alert('IFCファイルを選択してください');
                    this.value = '';
                } else if (file.size > 16 * 1024 * 1024) { // 16MB
                    alert('ファイルサイズは16MB以下にしてください');
                    this.value = '';
                }
            }
        });
    }
});