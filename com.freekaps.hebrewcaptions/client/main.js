/* ============================================================
   main.js  –  Node.js bridge running inside the CEP panel
   ============================================================ */

var path, spawn, os, fs, nodeAvailable = false;
try {
    path  = require("path");
    spawn = require("child_process").spawn;
    os    = require("os");
    fs    = require("fs");
    nodeAvailable = true;
} catch (e) {}

var csInterface;
try { csInterface = new CSInterface(); } catch (e) {}

// ── DOM refs ──────────────────────────────────────────────────
var btnGenerate    = document.getElementById("btn-generate");
var btnCancel      = document.getElementById("btn-cancel");
var btnCopyLog     = document.getElementById("btn-copy-log");
var btnRefresh     = document.getElementById("btn-refresh-tracks");
var trackSelect    = document.getElementById("track-select");
var wordsSlider    = document.getElementById("words-slider");
var wordsValue     = document.getElementById("words-value");
var checkAutoplace = document.getElementById("check-autoplace");
var checkRtlFix    = document.getElementById("check-rtl-fix");
var logDiv         = document.getElementById("log");
var statusBadge    = document.getElementById("status-badge");
var statusText     = document.getElementById("status-text");
var stepPips       = document.querySelectorAll(".step-pip");

var currentProcess = null;
var isCancelled = false;

wordsSlider.addEventListener("input", function() {
    wordsValue.textContent = wordsSlider.value;
});

function log(msg, type) {
    type = type || "info";
    var line = document.createElement("div");
    line.className = "log-" + type;
    var ts = new Date().toLocaleTimeString("en-GB", {hour12: false});
    line.textContent = "[" + ts + "] " + msg;
    logDiv.appendChild(line);
    logDiv.scrollTop = logDiv.scrollHeight;
}

function setStatus(text, state) {
    statusText.textContent = text;
    statusBadge.className = "status-badge " + state;
}

function setStep(n, state) {
    for (var i = 0; i < stepPips.length; i++) {
        var pip = stepPips[i];
        var pipStep = parseInt(pip.getAttribute("data-step"));
        if (pipStep < n) pip.className = "step-pip done";
        else if (pipStep === n) pip.className = "step-pip " + state;
        else pip.className = "step-pip";
    }
}

function resetSteps() {
    for (var i = 0; i < stepPips.length; i++) stepPips[i].className = "step-pip";
}

var extRoot = "", pythonDir = "", tmpDir = "", wavPath = "", srtPath = "";
var pythonCmd = "python";

function initPaths() {
    try { extRoot = csInterface.getSystemPath(SystemPath.EXTENSION); } catch (e) { return false; }
    pythonDir = path.join(extRoot, "python");
    tmpDir    = os.tmpdir();
    wavPath   = path.join(tmpDir, "freekaps_audio.wav");
    srtPath   = path.join(tmpDir, "freekaps_captions.srt");
    
    pythonCmd  = os.platform() === "win32" ? "python" : "python3";
    return true;
}

function evalJSX(script) {
    return new Promise(function (resolve, reject) {
        csInterface.evalScript(script, function (result) {
            if (result === "EvalScript error." || result === "undefined") return reject(new Error("ExtendScript error"));
            try {
                var parsed = JSON.parse(result);
                if (parsed.error) reject(new Error(parsed.error));
                else resolve(parsed);
            } catch (e) { resolve(result); }
        });
    });
}

async function refreshTracks() {
    try {
        var tracks = await evalJSX("getAudioTrackList()");
        if (typeof tracks === "string") tracks = JSON.parse(tracks);
        while (trackSelect.options.length > 1) trackSelect.remove(1);
        tracks.forEach(function(t) {
            var opt = document.createElement("option");
            opt.value = t.index;
            opt.textContent = t.name;
            trackSelect.appendChild(opt);
        });
        log("רשימת הערוצים עודכנה.");
    } catch (e) { log("טעינת ערוצים נכשלה.", "warn"); }
}
btnRefresh.addEventListener("click", refreshTracks);

function runPython(inputWav, outputSrt, maxWords, doRtlFix) {
    return new Promise(function (resolve, reject) {
        var scriptPath = path.join(pythonDir, "transcriber.py");
        isCancelled = false;
        var workSuccess = false;
        
        var rtlArg = doRtlFix ? "True" : "False";
        
        try {
            currentProcess = spawn(pythonCmd, [scriptPath, inputWav, outputSrt, maxWords, rtlArg], {
                cwd: pythonDir,
                env: Object.assign({}, process.env, { PYTHONIOENCODING: "utf-8" }),
            });
        } catch (e) { return reject(new Error("הפעלת Python נכשלה")); }

        currentProcess.stdout.on("data", function (d) {
            var lines = d.toString().split("\n");
            lines.forEach(function(l) { 
                if(l.trim()) {
                    log(l.trim(), "py");
                    if (l.indexOf("SUCCESS") !== -1 || l.indexOf("Done.") !== -1) workSuccess = true;
                }
            });
        });
        currentProcess.stderr.on("data", function (d) {
            d.toString().split("\n").forEach(function(l) { if(l.trim()) log(l.trim(), "warn"); });
        });

        currentProcess.on("close", function (code) {
            currentProcess = null;
            if (isCancelled) reject(new Error("Cancelled"));
            else if (code === 0 || (workSuccess && fs.existsSync(outputSrt))) resolve();
            else reject(new Error("Python exited " + code));
        });
    });
}

btnCancel.addEventListener("click", function() {
    if (currentProcess) { isCancelled = true; currentProcess.kill(); }
});

btnCopyLog.addEventListener("click", function() {
    var text = logDiv.innerText;
    var textarea = document.createElement("textarea");
    textarea.value = text;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand("copy");
    document.body.removeChild(textarea);
    var old = btnCopyLog.textContent;
    btnCopyLog.textContent = "הועתק!";
    setTimeout(function(){ btnCopyLog.textContent = old; }, 2000);
});

function cleanup() {
    try { if (fs.existsSync(wavPath)) fs.unlinkSync(wavPath); } catch(e) {}
}

btnGenerate.addEventListener("click", async function () {
    btnGenerate.disabled = true;
    btnCancel.style.display = "block";
    logDiv.innerHTML = "";
    resetSteps();
    setStatus("מעבד...", "working");
    cleanup();

    try {
        var trackIdx = parseInt(trackSelect.value);
        var maxWords = wordsSlider.value;
        var doRtlFix = checkRtlFix.checked;
        
        // שלב 1: ייצוא
        setStep(1, "active");
        log("שלב 1/4 — מייצא סאונד מהסיקוונס...");
        await evalJSX('exportActiveSequenceAudio("' + wavPath.replace(/\\/g, "/") + '", ' + trackIdx + ')');
        
        var start = Date.now();
        while(!fs.existsSync(wavPath) || fs.statSync(wavPath).size === 0) {
            if (isCancelled) throw new Error("Cancelled");
            if (Date.now() - start > 20000) throw new Error("הייצוא נכשל (Timeout)");
            await new Promise(r => setTimeout(r, 500));
        }
        setStep(1, "done");

        // שלב 2: תמלול
        setStep(2, "active");
        log("שלב 2/4 — מתמלל בבינה מלאכותית...");
        await runPython(wavPath, srtPath, maxWords, doRtlFix);
        setStep(2, "done");

        // שלב 3: ייבוא
        setStep(3, "active");
        log("שלב 3/4 — מייבא כתוביות לפרויקט...");
        await evalJSX('importSRT("' + srtPath.replace(/\\/g, "/") + '")');
        setStep(3, "done");

        // שלב 4: מיקום
        if (checkAutoplace.checked) {
            setStep(4, "active");
            log("שלב 4/4 — ממקם על הטיימליין...");
            await evalJSX('placeSRTOnTimeline("' + srtPath.replace(/\\/g, "/") + '")');
            setStep(4, "done");
            log("הסתיים בהצלחה!", "ok");
            setStatus("מוכן", "done");
        } else {
            log("הסתיים! (ייבוא בלבד)", "ok");
            setStatus("מוכן", "ready");
        }

    } catch (err) {
        setStatus(err.message === "Cancelled" ? "מוכן" : "שגיאה", err.message === "Cancelled" ? "ready" : "error");
        log(err.message === "Cancelled" ? "נעצר." : "נכשל: " + err.message, "err");
    } finally {
        cleanup();
        btnGenerate.disabled = false;
        btnCancel.style.display = "none";
    }
});

function init() {
    if (!nodeAvailable || !csInterface || !initPaths()) return;
    refreshTracks();
    setStatus("מוכן", "ready");
}
init();
