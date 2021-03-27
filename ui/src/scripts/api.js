function APICall(method, endpoint) {
  const url = 'http://192.168.1.10:5000';
  return fetch(url + endpoint, {method: method})
}

export function SetColorAPI(r, g, b) {
  APICall("POST", `/set-color?color=${r},${g},${b}`)
}

export function InitColorAPI() {
  return APICall("GET", '/get-color');
}

export function LikeAPI(hex) {
  APICall("POST", `/favorite?color=${hex}`)
}

export function FavoritesAPI() {
  return APICall("GET", '/favorites')
}

export function TurnOnAPI(r, g, b) {
  return APICall("POST", `/turn-on?color=${r},${g},${b}`)
}

export function TurnOffAPI() {
  return APICall("POST", '/turn-off')
}

export function ShiftAPI(color1, color2, period) {
  let rgb1 = `${color1.rgb[0]},${color1.rgb[1]},${color1.rgb[2]}`;
  let rgb2 = `${color2.rgb[0]},${color2.rgb[1]},${color2.rgb[2]}`;
  return APICall("POST", `/shift?start=${rgb1}&end=${rgb2}&period=${period}&cont=true`)
}
