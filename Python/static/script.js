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

const time_second_ms = 1000;
const seconds_in_minute = 60;
function new_timer() {
    const Hour = document.createElement('span');
    Hour.classList.add('hour');
    Hour.innerText = '00';

    const Minute = document.createElement('span');
    Minute.classList.add('minute');
    Minute.innerText = '00';

    const Second = document.createElement('span');
    Second.classList.add('second');
    Second.innerText = '00';

    const HourSeperator = document.createElement('span');
    HourSeperator.classList.add('hour-seperator');
    HourSeperator.innerText = ':';

    const MinuteSeperator = document.createElement('span');
    MinuteSeperator.classList.add('minute-seperator');
    MinuteSeperator.innerText = ':';

    const Timer = children(document.createElement('div'),
        Hour,
        HourSeperator,
        Minute,
        MinuteSeperator,
        Second,
    );
    const ticking_function = setInterval(() => {
        const timer = Timer;
        const hour_el = timer.querySelector('.hour');
        const minute_el = timer.querySelector('.minute');
        const second_el = timer.querySelector('.second');

        let hour_val = parseInt(hour_el.innerText);
        let minute_val = parseInt(minute_el.innerText);
        let second_val = parseInt(second_el.innerText);

        second_val += 1;
        if (second_val >= seconds_in_minute) {
            minute_val += 1;
            second_val = 0;
        }

        if (minute_val >= seconds_in_minute) {
            hour_val += 1;
            minute_val = 0;
        }

        hour_el.innerText = pad_number(hour_val);
        minute_el.innerText = pad_number(minute_val);
        second_el.innerText = pad_number(second_val);
    }, time_second_ms);

    return { Timer, ticking_function };
}

function pad_number(number) {
    let result = number.toString();
    if (result.length < 2) {
        result = '0' + result;
    }

    return result;
}

function new_notification(notif_data) {
    const { timer } = notif_data;

    const Title = document.createElement('h2');
    Title.innerText = notif_data.title;

    let Body;
    let notification_ticker;
    if (!timer) {
        const Message = document.createElement('p');

        Message.innerText = notif_data.message;
        Body = Message;

    } else {
        const { Timer, ticking_function } = new_timer();

        notification_ticker = ticking_function;
        Body = Timer;
    }

    const CloseButton = document.createElement('button');
    CloseButton.innerText = 'x';
    CloseButton.classList.add('close-notif-button');

    if (!timer) {
        CloseButton.addEventListener('click', event => handle_close_notif_click(event.target));
        setTimeout(() => handle_close_notif_click(CloseButton), notification_decay_duration_ms);
    } else {
        CloseButton.addEventListener('click', () => {
            clearInterval(notification_ticker);
            handle_close_notif_click(CloseButton);
        });
    }

    const Notification = children(document.createElement('div'),
        Title,
        Body,
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
