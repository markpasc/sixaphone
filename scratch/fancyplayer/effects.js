
var plasmaElem;
var plasmaPixelSize = 4;
var visElem;
var counter = 0;
var visWidth = 1;
var visHeight = 1;
var visScale = 1;

var waveformData = { left: [], right: [] };

// Plasma thing based on demo at http://dave-webster.com/projects/index.php?page=incs/plasma_demo1

function dist(a, b, c, d) {
	return Math.sqrt((a - c) * (a - c) + (b - d) * (b - d));
}

function makeFakeWaveform() {

    for (var i = 0; i < 256; i++) {
        waveformData.left[i] = Math.sin(i + counter);
        waveformData.right[i] = Math.sin(i + counter);
    }

}

function renderEffects() {
	counter++;

    renderPlasma();
    if (currentSound && currentSound.waveformData) {
        waveformData = currentSound.waveformData;
    }
    else {
        makeFakeWaveform();
    }
    renderVisualization();
}

function renderPlasma() {
    var ctx = plasmaElem.getContext('2d');
    ctx.save();
 
    var time = counter * 5;

    for( y = 0; y < 128; y += plasmaPixelSize) {
        for( x = 0 ; x < 128; x += plasmaPixelSize) {

            var temp_val = (
                Math.floor(
                    Math.sin(dist(x + time, y, 128.0, 128.0) / 8.0) +
                    Math.sin(dist(x, y, 64.0, 64.0) / 8.0) + 
                    Math.sin(dist(x, y + time / 7, 192.0, 64) / 7.0) +
                    Math.sin(dist(x, y, 192.0, 100.0) / 8.0)
                )
            );
 
            var temp_col = Math.floor((2 + temp_val) * 50);
 
            var rand_red = 0;
            var rand_green = 0; //(temp_col / 2);
            var rand_blue = (128 - temp_col) / 2;
 
            ctx.fillStyle = "rgb("+rand_red+","+rand_green+","+rand_blue+")";
 
            ctx.fillRect(x,y,plasmaPixelSize,plasmaPixelSize);

		}
	}
 
	ctx.restore();
 
}

function renderVisualization() {
    var ctx = visElem.getContext('2d');
    ctx.save();

    // Fade out previous frame
    var pixelData = ctx.getImageData(0, 0, visWidth, visHeight);
    var dataLength = pixelData.data.length;
    for (var i = 3; i < dataLength; i += 4) {
        var current = pixelData.data[i];
        var n = current - 50;
        if (n < 0) n = 0;
        pixelData.data[i] = n;
    }
    ctx.putImageData(pixelData, 0, 0);

    // Draw next frame
    ctx.fillStyle = "rgba(255, 255, 0, 128)";
    ctx.fillRect(counter % visWidth, (visHeight / 2) - (Math.cos(counter / 10) * 10), 7, 6);

    renderWaveform(ctx);

    ctx.restore();
}

function renderWaveform(ctx) {
    
    var left = waveformData.left;
    var right = waveformData.right;

    var centerX = visWidth / 2.0;
    var centerY = visHeight / 2.0;

    ctx.beginPath();
    ctx.moveTo(centerX, centerY);

    for (var i = 0; i < 256; i++) {
        var leftValue = left[255 - i];
        var x = (i / 256.0) * visScale;
        var ly = leftValue * (visHeight / 4.0);
        ctx.lineTo(centerX - x, centerY - ly);
    }

    ctx.lineTo(0, centerY);

    ctx.moveTo(centerX, centerY);

    for (var i = 0; i < 256; i++) {
        var rightValue = right[i];
        var x = (i / 256.0) * visScale;
        var ry = rightValue * (visHeight / 4.0);
        ctx.lineTo(centerX + x, centerY - ry);
    }

    ctx.lineTo(visWidth - 1, centerY);

    ctx.fillStyle = "rgba(0, 255, 0, 128)";
    ctx.fill();

}

$(document).ready(function () {
    plasmaElem = document.createElement("canvas");
    var jqp = $(plasmaElem);
    jqp.attr("width", "128");
    jqp.attr("height", "128");
    jqp.css('position', 'fixed');
    jqp.css('top', '0');
    jqp.css('left', '0');
    //jqp.css('bottom', '0');
    //jqp.css('right', '0');
    jqp.css('width', '100%');
    jqp.css('height', '100%');
    jqp.css('z-index', '0');

    $(document.body).append(jqp);

    visElem = document.createElement("canvas");
    var jqv = $(visElem);
    visWidth = $(document).width() / 8;
    visHeight = $(document).height() / 8;
    jqv.attr("width", visWidth);
    jqv.attr("height", visHeight);
    jqv.css('position', 'fixed');
    jqv.css('top', '0');
    jqv.css('left', '0');
    jqv.css('z-index', '10');
    jqv.css('width', '100%');
    jqv.css('height', '100%');

    $(document.body).append(jqv);

    // Whichever is largest of our width and height becomes the visualization scale
    if (visWidth > visHeight) {
        visScale = visWidth;
    }
    else {
        visScale = visHeight;
    }

    setInterval(renderEffects, 10);
});


