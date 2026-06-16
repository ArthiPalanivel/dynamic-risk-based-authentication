let keyDownTimes = [];
let dwellTimes = [];
let flightTimes = [];
let keystrokePattern = [];

let lastKeyUp = null;

const passwordField = document.getElementById("password");
const form = document.getElementById("loginForm");

passwordField.addEventListener("keydown", (e) => {

    // Ignore special keys
    if (e.key.length > 1) return;

    const now = performance.now();

    keyDownTimes.push(now);

    if (lastKeyUp !== null) {
        let flight = now - lastKeyUp;
        flightTimes.push(flight);
    }

});

passwordField.addEventListener("keyup", (e) => {

    if (e.key.length > 1) return;

    const now = performance.now();

    const lastKeyDown = keyDownTimes[keyDownTimes.length - 1];

    if (lastKeyDown) {
        let dwell = now - lastKeyDown;
        dwellTimes.push(dwell);
        keystrokePattern.push(dwell);
    }

    lastKeyUp = now;

});

form.addEventListener("submit", function () {

    const dwellAvg =
        dwellTimes.reduce((a,b)=>a+b,0) / (dwellTimes.length || 1);

    const flightAvg =
        flightTimes.reduce((a,b)=>a+b,0) / (flightTimes.length || 1);

    // dwell average
    const dwellInput = document.createElement("input");
    dwellInput.type = "hidden";
    dwellInput.name = "dwell_time";
    dwellInput.value = dwellAvg;

    // flight average
    const flightInput = document.createElement("input");
    flightInput.type = "hidden";
    flightInput.name = "flight_time";
    flightInput.value = flightAvg;

    // full keystroke pattern
    const patternInput = document.createElement("input");
    patternInput.type = "hidden";
    patternInput.name = "keystroke_pattern";
    patternInput.value = JSON.stringify(keystrokePattern);

    this.appendChild(dwellInput);
    this.appendChild(flightInput);
    this.appendChild(patternInput);

});
