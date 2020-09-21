import React, {useState, useEffect} from 'react';
import {ChromePicker, CirclePicker} from 'react-color';
import Like from './components/Like.jsx';
import ColorPicker from './components/ColorPicker.jsx';
import {InitColorAPI, SetColorAPI} from './scripts/api.js';

function Main() {
  const [color, setColor] = useState({rgb: [0, 0, 0]});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    InitColorAPI().then(response => {
      response.json().then(data => {
        setColor({
          rgb: [
            data.r,
            data.g,
            data.b,
          ]
        });
        setLoading(false);
      })
    })
  }, []);

  let handleChange = (clr, event) => {
    setColor(clr);
    SetColorAPI(clr.rgb[0], clr.rgb[1], clr.rgb[2])
  }

  if (loading) {
    return <p>Loading...</p>
  } else {
    return (
      <div style={{
        height: '100vh',
        width: '100wv',
        background: `rgb(${color.rgb[0]}, ${color.rgb[1]}, ${color.rgb[2]})`
        }}>
          <ColorPicker initRGB={[color.rgb[0], color.rgb[1], color.rgb[2]]} setColor={setColor} onChange={handleChange}/>
          <Like color={color.hex} setColor={setColor} />
      </div>
    );
  }
}

export default Main;
