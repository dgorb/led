import React, {useState, useEffect} from 'react';
import {ChromePicker, CirclePicker} from 'react-color';
import Favorites from './components/Favorites.jsx';
import ColorPicker from './components/ColorPicker.jsx';
import {InitColorAPI, SetColorAPI, TurnOffAPI, TurnOnAPI} from './scripts/api.js';
import ToggleOffOutlinedIcon from '@material-ui/icons/ToggleOffOutlined';
import ToggleOnOutlinedIcon from '@material-ui/icons/ToggleOnOutlined';

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
        }}>
          <OnOffButton color={color.rgb}/>
          <ColorPicker initRGB={[color.rgb[0], color.rgb[1], color.rgb[2]]} setColor={setColor} onChange={handleChange}/>
          <Favorites color={color.hex} setColor={setColor} />
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
      TurnOnAPI(props.color[0], props.color[1], props.color[2])
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
