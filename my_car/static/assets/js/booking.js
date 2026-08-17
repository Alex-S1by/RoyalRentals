document.addEventListener("DOMContentLoaded", function () {

    // DATE PICKER
    flatpickr(".date-picker", {
        dateFormat: "d M Y",
        minDate: "today",
        disableMobile: true
    });

    // TIME PICKER
    flatpickr(".time-picker", {
        enableTime: true,
        noCalendar: true,
        dateFormat: "h:i K",
        time_24hr: false,
        minuteIncrement: 30,
        disableMobile: true
    });

});
