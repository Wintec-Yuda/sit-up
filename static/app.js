$(document).ready(function () {
    $("#uploadButton").click(function () {
        let formData = new FormData();
        formData.append('nama', $('#namaUpload').val());
        formData.append('file', $('#file')[0].files[0]);

        let apiUrl = "upload";

        $.ajax({
            type: "POST",
            url: apiUrl,
            data: formData,
            contentType: false,
            processData: false,
            success: function (data) {
                if (data) {
                    $("#iframeVideo").removeClass("d-none").addClass("d-block");
                    $("#iframeVideo").attr("href", `http://127.0.0.1:5000/video_feed_upload?file_path=${data.file_path}&nama=${data.nama}`);
                } else {
                    alert("Gagal mengupload video.");
                }
            },
            error: function (xhr, status, error) {
                console.error("Error:", xhr, status, error);
                alert("Terjadi kesalahan. Silakan coba lagi.");
            }
        });
    });
    $("#realtimeButton").click(function () {
        let data = {
            'nama': $('#namaRealtime').val(),
            'waktu': $('#waktu').val(),
        };
        if (data) {
            $("#iframeVideo").removeClass("d-none").addClass("d-block");
            $("#iframeVideo").attr("href", `http://127.0.0.1:5000/video_feed_realtime?nama=${data.nama}&waktu=${data.waktu}`);
        } else {
            alert("Gagal mengupload video.");
        }
    });
});
