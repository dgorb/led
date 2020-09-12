import React, {useState, useEffect} from 'react';
import {SketchPicker, ChromePicker} from 'react-color';

function Main() {
  const [color, setColor] = useState({});

  useEffect(() => {
    initColorAPI().then(response => {
      response.json().then(data => {
        setColor(data);
      })
    })
  }, []);

  let handleChange = (color, event) => {
    setColor(color.rgb);
    setColorAPI(color.rgb.r, color.rgb.g, color.rgb.b)
  };

  return (
    <div style={{
      height: '100vh',
      width: '100wv',
      background: `rgb(${color.r}, ${color.g}, ${color.b})`
      }}>
        <ChromePicker
            color={color}
            onChange={handleChange}
            disableAlpha={true}
        />
    </div>
  );
}

function APICall(method, endpoint) {
  const url = 'http://192.168.1.10:5000';
  return fetch(url + endpoint, {method: method})
}

function setColorAPI(r, g, b) {
  APICall("POST", `/set-color?color=${r},${g},${b}`)

}

function initColorAPI() {
  return APICall("GET", '/get-color');
}

export default Main;
