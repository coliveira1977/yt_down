async function baixarVideo() {
    let url = document.getElementById("videoUrl").value;
    let statusText = document.getElementById("status");

    if (!url) {
        statusText.innerHTML = "Por favor, insira um link válido!";
        return;
    }

    statusText.innerHTML = "Processando...";

    let response = await fetch("/baixar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url })
    });

    let data = await response.json();

    if (data.success) {
        window.location.href = data.downloadLink; // Redireciona para o arquivo baixado
    } else {
        statusText.innerHTML = "Erro ao baixar o vídeo!";
    }
}
