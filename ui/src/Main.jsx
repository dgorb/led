import React, {useState, useEffect} from 'react';
import {ChromePicker, CirclePicker} from 'react-color';
import Favorites from './components/Favorites.jsx';
import ColorPicker from './components/ColorPicker.jsx';
import {InitColorAPI, SetColorAPI, TurnOffAPI, TurnOnAPI} from './scripts/api.js';
import {RGBtoHEX, RGBtoHSV} from './scripts/utils.js';

import ToggleOffOutlinedIcon from '@material-ui/icons/ToggleOffOutlined';
import ToggleOnOutlinedIcon from '@material-ui/icons/ToggleOnOutlined';

function Main() {
  const [color, setColor] = useState({rgb: [0, 0, 0], hsv: [0, 0, 0], hex: ""});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    InitColorAPI().then(response => {
      response.json().then(data => {
        setColorWithRGB([data.r, data.g, data.b]);
        setLoading(false);
      })
    })
  }, []);

  let handleChange = (clr, event) => {
    if (color.hex !== clr.hex) {
      SetColorAPI(clr.rgb[0], clr.rgb[1], clr.rgb[2])
    }
  }

  const setColorWithRGB = (rgb) => {
    setColor({
      rgb: rgb,
      hsv: RGBtoHSV(rgb),
      hex: RGBtoHEX(rgb),
    })
  }

  if (loading) {
    return <p>Loading...</p>
  } else {
    return (
      <div style={{
        height: '100vh',
        width: '100wv',
        }}>
          <OnOffButton color={color}/>
          <ColorPicker color={color} setColor={setColor} onChange={handleChange}/>
          <Favorites color={color} setColor={setColorWithRGB} />
      </div>
    );
  }
}

function OnOffButton(props) {
  const [on, setOn] = useState(true);

  const toggle = () => {
    if (on) {
      TurnOffAPI()
    } else {
      TurnOnAPI(props.color.rgb[0], props.color.rgb[1], props.color.rgb[2])
    }
    setOn(!on);
  }

  if (on) {
    return (
      <ToggleOnOutlinedIcon fontSize="large" onClick={toggle}/>
    )
  } else {
    return (
      <ToggleOffOutlinedIcon fontSize="large" onClick={toggle}/>
    )
  }
}

export default Main;
