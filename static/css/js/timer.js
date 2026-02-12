let timeLeft = 1200;
let timerDisplay = document.getElementById("timer");

let countdown = setInterval(function() {
    let minutes = Math.floor(timeLeft / 60);
    let seconds = timeLeft % 60;
    timerDisplay.innerHTML = minutes + ":" + (seconds < 10 ? "0" : "") + seconds;
    timeLeft--;

    if (timeLeft < 0) {
        clearInterval(countdown);
        alert("Time is up! Submitting exam...");
        document.getElementById("examForm").submit();
    }
}, 1000);
