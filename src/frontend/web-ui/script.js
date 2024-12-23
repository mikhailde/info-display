const messageInput = document.getElementById("messageInput");
const sendButton = document.getElementById("sendMessageBtn");
const updateButton = document.getElementById("updateDeviceBtn");
const notificationDiv = document.getElementById("notification");
const statusDiv = document.getElementById("status");
const statusList = document.getElementById("statusList");

function showNotification(message, type = "success") {
  notificationDiv.textContent = message;
  notificationDiv.classList.remove("success", "error"); // Очищаем классы
  notificationDiv.classList.add(type); // Добавляем класс в зависимости от типа
  notificationDiv.style.display = "block"; // Показываем уведомление

  // Скрываем уведомление через 5 секунд
  setTimeout(() => {
    notificationDiv.style.display = "none";
  }, 5000);
}

function sendMessage(event) {
  event.preventDefault(); // Предотвращаем стандартное поведение формы

  const message = messageInput.value.trim();
  if (!message) {
    showNotification("Пожалуйста, введите сообщение.", "error");
    return;
  }

  fetch('/api/v1/content', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ message: message })
  })
  .then(handleResponse)
  .then(data => {
      showNotification(data.message || "Сообщение успешно отправлено.");
      messageInput.value = ""; // Очищаем поле ввода после успешной отправки
  })
  .catch(error => {
    showNotification(error.message || error.detail || "Ошибка при отправке сообщения.", "error");
  });
}

function updateDevice() {
  statusDiv.textContent = "Отправка запроса на обновление...";

  fetch('/api/v1/device/update', {
    method: 'POST'
  })
  .then(handleResponse)
  .then(data => {
      statusDiv.textContent = data.message || "Данные отправлены на табло.";
  })
  .catch(error => {
    statusDiv.textContent = error.message || error.detail || "Ошибка при обновлении табло.";
  });
}

function handleResponse(response) {
  if (response.ok) {
    // Проверяем, есть ли тело ответа
    if (response.status === 204) {
      // Если статус 204 No Content, то тела нет
      return {}; // Возвращаем пустой объект, чтобы не сломать цепочку then
    } else {
        return response.json();
    }
  } else {
    return response.json().then(data => {
      throw data;
    });
  }
}

function updateStatusList(data) {
    statusList.innerHTML = ""; // Очищаем список перед обновлением

    const statusItem = document.createElement("li");
    statusItem.textContent = `Статус: ${data.status || "Неизвестно"}`;
    statusList.appendChild(statusItem);

    const lastSeenItem = document.createElement("li");
    lastSeenItem.textContent = `Последнее обновление: ${data.last_seen || "Неизвестно"}`;
    statusList.appendChild(lastSeenItem);

    const messageItem = document.createElement("li");
    messageItem.textContent = `Текущее сообщение: ${data.message || "Неизвестно"}`;
    statusList.appendChild(messageItem);

    const brightnessItem = document.createElement("li");
    brightnessItem.textContent = `Яркость: ${data.brightness || "Неизвестно"}`;
    statusList.appendChild(brightnessItem);

    const temperatureItem = document.createElement("li");
    temperatureItem.textContent = `Температура: ${data.temperature || "Неизвестно"}`;
    statusList.appendChild(temperatureItem);

    const freeSpaceItem = document.createElement("li");
    freeSpaceItem.textContent = `Свободное место: ${data.free_space || "Неизвестно"}`;
    statusList.appendChild(freeSpaceItem);

    const uptimeItem = document.createElement("li");
    uptimeItem.textContent = `Время работы: ${data.uptime || "Неизвестно"}`;
    statusList.appendChild(uptimeItem);
}

function getDeviceStatus() {
  fetch('/api/v1/device/1/status')
    .then(handleResponse)
    .then(data => {
      updateStatusList(data);
    })
    .catch(error => {
      console.error("Ошибка при получении статуса устройства:", error);
      statusList.innerHTML = `<li>Ошибка при получении статуса устройства</li>`;
    });
}

sendButton.addEventListener("click", sendMessage);
updateButton.addEventListener("click", updateDevice);

// Первоначальное получение статуса
getDeviceStatus();

// Периодическое обновление статуса каждые 5 секунд
setInterval(getDeviceStatus, 5000);
