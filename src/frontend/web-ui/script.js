const API_KEY = "your_api_key_here"; // Замени на свой API ключ
const messageInput = document.getElementById("messageText");
const sendButton = document.getElementById("sendMessageBtn");
const updateButton = document.getElementById("updateDeviceBtn");
const notificationDiv = document.getElementById("notification");

function showNotification(message, isError = false) {
  notificationDiv.textContent = message;
  notificationDiv.className = isError ? "error" : "success";
  setTimeout(() => {
    notificationDiv.textContent = "";
    notificationDiv.className = "";
  }, 5000);
}

function sendMessage() {
  const message = messageInput.value.trim();
  if (!message) {
    showNotification("Пожалуйста, введите сообщение.", true);
    return;
  }

  fetch('/api/v1/content', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': API_KEY
    },
    body: JSON.stringify({ message: message })
  })
  .then(handleResponse)
  .catch(handleError);
}

function updateDevice() {
  fetch('/api/v1/device/update', {
    method: 'POST',
    headers: {
      'X-API-Key': API_KEY
    }
  })
  .then(handleResponse)
  .catch(handleError);
}

function handleResponse(response) {
  if (response.ok) {
    // Проверяем, есть ли тело ответа
    if (response.status === 204) {
      // Если статус 204 No Content, то тела нет
      showNotification("Запрос на обновление данных успешно отправлен.");
      return; // Завершаем выполнение, так как тела нет
    } else {
        return response.json().then(data => {
            if (data && data.message) {
                showNotification(data.message);
            } else {
                showNotification("Операция успешно выполнена.");
            }
        });
    }
  } else {
    return response.json().then(data => {
      throw data;
    });
  }
}

function handleError(error) {
  showNotification(`Ошибка: ${error.message || error.detail || "Неизвестная ошибка"}`, true);
}

sendButton.addEventListener("click", sendMessage);
updateButton.addEventListener("click", updateDevice);
