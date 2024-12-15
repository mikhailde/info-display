const sendMessageBtn = document.getElementById("sendMessageBtn");
const messageText = document.getElementById("messageText");
const statusDiv = document.getElementById("status");
const updateDeviceBtn = document.getElementById("updateDeviceBtn");

/*
sendMessageBtn.addEventListener("click", async () => {
    const message = messageText.value.trim();
    if (!message) {
        statusDiv.textContent = "Введите текст сообщения!";
        return;
    }

    try {
        const response = await fetch("/api/v1/content", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message }),
        });

        if (response.ok) {
            statusDiv.textContent = "Сообщение успешно отправлено.";
            messageText.value = "";
        } else {
            statusDiv.textContent = "Ошибка при отправке сообщения.";
        }
    } catch (error) {
        statusDiv.textContent = "Произошла ошибка.";
        console.error(error);
    }
});

updateDeviceBtn.addEventListener("click", async () => {
    statusDiv.textContent = "Обновление данных на табло...";
    try {
        const response = await fetch("/api/v1/device/update", { method: "POST" });

        if (response.ok) {
            statusDiv.textContent = "Команда на обновление данных отправлена на табло.";
        } else {
            statusDiv.textContent = "Ошибка при отправке команды на обновление.";
        }
    } catch (error) {
        statusDiv.textContent = "Произошла ошибка.";
        console.error(error);
    }
});
*/