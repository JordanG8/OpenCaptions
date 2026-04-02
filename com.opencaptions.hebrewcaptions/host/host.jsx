/* ============================================================
   host.jsx  –  ExtendScript for Premiere Pro
   ============================================================ */

function probeSequence() {
    var seq = app.project.activeSequence;
    if (!seq) return '{"error": "No active sequence."}';
    var info = [];
    if (seq.captionTracks) info.push("Has captionTracks (" + seq.captionTracks.numTracks + ")");
    else info.push("No captionTracks");
    var keys = [];
    for (var key in seq) {
        if (key.indexOf("aption") !== -1 || key.indexOf("create") !== -1) keys.push(key);
    }
    return '{"keys": "' + info.join(' | ') + ' | Methods: ' + keys.join(', ') + '"}';
}

function getAudioTrackList() {
    var proj = app.project;
    if (!proj) return '{"error": "No project open."}';
    var seq = proj.activeSequence;
    if (!seq) return '{"error": "No active sequence."}';
    var tracks = [];
    for (var i = 0; i < seq.audioTracks.numTracks; i++) {
        var track = seq.audioTracks[i];
        tracks.push({ index: i, name: track.name || ("Audio " + (i + 1)) });
    }
    var jsonParts = [];
    for (var j = 0; j < tracks.length; j++) {
        jsonParts.push('{"index":' + tracks[j].index + ',"name":"' + tracks[j].name + '"}');
    }
    return '[' + jsonParts.join(',') + ']';
}

function exportActiveSequenceAudio(outputPath, trackIndex) {
    var proj = app.project;
    var seq = proj.activeSequence;
    try {
        var wavPresetPath = findWavPreset();
        var originalMuteStates = [];
        if (typeof trackIndex !== "undefined" && trackIndex !== -1) {
            for (var i = 0; i < seq.audioTracks.numTracks; i++) {
                originalMuteStates[i] = seq.audioTracks[i].isMuted() ? 1 : 0;
                seq.audioTracks[i].setMute(i == trackIndex ? 0 : 1);
            }
        }
        var outF = new File(outputPath);
        if (outF.exists) outF.remove();
        seq.exportAsMediaDirect(outF.fsName, wavPresetPath, 0);
        $.sleep(1000);
        if (typeof trackIndex !== "undefined" && trackIndex !== -1) {
            for (var k = 0; k < seq.audioTracks.numTracks; k++) {
                seq.audioTracks[k].setMute(originalMuteStates[k]);
            }
        }
        return outF.exists ? '{"ok": "Done"}' : '{"error": "Export failed"}';
    } catch (e) { return '{"error": "' + e.message + '"}'; }
}

function findWavPreset() {
    var app_path = Folder.appPackage ? Folder.appPackage.fsName : "C:/Program Files/Adobe/Adobe Premiere Pro 2026";
    var systemPresetsPath = app_path + "/MediaIO/systempresets";
    var systemPresetsFolder = new Folder(systemPresetsPath);
    var folders = systemPresetsFolder.getFiles();
    for (var i = 0; i < folders.length; i++) {
        if (folders[i] instanceof Folder && folders[i].name.indexOf("57415645") !== -1) {
            var presets = folders[i].getFiles("*.epr");
            if (presets && presets.length > 0) return presets[0].fsName;
        }
    }
    return null;
}

function removeExistingSRT(srtPath) {
    try {
        var fileName = srtPath.replace(/^.*[\\\/]/, "").toLowerCase();
        removeItemsFromBin(app.project.rootItem, fileName);
        return '{"ok": "Cleaned"}';
    } catch(e) { return '{"ok": "Nothing to clean"}'; }
}

function removeItemsFromBin(parent, fileName) {
    for (var i = parent.children.numItems - 1; i >= 0; i--) {
        var child = parent.children[i];
        if (child.type === ProjectItemType.BIN) {
            removeItemsFromBin(child, fileName);
        } else if (child.name.toLowerCase() === fileName) {
            try { child.remove(false, false); } catch(e) {}
        }
    }
}

function importSRT(srtPath) {
    try {
        var importOK = app.project.importFiles([srtPath], true, app.project.rootItem, false);
        return importOK ? '{"ok": "Imported"}' : '{"error": "Import Failed"}';
    } catch (e) { return '{"error": "' + e.message + '"}'; }
}

/**
 * Brute-force placement variations for Premiere 2026
 */
function placeSRTOnTimeline(srtPath) {
    var proj = app.project;
    var seq = proj.activeSequence;
    if (!seq) return '{"error": "No active sequence."}';

    var srtItem = findProjectItemByPath(srtPath, proj.rootItem);
    if (!srtItem) return '{"error": "SRT item not found in bin"}';
    
    var startTime = new Time();
    startTime.seconds = 0;

    // Trial 1: (ProjectItem, TimeObject, String)
    try {
        if (seq.createCaptionTrack(srtItem, startTime, "Subtitles")) return '{"ok": "Trial 1 Success"}';
    } catch(e) {}

    // Trial 2: (ProjectItem, TicksString, String)
    try {
        if (seq.createCaptionTrack(srtItem, startTime.ticks, "Subtitles")) return '{"ok": "Trial 2 Success"}';
    } catch(e) {}

    // Trial 3: (ProjectItem, TimeObject) - Some versions skip format
    try {
        if (seq.createCaptionTrack(srtItem, startTime)) return '{"ok": "Trial 3 Success"}';
    } catch(e) {}

    // Trial 4: (ProjectItem, TicksString)
    try {
        if (seq.createCaptionTrack(srtItem, startTime.ticks)) return '{"ok": "Trial 4 Success"}';
    } catch(e) {}

    // Trial 5: (ProjectItem, NumberOfTicks) - Passing as actual number
    try {
        var tickNum = Number(startTime.ticks);
        if (seq.createCaptionTrack(srtItem, tickNum)) return '{"ok": "Trial 5 Success"}';
    } catch(e) {}

    // Trial 6: The "Drop" method - Using projectItem.attachToSequence
    try {
        srtItem.attachToSequence(seq, startTime);
        return '{"ok": "Trial 6 (Attach) Success"}';
    } catch(e) {}

    // Trial 7: Last resort overwrite on V1
    try {
        seq.videoTracks[0].overwriteClip(srtItem, startTime);
        return '{"ok": "Placed via V1 Overwrite"}';
    } catch(e) {}

    return '{"error": "All 7 placement strategies failed."}';
}

function findProjectItemByPath(filePath, parentItem) {
    var fullPath = filePath.replace(/\\\\/g, "/").toLowerCase();
    var fileName = filePath.replace(/^.*[\\\/]/, "").toLowerCase();
    for (var i = 0; i < parentItem.children.numItems; i++) {
        var child = parentItem.children[i];
        if (child.type === ProjectItemType.BIN) {
            var found = findProjectItemByPath(filePath, child);
            if (found) return found;
        }
        if (child.getMediaPath && child.getMediaPath().replace(/\\\\/g, "/").toLowerCase() === fullPath) return child;
        if (child.name.toLowerCase() === fileName) return child;
    }
    return null;
}
