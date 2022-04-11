console.log("Sanity check from room.js.");

const roomName = JSON.parse(document.getElementById("roomName").textContent);

let chatLog = document.querySelector("#chatLog");
let chatMessageInput = document.querySelector("#chatMessageInput");
let chatMessageSend = document.querySelector("#chatMessageSend");
let onlineUsersSelector = document.querySelector("#onlineUsersSelector");

// adds a new option to 'onlineUsersSelector'
function onlineUsersSelectorAdd(value) {
  if (document.querySelector("option[value='" + value + "']")) return;
  let newOption = document.createElement("option");
  newOption.value = value;
  newOption.innerHTML = value;
  onlineUsersSelector.appendChild(newOption);
}

// removes an option from 'onlineUsersSelector'
function onlineUsersSelectorRemove(value) {
  let oldOption = document.querySelector("option[value='" + value + "']");
  if (oldOption !== null) oldOption.remove();
}

// focus 'chatMessageInput' when user opens the page
chatMessageInput.focus();

// submit if the user presses the enter key
chatMessageInput.onkeyup = function (e) {
  if (e.keyCode === 13) {
    // enter key
    chatMessageSend.click();
  }
};

// clear the 'chatMessageInput' and forward the message
chatMessageSend.onclick = function () {
  if (chatMessageInput.value.length === 0) return;
  // TODO: forward the message to the WebSocket
  chatSocket.send(
    JSON.stringify({
      message: chatMessageInput.value,
    })
  );
  chatMessageInput.value = "";
};

let chatSocket = null;

function connect() {
  chatSocket = new WebSocket(
    "ws://" + window.location.host + "/ws/chat/" + roomName + "/"
  );

  chatSocket.onopen = function (e) {
    console.log("Successfully connected to the WebSocket.");
  };

  chatSocket.onclose = function (e) {
    console.log(
      "WebSocket connection closed unexpectedly. Trying to reconnect in 2s..."
    );
    setTimeout(function () {
      console.log("Reconnecting...");
      connect();
    }, 2000);
  };

  chatSocket.onmessage = function (e) {
    const data = JSON.parse(e.data);
    console.log(data);

    switch (data.type) {
      case "chat_message":
        chatLog.value += data.user + ": " + data.message + "\n";
        break;
      case "user_list":
        for (let i = 0; i < data.users.length; i += 1) {
          onlineUsersSelectorAdd(
            data.users[i].username + ":   " + data.users[i].photo
          );
        }
        break;
      case "user_join":
        chatLog.value += data.user.username + " joined the room.\n";
        onlineUsersSelectorAdd(data.user.username + ":   " + data.user.photo);
        break;
      case "user_leave":
        chatLog.value += data.user.username + " leave the room.\n";
        onlineUsersSelectorRemove(
          data.user.username + ":   " + data.user.photo
        );
        break;
      case "private_message":
        chatLog.value += "PM from " + data.user + ": " + data.message + "\n";
        break;
      case "private_message_delivered":
        chatLog.value += "PM to " + data.target + ": " + data.message + "\n";
        break;
      default:
        console.error("Unknown message type!");
        break;
    }

    // scroll 'chatLog' to the bottom
    chatLog.scrollTop = chatLog.scrollHeight;
  };

  chatSocket.onerror = function (err) {
    console.log("WebSocket encountered an error: " + err.message);
    console.log("Closing the socket.");
    chatSocket.close();
  };
}
connect();

onlineUsersSelector.onchange = function () {
  chatMessageInput.value =
    "/pm " + onlineUsersSelector.value.split(":")[0] + " ";
  onlineUsersSelector.value = null;
  chatMessageInput.focus();
};

window.addEventListener("unload", function () {
    if(chatSocket.readyState == WebSocket.OPEN)
        chatSocket.close();
});
