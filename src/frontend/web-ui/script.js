const messageInput = document.getElementById("messageText");
const sendButton = document.getElementById("sendMessageBtn");
const updateButton = document.getElementById("updateDeviceBtn");
const notificationDiv = document.getElementById("notification"); // Добавляем ссылку на div для уведомлений

function showNotification(message, isError = false) {
  notificationDiv.textContent = message;
  notificationDiv.className = isError ? "error" : "success"; // Добавляем класс для стилизации (CSS ниже)
  setTimeout(() => {
    notificationDiv.textContent = "";
    notificationDiv.className = "";
  }, 5000); // 5 секунд
}

function sendMessage() {
  const message = messageInput.value.trim();
  if (!message) {
    showNotification("Пожалуйста, введите сообщение.", true);
    return;
  }

  fetch('/api/v1/content', { // Исправлено на /api/v1/content
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ message: message })
  })
  .then(response => {
    if (response.ok) {
      showNotification("Сообщение успешно отправлено.");
      messageInput.value = "";
    } else {
      return response.json().then(data => { throw data });
    }
  })
  .catch(error => {
    showNotification(`Ошибка: ${error.message || error.detail || "Неизвестная ошибка"}`, true);
  });
}

function updateDevice() {
  fetch('/api/v1/device/update', {
    method: 'POST'
  })
  .then(response => {
    if (response.ok) {
      showNotification("Запрос на обновление данных успешно отправлен.");
    } else {
      return response.json().then(data => { throw data });
    }
  })
  .catch(error => {
    showNotification(`Ошибка: ${error.message || error.detail || "Неизвестная ошибка"}`, true);
  });
}

sendButton.addEventListener("click", sendMessage);
updateButton.addEventListener("click", updateDevice);
