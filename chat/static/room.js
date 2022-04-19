// console.log("Sanity check from room.js.");

function hide_broken_image() {
  const imgs = document.querySelectorAll('img');
  imgs.forEach((img) => {
    img.onerror = function() {
      this.style.display = 'none';
    }
  });
}

hide_broken_image()

const roomName = JSON.parse(document.getElementById("roomName").textContent);
const avatar_url = document.querySelector('#avatar').src;
const username = document.querySelector('#avatar').alt.replace(' avatar', '');

let ended = false;
let photo;
let currentPage = 2;
const file = document.querySelector('input[type=file]');
const q2 = document.querySelector('#q2');
let chatLog = document.querySelector("#chatLog");
let chatMessageInput = document.querySelector("#chatMessageInput");
let chatMessageSend = document.querySelector("#chatMessageSend");
let onlineUsersSelector = document.querySelector("#onlineUsersSelector");

file.addEventListener('change', () => {
  const fileListArr = Array.from(file.files);
  fileListArr.splice(0, 1); // here u remove the file
  // console.log(fileListArr);
})


function createMessage(author, msg, photo, timestamp, attachment) {
  const newMessage = document.createElement('div');
  newMessage.classList.add('message');
  const user = document.createElement('div');
  user.classList.add('message_user');
  const avatar = document.createElement('img');
  avatar.src = photo;
  avatar.style.width = '40px';
  avatar.style.height = '40px';
  avatar.classList.add('avatar');
  const username = document.createElement('div');
  username.textContent = author;
  const message = document.createElement('div');
  message.classList.add('message_text');
  const message_text = document.createElement('div');
  message_text.textContent = msg;
  message_text.classList.add('message_text__conteiner');
  message.appendChild(message_text);
  const message_timestamp = document.createElement('div');
  message_timestamp.textContent = timestamp;
  message_timestamp.classList.add("message_text__timestamp");
  message.appendChild(message_timestamp);

  user.appendChild(avatar);
  user.appendChild(username);

  newMessage.appendChild(user);

  if (attachment) {
    const att = document.createElement('img');
    att.src = attachment;
    att.style.width = "160px";
    att.style.height = "80px";
    message.appendChild(att);
  }

  newMessage.appendChild(message);
  return newMessage;
}

function addMessage(author, msg, photo, timestamp, attachment) {
  const message = createMessage(author, msg, photo, timestamp, attachment);
  chatLog.appendChild(message);
}

function loadMessage(author, msg, photo, timestamp, attachment) {
  const message = createMessage(author, msg, photo, timestamp, attachment);
  chatLog.prepend(message);
}

// adds a new option to 'onlineUsersSelector'
function onlineUsersSelectorAdd(username, avatar_url) {
  const qw = document.querySelector("#" + username + "_online");
  if (qw) return;
  const newOption = document.createElement("div");
  newOption.id = username + "_online";
  const uname = document.createElement("div");
  uname.style.alignSelf = 'center';
  uname.textContent = username;
  const avatar = document.createElement("div");
  const img = document.createElement("img");
  img.src = avatar_url;
  img.alt = username + ' avatar';
  img.style.width = '40px';
  img.style.height = '40px';
  img.classList.add('avatar');
  avatar.appendChild(img);
  newOption.appendChild(avatar);
  newOption.appendChild(uname);
  newOption.classList.add("user_online_info");
  onlineUsersSelector.appendChild(newOption);
}

// removes an option from 'onlineUsersSelector'
function onlineUsersSelectorRemove(username) {
  const oldOption = document.querySelector("#" + username + "_online");
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

function loading_messages(e) {
  e.preventDefault();
  e.stopPropagation();
  const msg = {
    "updater": {
      "page": currentPage,
    }
  }
  chatSocket.send(JSON.stringify(msg));
}

// clear the 'chatMessageInput' and forward the message
chatMessageSend.onclick = function () {
  if (chatMessageInput.value.length === 0 && !photo) return;
  if (photo) {
    const fr = new FileReader();
    fr.onloadend = () => {
      const msg = {
        message: chatMessageInput.value,
        photo: fr.result,
      };
      chatMessageInput.value = "";
      chatSocket.send(JSON.stringify(msg));
      q2.src = '#';
      q2.style.display = 'none';
    };
    fr.readAsDataURL(photo);
    return;
  }

  chatSocket.send(
    JSON.stringify({
      message: chatMessageInput.value,
    })
  );
  chatMessageInput.value = "";
  return;
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
    // console.log(data);

    switch (data.type) {
      case "user_list":
        {
          for (let i = 0; i < data.users.length; i += 1) {
            onlineUsersSelectorAdd(data.users[i].username, data.users[i].photo);
          }
          break;
        }
      case "user_join":
        {
          onlineUsersSelectorAdd(data.user.username, data.user.photo);
          break;
        }
      case "user_leave":
        {
          console.log(data.user.username + " leave the room.");
          onlineUsersSelectorRemove(data.user.username);
          break;
        }
      case "message_loading":
        {
          const ended_messages = data.messages.ended;
          if (ended_messages) {
            ended = true;
            break;
          }
          const messages = data.messages.page;
          for (let i = 0; i < messages.length; i += 1) {
            const message = JSON.parse(messages[i]);
            const username = message.username;
            const content = message.content;
            const attachment = message.attachment;
            const avatar_url = message.avatar_url;
            const timestamp = message.timestamp;
            loadMessage(username, content, avatar_url, timestamp, attachment);
          }
          currentPage += 1;
          break;
        }
      case "chat_public_message":
        {
          const username = data.user.username;
          const avatar_url = data.user.avatar_url;
          const content = data.message.content;
          const timestamp = data.message.timestamp;
          addMessage(username, content, avatar_url, timestamp);
          break;
        }
      case "chat_public_with_attachment_message":
        {
          const username = data.user.username;
          const avatar_url = data.user.avatar_url;
          const content = data.message.content;
          const timestamp = data.message.timestamp;
          const attachment = data.message.attachment;

          addMessage(username, content, avatar_url, timestamp, attachment);
          break
        }
      case "chat_private_message":
        {
          const username = data.user.username;
          const avatar_url = data.user.avatar_url;
          const content = data.message.content;
          const timestamp = data.message.timestamp;
          addMessage(username, "PM from " + username + ": " + content, avatar_url, timestamp);
          break;
        }
      case "chat_private_with_attachment_message":
        {
          const username = data.user.username;
          const avatar_url = data.user.avatar_url;
          const content = data.message.content;
          const timestamp = data.message.timestamp;
          const attachment = data.message.attachment
          addMessage(username, "PM from " + username + ": " + content, avatar_url, timestamp, attachment);
          break;
        }
      case "private_message_delivered":
        {
          const message = data.message;
          const content = message.content;
          const attachment = message.attachment;
          const timestamp = message.timestamp;
          addMessage(username + ':', "PM to " + data.target + ": " + content, avatar_url, timestamp, attachment);
          break;
        }
      default:
        {
          console.error("Unknown message type!");
          break;
        }
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


window.addEventListener("unload", function () {
    if(chatSocket.readyState == WebSocket.OPEN)
        chatSocket.close();
});

function upload_img(input) {
  if (input.files && input.files[0]) {
    photo = input.files[0];
    const src = URL.createObjectURL(input.files[0])
    q2.src = src;
    q2.style.display = 'block';
  }
}

window.onload = function() {
  file.addEventListener('change', (e) => {
      e.stopPropagation();
      upload_img(e.target)
  });
}

const sending_form = document.querySelector('#sending_form');
sending_form.addEventListener('submit', (e) => {
  e.preventDefault();
  chatMessageSend.click();
  file.value = '';
});

onlineUsersSelector.ondblclick = function (e) {
  const target = e.target;
  e.stopPropagation();
  const user_info_online = target.closest('.user_online_info');
  const username = user_info_online.id.replace('#', '').replace('_online', '');
  chatMessageInput.value =
    "/pm " + username + " "
    + chatMessageInput.value;
  chatMessageInput.focus();
};

chatLog.addEventListener('scroll', (e) => {
  const myDiv = e.target;
  // console.log(myDiv.offsetHeight, myDiv.scrollTop, myDiv.scrollHeight);
  if ((myDiv.scrollTop == 0) && (ended == false)) {
    loading_messages(e);
  }
})
