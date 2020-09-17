export function hue(r, x, y) {
    // Hue is angle on the color wheel
    let angle = Math.atan2(y-r, x-r);
    if (angle < 0) {
        angle += 2 * Math.PI;
    }

    const h = angle * 180 / Math.PI;
    return Math.round(h * 100) / 100;
}

export function saturation(d, r) {
    // Saturation is distance from color wheel origin
    // in (1, 0) range
    const sat = d / r;
    return Math.round(sat * 100) / 100;
}

export function distance(r, x, y) {
    return Math.sqrt(Math.pow(x-r, 2)+Math.pow(y-r, 2))
}

export function coordsToHSV(x, y, r, b=1) {
    let h = hue(r, x, y);
    let d = distance(r, x, y);
    let s = saturation(d, r);

    return [h, s, b]
}
