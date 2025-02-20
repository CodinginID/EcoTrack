document.getElementById('dataForm').addEventListener('submit', function(event) {
    event.preventDefault();  // Menghindari reload halaman saat form disubmit

    // Ambil data dari form
    const tahun = document.getElementById('tahun').value;
    const id_propinsi = document.getElementById('id_propinsi').value;
    const id_district = document.getElementById('id_district').value;

    // Siapkan data untuk dikirimkan ke API
    const data = {
        tahun: tahun,
        id_propinsi: id_propinsi,
        id_district: id_district
    };

    // Kirim data menggunakan fetch dengan metode POST
    fetch('/get_data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        // Tampilkan hasil dari API ke dalam elemen <pre>
        document.getElementById('response').textContent = JSON.stringify(result, null, 2);
    })
    .catch(error => {
        document.getElementById('response').textContent = 'Error: ' + error;
    });
});
