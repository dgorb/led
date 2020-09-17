import React, {useState, useEffect} from 'react';
import {ChromePicker, CirclePicker} from 'react-color';
import Like from './components/Like.jsx';
import ColorPicker from './components/ColorPicker.jsx';
import {InitColorAPI, SetColorAPI} from './scripts/api.js';

function Main() {
  const [color, setColor] = useState({rgb: [0, 0, 0]});

  /*useEffect(() => {
    initColorAPI().then(response => {
      response.json().then(data => {
        setColor(data);
      })
    })
  }, []);*/

  let handleChange = (clr, event) => {
    setColor(clr);
    SetColorAPI(clr.rgb[0], clr.rgb[1], clr.rgb[2])
  }

  return (
    <div style={{
      height: '100vh',
      width: '100wv',
      background: `rgb(${color.rgb[0]}, ${color.rgb[1]}, ${color.rgb[2]})`
      }}>
        <ColorPicker setColor={setColor} onChange={handleChange}/>
        <Like color={color.hex} setColor={setColor} />
    </div>
  );
}

export default Main;
