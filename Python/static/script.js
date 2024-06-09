let sections = document.querySelectorAll('section');
let navLinks = document.querySelectorAll('header nav a');
window.onscroll = () => {
    sections.forEach(sec => {
        let top = window.scrollY;
        let offset = sec.offsetTop - 150;
        let height = sec.offsetHeight;
        let id = sec.getAttribute('id');
        if(top >= offset && top < offset + height) {
            navLinks.forEach(links => {
                links.classList.remove('active');
                document.querySelector('header nav a[href*=' + id + ']').classList.add('active');
            });
        };
    });
};

const notification_decay_duration_ms = 5000;

window.addEventListener('message', event => {
    const notif_data = event.data;
    if (notif_data.type !== "notification") {
        return;
    }

    const new_notif = new_notification(notif_data);
    push_notification(new_notif);
});

function new_notification(notif_data) {
    const Title = document.createElement('h2');
    Title.innerHTML = notif_data.title;

    const Message = document.createElement('p');
    Message.innerHTML = notif_data.message;

    const CloseButton = document.createElement('button');
    CloseButton.innerHTML = 'x';
    CloseButton.classList.add('close-notif-button');
    CloseButton.addEventListener('click', event => handle_close_notif_click(event.target));

    setTimeout(() => handle_close_notif_click(CloseButton), notification_decay_duration_ms);

    const Notification = children(document.createElement('div'),
        Title,
        Message,
        CloseButton,
    );

    Notification.classList.add('notification');
    return Notification;
}

function handle_close_notif_click(button_element) {
    const data_id = button_element.getAttribute('data-id');

    const notification_wrapper = document.querySelector('.notification-wrapper');
    const notification = notification_wrapper.querySelector(`.notification[data-id="${data_id}"]`);
    notification_wrapper.removeChild(notification);

    update_notifications(notification_wrapper);
}

function push_notification(new_notif) {
    const notifications = document.querySelector('.notification-wrapper');
    notifications.appendChild(new_notif);
    
    update_notifications(notifications);
}

function update_notifications(notification_wrapper) {
    const notifications = notification_wrapper.querySelectorAll('.notification');
    let index = 0;

    for (const notification of notifications) {
        const button = notification.querySelector('.close-notif-button');

        notification.setAttribute('data-id', index);
        button.setAttribute('data-id', index);

        index += 1;
    }
}
