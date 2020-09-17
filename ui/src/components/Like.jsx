import React, {useState, useEffect} from 'react';
import {CirclePicker} from 'react-color';
import Heart from "react-animated-heart";
import Typography from '@material-ui/core/Typography';
import {FavoritesAPI, LikeAPI, SetColorAPI} from '../scripts/api.js';

export default function Like(props) {
  const [isClick, setClick] = useState(false);
  const [favorites, setFavorites] = useState();

  useEffect(() => {
    FavoritesAPI().then(response => {
      response.json().then(data => {
        setFavorites(data);
      })
    })
  }, []);

  useEffect(() => {
    if (isClick) {
      setClick(false);
    }
  }, [props.color]);

  useEffect(() => {
    FavoritesAPI().then(response => {
      response.json().then(data => {
        setFavorites(data);
      })
    })
  }, [isClick]);

  let handleChange = (color, event) => {
    props.setColor({ rgb: [color.rgb.r, color.rgb.g, color.rgb.b]});
    SetColorAPI(color.rgb.r, color.rgb.g, color.rgb.b)
  };

  return (
    <>
    <div style={{backgroundColor: 'white', width: window.innerWidth}}>
      <Typography>Favorites</Typography>
      <Heart isClick={isClick} onClick={() => {
          LikeAPI(props.color.replace('#', ''));
          setClick(!isClick)
      }} />
      <CirclePicker
        onChange={handleChange}
        colors={favorites}
      />
    </div>
    </>
  );
}
