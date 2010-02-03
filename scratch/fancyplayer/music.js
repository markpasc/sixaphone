
soundManager.url = 'sm/';
soundManager.flashVersion = 9;
soundManager.flash9Options = {
    useWaveformData: true
};
soundManager.useFastPolling = true;
soundManager.useHighPerformance = true;

var currentSound = null;

var sounds = [];
var smLoaded = false;

soundManager.onload = function() {
    smLoaded = true;
};

function startSounds() {
    console.log("Starting sounds ", sounds);
    currentSound = soundManager.createSound('sound0',sounds[0]);
    soundManager.play('sound0');
}

$(document).ready(function () {

    var listElem = $('#sounds');
    var linkElems = listElem.find('a');

    for (var i = 0; i < linkElems.length; i++) {
        var linkElem = linkElems[i];
        var url = linkElem.href;
        //var url = linkElem;
        console.log("have url ", url);
        sounds.push(url);
    }

    if (smLoaded) {
        startSounds();
    }
    else {
        soundManager.onload = function() {
            smLoaded = true;
            startSounds();
        };
    }

});


