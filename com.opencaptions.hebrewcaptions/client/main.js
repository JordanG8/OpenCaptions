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

// Setup screen
var btnGenerate    = document.getElementById("btn-generate");
var btnRefresh     = document.getElementById("btn-refresh-tracks");
var trackSelect    = document.getElementById("track-select");
var wordsSlider    = document.getElementById("words-slider");
var wordsValue     = document.getElementById("words-value");
var checkAutoplace = document.getElementById("check-autoplace");
var checkRtlFix    = document.getElementById("check-rtl-fix");

// Progress screen
var btnCancel      = document.getElementById("btn-cancel");
var btnBack        = document.getElementById("btn-back");
var btnRetry       = document.getElementById("btn-retry");
var stepBarFill    = document.getElementById("step-bar-fill");
var stepPips       = document.querySelectorAll(".step-bar .step-pip");
var stepItems      = document.querySelectorAll(".step-bar .step-item");

// Step 2 elements
var step2Title     = document.getElementById("step2-title-text");
var step2Subtitle  = document.getElementById("step2-subtitle");
var step2Spinner   = document.getElementById("step2-spinner");
var txProgress     = document.getElementById("transcription-progress");
var txIndeterminate = document.getElementById("transcription-indeterminate");
var txFill         = document.getElementById("transcription-fill");
var txPct          = document.getElementById("transcription-pct");
var txTime         = document.getElementById("transcription-time");
var livePreview    = document.getElementById("live-preview");
var backendBadge   = document.getElementById("backend-badge");
var statDuration   = document.getElementById("stat-duration");
var statElapsed    = document.getElementById("stat-elapsed");

// Done / Error
var doneMessage    = document.getElementById("done-message");
var doneSub        = document.getElementById("done-sub");
var errorMessage   = document.getElementById("error-message");

// Log
var logDiv         = document.getElementById("log");
var logToggle      = document.getElementById("log-toggle");
var logArrow       = document.getElementById("log-arrow");
var btnCopyLog     = document.getElementById("btn-copy-log");

// Status
var statusBadge    = document.getElementById("status-badge");
var statusText     = document.getElementById("status-text");

// Screens
var screenSetup    = document.getElementById("screen-setup");
var screenProgress = document.getElementById("screen-progress");

var currentProcess = null;
var isCancelled = false;
var elapsedTimer = null;
var elapsedSeconds = 0;

// ── Helpers ──────────────────────────────────────────────────

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

function showScreen(name) {
    screenSetup.className    = "screen" + (name === "setup"    ? " active" : "");
    screenProgress.className = "screen" + (name === "progress" ? " active" : "");
}

// ── Step bar management ──────────────────────────────────────

// fillPercent maps step positions to how full the connecting line should be
// Step 1 active = 0%, Step 1 done = 16%, Step 2 active = 33%, Step 2 done = 50%, etc.
var fillMap = { "1a": "0%", "1d": "16%", "2a": "33%", "2d": "50%", "3a": "66%", "3d": "83%", "4a": "90%", "4d": "100%", "done": "100%" };

function setStep(n, state) {
    // Update pips
    for (var i = 0; i < stepPips.length; i++) {
        var pip = stepPips[i];
        var item = stepItems[i];
        var s = parseInt(pip.getAttribute("data-step"));
        if (s < n) {
            pip.className = "step-pip done";
            item.className = "step-item done";
        } else if (s === n) {
            pip.className = "step-pip " + state;
            item.className = "step-item " + state;
        } else {
            pip.className = "step-pip";
            item.className = "step-item";
        }
    }

    // Update fill bar
    var key = state === "done" ? "done" : (n + (state === "active" ? "a" : "d"));
    if (fillMap[key]) stepBarFill.style.width = fillMap[key];

    // Show corresponding panel
    showPanel(state === "done" && n === 4 ? "done" : String(n));
}

function showPanel(id) {
    var panels = document.querySelectorAll(".step-panel");
    for (var i = 0; i < panels.length; i++) {
        panels[i].className = "step-panel" + (panels[i].getAttribute("data-panel") === id ? " active" : "");
    }
}

function resetSteps() {
    for (var i = 0; i < stepPips.length; i++) {
        stepPips[i].className = "step-pip";
        stepItems[i].className = "step-item";
    }
    stepBarFill.style.width = "0%";
}

function resetStep2() {
    step2Title.textContent = "טוען מודל AI";
    step2Subtitle.textContent = "מאתחל את מנוע התמלול...";
    step2Spinner.style.display = "";
    txProgress.style.display = "none";
    txIndeterminate.style.display = "";
    txFill.style.width = "0%";
    txPct.textContent = "0%";
    txTime.textContent = "";
    livePreview.innerHTML = '<span class="cursor"></span>';
    backendBadge.style.display = "none";
    statDuration.textContent = "—";
    statElapsed.textContent = "0:00";
}

// ── Elapsed timer ────────────────────────────────────────────

function startElapsedTimer() {
    elapsedSeconds = 0;
    statElapsed.textContent = "0:00";
    elapsedTimer = setInterval(function() {
        elapsedSeconds++;
        var m = Math.floor(elapsedSeconds / 60);
        var s = elapsedSeconds % 60;
        statElapsed.textContent = m + ":" + (s < 10 ? "0" : "") + s;
    }, 1000);
}

function stopElapsedTimer() {
    if (elapsedTimer) { clearInterval(elapsedTimer); elapsedTimer = null; }
}

// ── Paths ────────────────────────────────────────────────────

var extRoot = "", pythonDir = "", tmpDir = "", wavPath = "", srtPath = "";
var pythonCmd = "python";

function initPaths() {
    try { extRoot = csInterface.getSystemPath(SystemPath.EXTENSION); } catch (e) { return false; }
    pythonDir = path.join(extRoot, "python");
    tmpDir    = os.tmpdir();
    wavPath   = path.join(tmpDir, "opencaptions_audio.wav");
    // SRT lives in a persistent folder so Premiere keeps a valid reference between sessions
    var srtDir = path.join(process.env.APPDATA || os.tmpdir(), "OpenCaptions");
    try { if (!fs.existsSync(srtDir)) fs.mkdirSync(srtDir, { recursive: true }); } catch(e) {}
    srtPath   = path.join(srtDir, "opencaptions_captions.srt");

    var vendorPython = path.join(extRoot, "vendor", "python", "python.exe");
    var vendorFFmpeg = path.join(extRoot, "vendor", "ffmpeg");

    if (os.platform() === "win32" && fs.existsSync(vendorPython)) {
        pythonCmd = vendorPython;
        process.env.PATH = vendorFFmpeg + ";" + process.env.PATH;
    } else {
        pythonCmd = os.platform() === "win32" ? "python" : "python3";
    }
    return true;
}

// ── ExtendScript bridge ──────────────────────────────────────

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

// ── Track refresh ────────────────────────────────────────────

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

// ── Python runner with structured progress parsing ───────────

var audioDuration = 0;

function runPython(inputWav, outputSrt, maxWords, doRtlFix) {
    return new Promise(function (resolve, reject) {
        var scriptPath = path.join(pythonDir, "transcriber.py");
        isCancelled = false;
        var workSuccess = false;
        audioDuration = 0;

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
                l = l.trim();
                if (!l) return;

                // Parse structured progress messages
                if (l.indexOf("@@") === 0) {
                    handleProgressMessage(l);
                    if (l.indexOf("@@DONE") === 0) workSuccess = true;
                } else {
                    log(l, "py");
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

function handleProgressMessage(msg) {
    if (msg.indexOf("@@DURATION:") === 0) {
        audioDuration = parseFloat(msg.substring(11));
        statDuration.textContent = formatDuration(audioDuration);
        // Switch from indeterminate to real progress bar
        txIndeterminate.style.display = "none";
        txProgress.style.display = "";
        step2Title.textContent = "מתמלל...";
        step2Subtitle.textContent = "מזהה מילים מתוך השמע...";
        log("משך השמע: " + formatDuration(audioDuration), "py");
    }
    else if (msg.indexOf("@@BACKEND:") === 0) {
        var backend = msg.substring(10);
        backendBadge.style.display = "";
        backendBadge.textContent = backend;
        // Color-code the badge
        var lower = backend.toLowerCase();
        if (lower.indexOf("cuda") !== -1) backendBadge.className = "backend-badge cuda";
        else if (lower.indexOf("directml") !== -1) backendBadge.className = "backend-badge directml";
        else backendBadge.className = "backend-badge cpu";
        log("Backend: " + backend, "py");
    }
    else if (msg.indexOf("@@MODEL_LOADING") === 0) {
        step2Title.textContent = "טוען מודל AI";
        step2Subtitle.textContent = "טוען את מודל ivrit-ai (עברית) לזיכרון...";
        log("טוען מודל...", "py");
    }
    else if (msg.indexOf("@@MODEL_READY") === 0) {
        step2Title.textContent = "מתמלל...";
        step2Subtitle.textContent = "המודל מוכן, מתחיל תמלול...";
        log("המודל נטען, מתחיל תמלול.", "py");
    }
    else if (msg.indexOf("@@SEG:") === 0) {
        // @@SEG:<end_seconds>|<text>
        var rest = msg.substring(6);
        var pipeIdx = rest.indexOf("|");
        if (pipeIdx !== -1) {
            var endSec = parseFloat(rest.substring(0, pipeIdx));
            var text = rest.substring(pipeIdx + 1);

            // Update progress bar
            if (audioDuration > 0) {
                var pct = Math.min(100, Math.round((endSec / audioDuration) * 100));
                txFill.style.width = pct + "%";
                txPct.textContent = pct + "%";
                txTime.textContent = formatDuration(endSec) + " / " + formatDuration(audioDuration);
            }

            // Update live preview (show last transcribed text)
            livePreview.innerHTML = escapeHtml(text) + ' <span class="cursor"></span>';
        }
    }
    else if (msg.indexOf("@@BACKEND_FALLBACK:") === 0) {
        var reason = msg.substring(19);
        log("אזהרה: המעבד הגרפי נכשל (" + reason + ") — עובר למצב CPU", "warn");
        var confirmed = confirm(
            "המעבד הגרפי (GPU) לא זמין:\n" + reason +
            "\n\nהתמלול ימשיך במצב CPU — יהיה איטי יותר (5-10 דקות לדקת שמע)." +
            "\n\nהאם להמשיך?"
        );
        if (!confirmed) {
            if (currentProcess) { isCancelled = true; currentProcess.kill(); }
        }
    }
    else if (msg.indexOf("@@WRITING_SRT") === 0) {
        step2Title.textContent = "כותב קובץ כתוביות";
        step2Subtitle.textContent = "שומר את התמלול לקובץ SRT...";
        step2Spinner.style.display = "";
        txFill.style.width = "100%";
        txPct.textContent = "100%";
        log("כותב SRT...", "py");
    }
}

function formatDuration(sec) {
    var m = Math.floor(sec / 60);
    var s = Math.floor(sec % 60);
    return m + ":" + (s < 10 ? "0" : "") + s;
}

function escapeHtml(text) {
    var div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

// ── Cancel ───────────────────────────────────────────────────

btnCancel.addEventListener("click", function() {
    if (currentProcess) { isCancelled = true; currentProcess.kill(); }
});

// ── Log toggle ───────────────────────────────────────────────

logToggle.addEventListener("click", function() {
    var isOpen = logDiv.classList.contains("open");
    logDiv.className = isOpen ? "" : "open";
    logDiv.id = "log";
    logArrow.className = "arrow" + (isOpen ? "" : " open");
    btnCopyLog.style.display = isOpen ? "none" : "";
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

// ── Back / Retry buttons ─────────────────────────────────────

btnBack.addEventListener("click", function() {
    showScreen("setup");
    setStatus("מוכן", "ready");
});

btnRetry.addEventListener("click", function() {
    showScreen("setup");
    setStatus("מוכן", "ready");
});

// ── Cleanup ──────────────────────────────────────────────────

function cleanup() {
    // Only delete the WAV — SRT stays on disk so Premiere keeps a valid reference
    try { if (fs.existsSync(wavPath)) fs.unlinkSync(wavPath); } catch(e) {}
}

// ── Main generate flow ───────────────────────────────────────

btnGenerate.addEventListener("click", async function () {
    // Transition to progress screen
    showScreen("progress");
    logDiv.innerHTML = "";
    resetSteps();
    resetStep2();
    setStatus("מעבד...", "working");
    btnCancel.style.display = "block";
    cleanup();

    try {
        var trackIdx = parseInt(trackSelect.value);
        var maxWords = wordsSlider.value;
        var doRtlFix = checkRtlFix.checked;

        // Step 1: Export audio
        setStep(1, "active");
        log("שלב 1/4 — מייצא שמע מהסיקוונס...");
        await evalJSX('exportActiveSequenceAudio("' + wavPath.replace(/\\/g, "/") + '", ' + trackIdx + ')');

        // Wait for WAV to appear, be non-empty, AND stop growing (export fully flushed)
        var start = Date.now();
        var lastSize = -1;
        var stableCount = 0;
        while (true) {
            if (isCancelled) throw new Error("Cancelled");
            if (Date.now() - start > 60000) throw new Error("הייצוא נכשל (Timeout)");
            await new Promise(function(r) { setTimeout(r, 500); });
            if (!fs.existsSync(wavPath)) { lastSize = -1; stableCount = 0; continue; }
            var sz = fs.statSync(wavPath).size;
            if (sz === 0) { lastSize = -1; stableCount = 0; continue; }
            if (sz === lastSize) {
                stableCount++;
                if (stableCount >= 3) break; // size unchanged for 1.5s — export complete
            } else {
                lastSize = sz;
                stableCount = 0;
            }
        }
        setStep(1, "done");

        // Step 2: Transcription
        setStep(2, "active");
        startElapsedTimer();
        log("שלב 2/4 — מתמלל בבינה מלאכותית...");
        await runPython(wavPath, srtPath, maxWords, doRtlFix);
        stopElapsedTimer();
        setStep(2, "done");

        // Step 3: Import SRT (remove stale project reference first)
        setStep(3, "active");
        log("שלב 3/4 — מייבא כתוביות לפרויקט...");
        await evalJSX('removeExistingSRT("' + srtPath.replace(/\\/g, "/") + '")').catch(function(){});
        await evalJSX('importSRT("' + srtPath.replace(/\\/g, "/") + '")');
        setStep(3, "done");

        // Step 4: Place on timeline
        if (checkAutoplace.checked) {
            setStep(4, "active");
            log("שלב 4/4 — ממקם על הטיימליין...");
            await evalJSX('placeSRTOnTimeline("' + srtPath.replace(/\\/g, "/") + '")');
            setStep(4, "done");
        }

        // Show done panel
        btnCancel.style.display = "none";
        showPanel("done");
        stepBarFill.style.width = "100%";
        // Mark all steps done
        for (var i = 0; i < stepPips.length; i++) {
            stepPips[i].className = "step-pip done";
            stepItems[i].className = "step-item done";
        }

        var elapsed = formatDuration(elapsedSeconds);
        if (checkAutoplace.checked) {
            doneMessage.textContent = "הכתוביות נוצרו בהצלחה!";
            doneSub.textContent = "הושלם ב-" + elapsed;
        } else {
            doneMessage.textContent = "הכתוביות יובאו לפרויקט!";
            doneSub.textContent = "ייבוא בלבד (ללא מיקום) — " + elapsed;
        }
        log("הסתיים בהצלחה!", "ok");
        setStatus("מוכן", "done");

    } catch (err) {
        stopElapsedTimer();
        btnCancel.style.display = "none";

        if (err.message === "Cancelled") {
            showScreen("setup");
            setStatus("מוכן", "ready");
            log("נעצר.", "err");
        } else {
            showPanel("error");
            errorMessage.textContent = err.message;
            setStatus("שגיאה", "error");
            log("נכשל: " + err.message, "err");
        }
    } finally {
        cleanup();
    }
});

// ── Init ─────────────────────────────────────────────────────

function init() {
    if (!nodeAvailable || !csInterface || !initPaths()) return;
    refreshTracks();
    setStatus("מוכן", "ready");
}
init();
