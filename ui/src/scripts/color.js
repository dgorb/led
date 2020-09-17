export function HSVtoRGB(h, s, v) {
    // h: Hue, s: Saturation, v: Value/Brightness
    // https://en.wikipedia.org/wiki/HSL_and_HSV#HSV_to_RGB

    // Achromatic
    if (s == 0) {
       return [v*255, v*255, v*255]
    }

    const c = v * s; // Chroma
    const hh = h / 60;
    const x = c * (1 - Math.abs(hh % 2 - 1))

    let tmp = [];

    if (hh <= 1) {
        tmp = [c, x, 0];
    } else if (hh <= 2) {
        tmp = [x, c, 0];
    } else if (hh <= 3) {
        tmp = [0, c, x];
    } else if (hh <= 4) {
        tmp = [0, x, c];
    } else if (hh <= 5) {
        tmp = [x, 0, c];
    } else {
        tmp = [c, 0, x];
    }

    let componentVal = (x) => {
        return Math.round((x + v - c) * 255);
    }

    return [componentVal(tmp[0]), componentVal(tmp[1]), componentVal(tmp[2])];
}

export function RGBtoHEX(rgb) {
    const componentToHex = (c) => {
        var hex = c.toString(16);
        return hex.length == 1 ? "0" + hex : hex;
    }

    return "#" + componentToHex(rgb[0]) + componentToHex(rgb[1]) + componentToHex(rgb[2])
}

export function RGBtoHSV(rgb) {
    let r = rgb[0] / 255;
    let g = rgb[1] / 255;
    let b = rgb[2] / 255;

    let cMax = Math.max(r, Math.max(g, b));
    let cMin = Math.min(r, Math.min(g, b));
    let diff = cMax - cMin;
    let h = -1;
    let s = -1;

    if (cMax == cMin) {
        h = 0;
    } else if (cMax == r) {
        h = (60 * ((g - b) / diff) + 360) % 360;
    } else if (cMax == g) {
        h = (60 * ((b - r) / diff) + 120) % 360;
    } else if (cMax == b) {
        h = (60 * ((r - g) / diff) + 240) % 360;
    }

    if (cMax == 0) {
        s = 0;
    } else {
        s = (diff / cMax) * 100;
    }

    let v = cMax * 100;

    return [h, s, v]
}
