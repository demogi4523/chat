function upload_img(input) {
  if (input.files && input.files[0]) {
    const src = URL.createObjectURL(input.files[0])
    const img = document.querySelector('#img_id');
    img.src = src;
    img.style.display = 'block';
  }
}

function hide_broken_image() {
    const img = document.querySelector('#img_id');
    img.onerror = function() {
        // this.style.visibility = 'hidden';
        this.style.display = 'none';
    }
}

hide_broken_image()

window.onload = function() {
    const file = document.querySelector('input[type=file]');
    file.addEventListener('change', (e) => {
        e.stopPropagation();
        upload_img(e.target)
    });
}
