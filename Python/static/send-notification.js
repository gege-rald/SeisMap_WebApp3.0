function iframe_send_notification({ title, timer = false, message }) {
  window.top.postMessage({ type: 'notification', title, timer, message }, '*');
}
